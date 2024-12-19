# services/quote.py
from typing import List, Dict
from uuid import UUID

from pydantic import UUID4

from datetime import datetime
import pytz
from fastapi import HTTPException
from sqlalchemy.orm import Session

from models.schemas.currency import Currency
from models.schemas.changenow import TransactionType, FlowType, ExchangeEstimate, EstimateRequest
from models.schemas.quote import QuoteRequest, QuoteResponse, CurrencyQuote
from models.database_models import Order, Organization, OrderStatus

from services.currency import CurrencyService
from services.changenow import ChangeNowClient
from services.base import BaseService

from utils.logging import get_logger
logger = get_logger(__name__)


class QuoteService(BaseService):
    def __init__(self, db: Session):
        super().__init__(db)
        self.changenow_client = ChangeNowClient.get_instance()
        self.currency_service = CurrencyService.get_instance()


    async def _currency_to_usd(
        self,
        currency: Currency,
        amount: float
    ) -> float:
        # FIXME: Implement this method. Currently hardcoded for USDC
        """ Convert an amount of a given currency to USD."""
        if currency.ticker.lower() == "usdc":
            return amount

        if currency.network.lower() == "eth":
            if currency.ticker.lower() == "eth":
                return amount * 4027
            if currency.ticker.lower() == "pepe":
                return amount * 0.000024
        if currency.network.lower() == "sol":
            if currency.ticker.lower() == "sol":
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
            fromCurrency=from_currency.ticker,
            toCurrency=to_currency.ticker,
            fromNetwork=from_currency.network,
            toNetwork=to_currency.network,
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
        merchant = self.db.query(Organization).get(order.organization_id)

        settlement_currencies_and_amounts = []
        for currency in merchant.settlement_currencies:
            currency_obj = await self.currency_service.get_by_id(currency)
            if not currency_obj:
                logger.error(f"Currency not found: {currency}")
                continue
            settlement_currencies_and_amounts.append({
                "currency": currency_obj,
                "goal_amount": await self._usd_to_currency(currency_obj, order.total_value_usd)
            })

        input_currencies_and_prices = []
        for currency in request.currencies:
            currency_obj = await self.currency_service.get_by_id(currency)
            if not currency_obj:
                logger.error(f"Currency not found: {currency}")
                continue
            input_currencies_and_prices.append({
                "currency": currency_obj,
                "price_usd": await self._currency_to_usd(currency_obj, 1)
            })


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
                    currency_id=input_currency["currency"].id,
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

