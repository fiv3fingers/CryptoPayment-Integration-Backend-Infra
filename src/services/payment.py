# services/payment.py
from typing import Optional, List
from datetime import datetime, timedelta
import pytz

from src.models.enums import RoutingServiceType
from src.models.schemas.payment import PaymentResponse
from src.models.database_models import Order, OrderItem, Payment, Product, Organization, SettlementCurrency
from src.models.schemas.order import OrderCreate, OrderUpdate, OrderResponse
from src.models.database_models import OrderStatus

from .changenow import ChangeNowService
from .coingecko import CoinGeckoService
from .quote import QuoteService

from fastapi import HTTPException
import logging

from .base import BaseService

logger = logging.getLogger(__name__)

class PaymentService(BaseService[Payment]):
    async def create(self, order_id: str, currency_id: str, refund_address: str) -> PaymentResponse:
        order = self.db.query(Order).get(order_id)
        if not order:
            raise HTTPException(
                status_code=404,
                detail=f"Order {order_id} not found"
            )
        
        if order.status != OrderStatus.PENDING:
            raise HTTPException(
                status_code=400,
                detail="Order is not pending"
            )

        org = self.db.query(Organization).get(order.organization_id)
        if not org:
            raise HTTPException(
                status_code=404,
                detail=f"Organization {order.organization_id} not found"
            )

        settlement_currencies = [SettlementCurrency.from_dict(c) for c in org.settlement_currencies]

        print("-- Settlement Currencies --")
        for c in settlement_currencies:
            print(c)
        print("")

        # Get quote
        quote_service = QuoteService()
        quotes = await quote_service._get_quote(
            from_currencies=[currency_id],
            to_currencies=[c.currency_id for c in settlement_currencies],
            value_usd=order.total_value_usd
        )

        quote = min(quotes, key=lambda x: x.value_usd)

        print("-- Quote --")
        print(quote)
        print("")



        settlement_currency = next(c for c in settlement_currencies if c.currency_id == quote.currency_out.id)

        print("-- Exchange params --")
        print(f"Address: {settlement_currency.address}")
        print(f"Refund Address: {refund_address}")
        print(f"Currency In: {quote.currency}")
        print(f"Currency Out: {quote.currency_out}")
        print(f"Amount: {quote.amount}")
        print("")

        # Create payment
        cn = ChangeNowService()
        exch = await cn.exchange(
            address=settlement_currency.address,
            refund_address=refund_address,
            currency_in=quote.currency,
            currency_out=quote.currency_out,
            amount=quote.amount,
        )

        print("-- Exchange --")
        for k, v in exch.model_dump().items():
            print(f"{k}: {v}")

        payment = Payment(
            order_id=order_id,
            organization_id=order.organization_id,
            refund_address=refund_address,
            in_value_usd=quote.value_usd,
            in_amount=exch.from_amount,
            in_currency=quote.currency.id,
            in_address=exch.deposit_address,
            out_value_usd=0,
            out_amount=exch.to_amount,
            out_currency=quote.currency_out.id,
            out_address=settlement_currency.address,
            routing_service=RoutingServiceType.CHANGENOW,
            routing_reference=exch.id,
            expires_at=datetime.now(pytz.utc) + timedelta(hours=1),
            updated_at=datetime.now(pytz.utc)
        )

        try:
            self.db.add(payment)
            self.db.commit()
            return PaymentResponse(
                order_id=order_id,
                value_usd=payment.in_value_usd,
                currency=quote.currency,
                address=payment.in_address,
                amount=payment.in_amount,
                expires_at=payment.expires_at
            
            )
        except Exception as e:
            logger.error(e)
            self.db.rollback()
            raise HTTPException(
                status_code=500,
                detail="Failed to create payment"
            )



       

    
