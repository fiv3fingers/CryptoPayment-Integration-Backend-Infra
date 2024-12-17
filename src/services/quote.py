# services/quote.py
from typing import List, Dict
from uuid import UUID

from pydantic import UUID4

from datetime import datetime
import pytz
from fastapi import HTTPException
from sqlalchemy.orm import Session

from models.schemas.changenow import TransactionType, FlowType, ExchangeEstimate
from models.schemas.quote import QuoteRequest, QuoteResponse, Currency, CurrencyQuote
from models.database_models import Order, User, OrderStatus

from services.changenow import ChangeNowClient, EstimateRequest
from services.base import BaseService

from utils.logging import get_logger
logger = get_logger("changenow")


class QuoteService(BaseService):
    def __init__(self, db: Session, changenow_client: ChangeNowClient):
        super().__init__(db)
        self.changenow_client = changenow_client



    async def _currency_to_usd(
        self,
        currency: Currency,
        amount: float
    ) -> float:
        # FIXME: Implement this method. Currently hardcoded for USDC
        """ Convert an amount of a given currency to USD."""
        if currency.token.lower() == "usdc":
            return amount

        if currency.chain.lower() == "eth":
            if currency.token.lower() == "eth":
                return amount * 4027
            if currency.token.lower() == "pepe":
                return amount * 0.000024
        if currency.chain.lower() == "sol":
            if currency.token.lower() == "sol":
                return amount * 219.75
        else:
            raise Exception("Unsupported currency")
            


    async def _usd_to_currency(
            self,
            currency: Currency,
            usd_value: float
    ) -> float:
        # FIXME: Implement this method. Currently hardcoded
        """ Convert a USD value to an amount of a given currency."""

        amount = usd_value / await self._currency_to_usd(currency, 1)

        return amount


    async def _get_estimate(
        self,
        from_currency: Currency,
        to_currency: Currency,
        target_amount: float
    ) -> float:
        """Get exchange estimate from ChangeNow."""


        request = EstimateRequest(
            fromCurrency=from_currency.token,
            toCurrency=to_currency.token,
            fromNetwork=from_currency.chain,
            toNetwork=to_currency.chain,
            toAmount=target_amount,
            type=TransactionType.REVERSE,
            flow=FlowType.FIXED_RATE
        )
        
        response: ExchangeEstimate = self.changenow_client.get_estimated_exchange_amount(request)

        return response.from_amount


    async def get_quotes(self, request: QuoteRequest) -> QuoteResponse:
        """Get quotes for converting from input currencies to merchant settlement currencies."""
        # Validate order exists and belongs to merchant
        order = self.db.query(Order).filter(
            Order.id == request.order_id,
        ).first()
        
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
            
        if order.status != OrderStatus.PENDING:
            raise HTTPException(status_code=400, detail="Order is not in pending state")

        # Get merchant's settlement currencies
        merchant = self.db.query(User).get(order.user_id)

        settlement_currencies_and_amounts = [
            {
                "currency": Currency(**currency),
                "goal_amount": await self._usd_to_currency(Currency(**currency), order.total_value_usd)
            }
            for currency in merchant.settlement_currencies
        ]

        input_currencies_and_prices = [
            {
                "currency": currency,
                "price_usd": await self._currency_to_usd(currency, 1)
            } for currency in request.currencies
        ]


        quotes: List[CurrencyQuote] = []

        for input_currency in input_currencies_and_prices:
            quotes_for_different_settlement_currencies = []
            for settlement_currency in settlement_currencies_and_amounts:
                try:
                    amount = await self._get_estimate(
                        input_currency["currency"],
                        settlement_currency["currency"],
                        settlement_currency["goal_amount"]
                    )
                except Exception as e:
                    logger.error(f"Failed to get estimate: {str(e)}")
                    continue

                quote = CurrencyQuote(
                    token=input_currency["currency"].token,
                    chain=input_currency["currency"].chain,
                    price_usd=input_currency["price_usd"],
                    value_usd=amount * input_currency["price_usd"],
                    amount=amount
                )
                quotes_for_different_settlement_currencies.append(quote)
            best_quote = min(quotes_for_different_settlement_currencies, key=lambda x: x.value_usd)
            quotes.append(best_quote)

        return QuoteResponse(
            timestamp=datetime.now(pytz.UTC),
            order_id=order.id,
            quotes=quotes
        )

