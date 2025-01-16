# services/payorder.py
from datetime import datetime, timedelta
import pytz

from src.models.enums import PayOrderStatus, PayOrderMode
from src.models.schemas import payorder
from src.models.schemas.payorder import CreatePaymentResponse, PayOrderCreate, PayOrderResponse

from src.models.database_models import Organization, SettlementCurrency, PayOrder
from src.utils.currencies.types import CurrencyBase
from src.utils.types import ChainId

from .changenow import ChangeNowService
from .quote import QuoteService

from .base import BaseService
from fastapi import HTTPException
import logging


logger = logging.getLogger(__name__)

class PayOrderService(BaseService[PayOrder]):

    async def create_sale(self, org_id: str, req: PayOrderCreate):
        org = self.db.query(Organization).get(org_id)

        # must include valaue usd
        if not req.out_value_usd:
            raise HTTPException(
                status_code=400,
                detail="out_value_usd is required for sales"
            )

        # Create PayOrder
        pay_order = PayOrder(
            organization_id=org_id,
            mode=req.mode,
            status=PayOrderStatus.PENDING,
            out_value_usd=req.out_value_usd,
            metadata=req.metadata,
            expires_at=datetime.now(pytz.utc) + timedelta(minutes=15)
        )

        try:
            self.db.add(pay_order)
            self.db.commit()
            self.db.refresh(pay_order)
        except Exception as e:
            logger.error("Error creating PayOrder: %s", e)
            raise HTTPException(
                status_code=500,
                detail="Error creating PayOrder"
            ) from e

        return PayOrderResponse(
            id=pay_order.id,
            mode=pay_order.mode,
            status=pay_order.status,
            metadata=pay_order.metadata,
            created_at=pay_order.created_at,
            expires_at=pay_order.expires_at,
        )


    async def create_deposit(self, org_id: str, req: PayOrderCreate):
        org = self.db.query(Organization).get(org_id)

        print("~~~ DEPOSIT PAYORDER ~~~")
        for (k, v) in req.model_dump().items():
            print(f"{k}: {v}")

        # Verify required fields
        if not req.out_amount:
            raise HTTPException( status_code=400, detail="out_amount is required for deposits")

        #if not req.out_token_address:
        #    raise HTTPException( status_code=400, detail="out_currency_id is required for deposits")

        if not req.out_token_chain_id:
            raise HTTPException( status_code=400, detail="out_address is required for deposits")

        if not req.out_address:
            raise HTTPException( status_code=400, detail="out_address is required for deposits")

        #if not req.in_token_address:
        #    raise HTTPException( status_code=400, detail="in_currency_id is required for deposits")

        if not req.in_token_chain_id:
            raise HTTPException( status_code=400, detail="in_token_chain_id is required for deposits")

        if not req.refund_address:
            raise HTTPException( status_code=400, detail="refund_address is required for deposits")



        # Build curenncy objects
        in_currency = CurrencyBase(
            address=req.in_token_address,
            chain_id=req.in_token_chain_id
        )

        out_currency = CurrencyBase(
            address=req.out_token_address,
            chain_id=req.out_token_chain_id
        )



        # Find optimal route
        quote_service = QuoteService()
        quotes = await quote_service._get_quote_currency_out(
            from_currencies=[in_currency],
            to_currency=out_currency,
            amount_out=req.out_amount
        )

        quote = min(quotes, key=lambda x: x.value_usd)

        print("~~~ QUOTE ~~~")
        for (k, v) in quote.model_dump().items():
            print(f"{k}: {v}")


        # Create ChangeNow exchange
        cn = ChangeNowService()
        exch = await cn.exchange(
            address=req.out_address,
            refund_address=req.refund_address,
            amount=quote.in_amount,
            currency_in=quote.in_currency,
            currency_out=quote.out_currency
        )

        # Create PayOrder
        pay_order = PayOrder(
            organization_id=org_id,
            mode=req.mode,
            status=PayOrderStatus.PENDING,
            in_value_usd=quote.value_usd,
            in_amount=exch.from_amount,
            in_currency_id=in_currency.id,
            in_address=exch.deposit_address,
            out_value_usd=None,
            out_amount=quote.out_amount,
            out_currency_id=quote.out_currency.id,
            out_address=req.out_address,
            refund_address=req.refund_address,
            expires_at=datetime.now(pytz.utc) + timedelta(minutes=15)
        )

        try:
            self.db.add(pay_order)
            self.db.commit()
            self.db.refresh(pay_order)
        except Exception as e:
            logger.error("Error creating PayOrder: %s", e)
            raise HTTPException(
                status_code=500,
                detail="Error creating PayOrder"
            ) from e

        return PayOrderResponse(
            id=pay_order.id,
            mode=pay_order.mode,
            status=pay_order.status,
            in_currency=quote.in_currency,
            in_amount=pay_order.in_amount,
            in_value_usd=pay_order.in_value_usd,
            in_address=pay_order.in_address,
            created_at=pay_order.created_at,
            expires_at=pay_order.expires_at,
            out_currency=quote.out_currency,
            out_amount=pay_order.out_amount,
            out_value_usd=pay_order.out_value_usd,
            out_address=pay_order.out_address,
        )


    async def create(self, org_id: str, req: PayOrderCreate):
        """Create a pay order"""
        if req.mode == PayOrderMode.SALE:
            print("~~~ SALE PAYORDER ~~~")
            return await self.create_sale(org_id, req)
        if req.mode == PayOrderMode.DEPOSIT:
            print("~~~ DEPOSIT PAYORDER ~~~")
            return await self.create_deposit(org_id, req)

        raise HTTPException(
            status_code=400,
            detail="Invalid mode"
        )

    async def get(self, org_id: str, order_id: str):
        """Get a pay order by id"""
        pay_order = self.db.query(PayOrder).where(
            PayOrder.id == order_id, PayOrder.organization_id == org_id
            ).first()
        if pay_order is None:
            raise HTTPException(
                status_code=404,
                detail="Order not found"
            )

        return pay_order
  
    async def get_all(self, org_id: str):
        """Get all pay orders for an organization"""
        return self.db.query(PayOrder).where(PayOrder.organization_id == org_id).all()


    async def pay_sale(self, payorder_id: str, in_token_address: str, in_chain_id: ChainId, refund_address: str):
        """ Create a payment for a sale """

        # Find the pay order
        pay_order = self.db.query(PayOrder).get(payorder_id)
        if pay_order is None:
            raise HTTPException(
                status_code=404,
                detail="Order not found"
            )

        org = self.db.query(Organization).get(pay_order.organization_id)
        if org is None:
            raise HTTPException(
                status_code=404,
                detail="Organization not found"
            )

        in_currency = CurrencyBase(
            address=in_token_address,
            chain_id=in_chain_id
        )

        # Organization settlement currencies
        settlement_currencies = [SettlementCurrency.from_dict(c) for c in org.settlement_currencies]

        # Find optimal route
        quote_service = QuoteService()
        quotes = await quote_service._get_quote_value_usd(
            from_currencies=[in_currency],
            to_currencies=[c.currency_id for c in settlement_currencies],
            value_usd=pay_order.out_value_usd
        )

        quote = min(quotes, key=lambda x: x.value_usd)
        settlement_currency = next(c for c in settlement_currencies if c.currency_id == quote.out_currency.id)

        # Create ChangeNow exchange
        cn = ChangeNowService()
        exch = await cn.exchange(
            address=settlement_currency.address,
            refund_address=refund_address,
            amount=quote.amount,
            currency_in=quote.in_currency,
            currency_out=quote.out_currency
        )

        # Update PayOrder
        pay_order.in_value_usd = quote.value_usd
        pay_order.in_amount = exch.from_amount
        pay_order.in_currency_id = in_currency.id
        pay_order.in_address = exch.deposit_address

        pay_order.out_currency_id = quote.out_currency.id
        pay_order.out_amount = quote.amount
        pay_order.out_address = settlement_currency.address

        pay_order.status = PayOrderStatus.AWAITING_PAYMENT
        pay_order.expires_at = datetime.now(pytz.utc) + timedelta(minutes=15)
        pay_order.refund_address = refund_address

        try:
            self.db.commit()
            self.db.refresh(pay_order)
        except Exception as e:
            logger.error("Error updating PayOrder: %s", e)
            raise HTTPException(
                status_code=500,
                detail="Error updating PayOrder"
            )

        return CreatePaymentResponse(
            id=pay_order.id,
            currency=quote.in_currency,
            amount=pay_order.in_amount,
            address=pay_order.in_address,
            expires_at=pay_order.expires_at
        )



        





