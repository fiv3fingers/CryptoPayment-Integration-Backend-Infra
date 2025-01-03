from models.database_models import Organization, Payment, Order
from models.schemas.changenow import Currency, EstimateRequest, TransactionType, FlowType
from models.enums import RoutingServiceType


from services.currency import CurrencyService
from services.changenow import ChangeNowClient, CreateExchangeRequest
from services.base import BaseService

import pytz
import time
import datetime

from fastapi import HTTPException


import logging

from services.quote import QuoteService
logger = logging.getLogger(__name__)

class PaymentService(BaseService):
    def __init__(self, db):
        super().__init__(db)
        self.changenow_client = ChangeNowClient.get_instance()
        self.currency_service = CurrencyService.get_instance()
        self.quote_service = QuoteService(db)

    async def create_payment(
        self, 
        order_id: str, 
        currency_id: str,
        refund_address: str
    ) -> Payment:
        order = self.db.query(Order).filter(
            Order.id == order_id
        ).first()

        print(f"Found order (id={order_id})")

        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        org = self.db.query(Organization).filter(
            Organization.id == order.organization_id
        ).first()

        print(f"Found organization (id={order.organization_id})")

        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")

        currency  = await self.currency_service.get_by_id(currency_id)
        if not currency:
            raise HTTPException(status_code=404, detail="Currency not found")

        print(f"Found currency (id={currency.id})")

        estimates = []
        for sc in org.settlement_currencies:
            c = await self.currency_service.get_by_ca(
                contract_address=sc["token"],
                chain_name=sc["chain"]
            )
            sc_target_amount = await self.quote_service._usd_to_currency(
                currency=c,
                usd_value=order.total_value_usd
            )

            est = self.changenow_client.get_estimated_exchange_amount(
                EstimateRequest(
                    fromCurrency=currency.ticker,
                    toCurrency=c.ticker,
                    fromNetwork=currency.network,
                    toNetwork=c.network,
                    toAmount=sc_target_amount,
                    type=TransactionType.REVERSE,
                    flow=FlowType.FIXED_RATE
                )
            )

            estimates.append({
                "currency": c,
                "destination": sc["address"],
                "amount": est.from_amount
            })


        # choose the best estimate:
        # min(value usd of input currency)
        # but just random for now
        best_estimate = estimates[0]


        # create exchange transaction
        exchange_transaction = self.changenow_client.create_exchange_transaction(
            CreateExchangeRequest(
                fromCurrency=currency.ticker,
                toCurrency=best_estimate["currency"].ticker,
                fromNetwork=currency.network,
                toNetwork=best_estimate["currency"].network,
                fromAmount=best_estimate["amount"],
                address=best_estimate["destination"],
                refundAddress=refund_address
            )
        )

        print(f"Created exchange transaction (id={exchange_transaction.id})")
        for k, v in exchange_transaction.dict().items():
            print(f"{k}: {v}")

        payment = Payment(
            order_id=order_id,
            organization_id=org.id,
            in_value_usd=exchange_transaction.from_amount,
            in_amount=exchange_transaction.from_amount,
            in_token=currency.ticker,
            in_chain=currency.network,
            in_address=exchange_transaction.payin_address,
            out_value_usd=exchange_transaction.to_amount,
            out_amount=exchange_transaction.to_amount,
            out_token=best_estimate["currency"].ticker,
            out_chain=best_estimate["currency"].network,
            out_address=best_estimate["destination"],
            routing_service=RoutingServiceType.CHANGENOW,
            routing_reference=exchange_transaction.id,
            expires_at=pytz.utc.localize(datetime.datetime.now() + datetime.timedelta(minutes=10)),
            updated_at=pytz.utc.localize(datetime.datetime.now())
        )

        try:
            self.db.add(payment)
            self.db.commit()
            self.db.refresh(payment)

            return payment
        except Exception as e:
            logger.exception(f"Failed to create payment: {str(e)}")
            self.db.rollback()
            raise HTTPException(status_code=500, detail="Failed to create payment")








