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

from utils import evm

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


        if currency.network.lower() == "btc" and currency.ticker.lower() == "btc":
            return amount * 95000


        if currency.ticker.lower() == "usdc" or currency.ticker.lower() == "usdt" or currency.ticker.lower() == "dai":
            return amount

        if currency.network.lower() == "eth":
            if currency.ticker.lower() == "eth":
                return amount * 3500
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


    async def get_quotes(self, order_id: str, chain_name: str, wallet_address: str) -> QuoteResponse:
        """Get quotes for converting from input currencies to merchant settlement currencies."""
        # Validate order exists and belongs to merchant
        order: Order = self.db.query(Order).filter(
            Order.id == order_id,
        ).first()
        
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
            
        if order.status != OrderStatus.PENDING:
            raise HTTPException(status_code=400, detail="Order is not in pending state")

        # Get merchant's settlement currencies
        merchant = self.db.query(Organization).get(order.organization_id)

        settlement_currencies_and_amounts = []
        for currency in merchant.settlement_currencies:
            currency_obj = await self.currency_service.get_by_ca(currency["token"].lower(), currency["chain"].lower())
            if not currency_obj:
                logger.error(f"Currency not found: {currency}")
                continue
            settlement_currencies_and_amounts.append({
                "currency": currency_obj,
                "goal_amount": await self._usd_to_currency(currency_obj, order.total_value_usd)
            })


        # Get user's input currencies
        all_currencies = self.currency_service.get_currencies(networks=[chain_name])
        token_balances = evm.get_token_balances(wallet_address, chain_name)
        relevant_cas = [t.contractAddress.lower() for t in token_balances if t.tokenBalance > 0]
        user_currencies = [c for c in all_currencies if not c.is_native and c.token_contract.lower() in relevant_cas]

        native_balance = evm.get_native_balance(wallet_address, chain_name)
        if native_balance > 0:
            native_currency = next((c for c in all_currencies if c.network == chain_name and c.is_native), None)
            if native_currency:
                print(native_currency)
                user_currencies.append(native_currency)


        quotes: List[CurrencyQuote] = []

        for input_currency in user_currencies:
            quotes_for_different_settlement_currencies = []
            for settlement_currency in settlement_currencies_and_amounts:
                try:
                    amount = await self._get_estimate(
                        input_currency,
                        settlement_currency["currency"],
                        settlement_currency["goal_amount"]
                    )
                except Exception as e:
                    logger.error(f"Failed to get estimate: {str(e)}")
                    continue

                quote = CurrencyQuote(
                    currency=input_currency,
                    amount=amount
                )
                quotes_for_different_settlement_currencies.append(quote)
            best_quote = min(quotes_for_different_settlement_currencies, key=lambda x: x.amount)
            quotes.append(best_quote)

        return QuoteResponse(
            timestamp=datetime.now(pytz.UTC),
            order_id=order.id,
            quotes=quotes
        )

