# services/payorder.py

from src.models.enums import PayOrderStatus, PayOrderMode
from src.models.schemas.payorder import CreateDepositRequest, CreateSaleRequest, DepositResponse, PayDepositRequest, PayDepositResponse, PaySaleRequest, PaySaleResponse, SaleResponse, UpdateDepositRequest, UpdateSaleRequest 

from src.models.database_models import Organization, SettlementCurrency, PayOrder
from src.services.coingecko import CoinGeckoService
from src.utils.currencies.types import Currency, CurrencyBase
from src.utils.types import ChainId

from .changenow import ChangeNowService
from .quote import QuoteService

from .base import BaseService
from fastapi import HTTPException
from datetime import datetime, timedelta
import pytz
import logging


logger = logging.getLogger(__name__)

class PayOrderService(BaseService[PayOrder]):
    async def get(self, order_id: str):
        """Get a pay order by id"""
        return self.db.query(PayOrder).where(PayOrder.id == order_id).first()
    
  
    async def get_all(self, org_id: str):
        """Get all pay orders for an organization"""
        return self.db.query(PayOrder).where(PayOrder.organization_id == org_id).all()



    #
    #   SALE
    #

    async def create_sale(self, org_id: str, req: CreateSaleRequest) -> SaleResponse:
        """
        Create a sale order

        org_id: str (Organization ID)
        req: CreateSaleRequest
            - metadata: dict
            - destination_value_usd: float

        Returns: SaleResponse
            - id: str
            - mode: PayOrderMode
            - status: PayOrderStatus

            - metadata: dict
            - destination_value_usd: float
        """
        # must include value usd
        if not req.destination_value_usd:
            raise HTTPException(
                status_code=422,
                detail="missing required field: destination_value_usd"
            )
    

        # Create PayOrder
        pay_order = PayOrder(
            organization_id=org_id,
            mode=PayOrderMode.SALE,
            status=PayOrderStatus.PENDING,

            destination_value_usd=req.destination_value_usd,
            metadata_= req.metadata.model_dump() if req.metadata else {}
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

        return SaleResponse(
            id=pay_order.id,
            mode=pay_order.mode,
            status=pay_order.status,

            metadata=pay_order.metadata_,
            destination_value_usd=pay_order.destination_value_usd
        )

    async def update_sale(self, payorder_id: str, req: UpdateSaleRequest) -> SaleResponse:
        """
        Update a sale order

        order_id: str
        req: UpdateSaleRequest
            - metadata: dict
            - destination_value_usd: float

        Returns: SaleResponse
            - id: str
            - mode: PayOrderMode
            - status: PayOrderStatus

            - metadata: dict
            - destination_value_usd: float

        """

        # Fetch payorder
        pay_order = self.db.query(PayOrder).get(payorder_id)
        if pay_order is None:
            raise HTTPException( status_code=404, detail="Order not found")

        # Check if payorder is a sale
        if pay_order.mode != PayOrderMode.SALE:
            raise HTTPException( status_code=400, detail="Order is not a sale")

        # Check if the sale is pending
        if pay_order.status != PayOrderStatus.PENDING:
            raise HTTPException( status_code=400, detail="Sale status is not pending, cannot update")


        # Update fields
        pay_order.destination_value_usd = req.destination_value_usd
        pay_order.metadata_ = req.metadata


        try:
            self.db.commit()
            self.db.refresh(pay_order)
        except Exception as e:
            logger.error("Error updating PayOrder: %s", e)
            raise HTTPException(
                status_code=500,
                detail="Error updating PayOrder"
            )


        return SaleResponse(
            id=pay_order.id,
            mode=pay_order.mode,
            status=pay_order.status,
            metadata=pay_order.metadata_,
            destination_value_usd=pay_order.destination_value_usd,
        )

    async def pay_sale(self, payorder_id: str, req: PaySaleRequest) -> PaySaleResponse:
        """
        Create payment details for a sale order

        payorder_id: str
        req: PaySaleRequest
            - source_currency: CurrencyBase
            - refund_address: str

        Returns: PaySaleResponse
            - id: str
            - mode: PayOrderMode
            - status: PayOrderStatus
            - expires_at: datetime

            - source_currency: Currency
            - deposit_address: str
            - amount: int
            - ui_amount: float
        """

        # Find the pay order
        pay_order = self.db.query(PayOrder).get(payorder_id)
        if pay_order is None:
            raise HTTPException( status_code=404, detail="Order not found")

        # Check if payorder is a sale
        if pay_order.mode != PayOrderMode.SALE:
            raise HTTPException( status_code=400, detail="Order is not a sale")

        # Check if payorder status is pending
        if pay_order.status != PayOrderStatus.PENDING:
            raise HTTPException( status_code=400, detail="Sale status is not pending, cannot create payment")


        org = self.db.query(Organization).get(pay_order.organization_id)
        if org is None:
            raise HTTPException( status_code=404, detail="Organization not found")


        async with CoinGeckoService() as cg:
            source_currency = await cg.get_token_info(req.source_currency)
        if not source_currency:
            raise HTTPException( status_code=400, detail="Invalid source_currency")

        # Organization settlement currencies
        settlement_currencies = [SettlementCurrency.from_dict(c) for c in org.settlement_currencies]

        # Find optimal settlement currency to route payment
        quote_service = QuoteService()
        quotes = await quote_service._get_quote_value_usd(
            from_currencies=[source_currency],
            to_currencies=[c.currency_id for c in settlement_currencies],
            value_usd=pay_order.destination_value_usd
        )

        quote = min(quotes, key=lambda x: x.value_usd)
        settlement_currency = next(c for c in settlement_currencies if c.currency_id == quote.out_currency.id)

        # Create ChangeNow exchange
        async with ChangeNowService() as cn:
            exch = await cn.exchange(
                address=settlement_currency.address,
                refund_address=req.refund_address,
                amount=quote.in_amount,
                currency_in=quote.in_currency,
                currency_out=quote.out_currency
            )

        # Update PayOrder
        pay_order.source_value_usd = quote.value_usd
        pay_order.source_amount = source_currency.ui_amount_to_amount(exch.from_amount)
        pay_order.source_currency_id = source_currency.id
        pay_order.source_deposit_address = exch.deposit_address

        pay_order.destination_currency_id = quote.out_currency.id
        pay_order.destination_amount = quote.out_currency.ui_amount_to_amount(quote.out_amount),
        pay_order.destination_address = settlement_currency.address

        pay_order.status = PayOrderStatus.AWAITING_PAYMENT
        pay_order.expires_at = datetime.now(pytz.utc) + timedelta(minutes=15)
        pay_order.refund_address = req.refund_address

        try:
            self.db.commit()
            self.db.refresh(pay_order)
        except Exception as e:
            logger.error("Error updating PayOrder: %s", e)
            raise HTTPException(
                status_code=500,
                detail="Error updating PayOrder"
            )

        #return pay_order
        

        return PaySaleResponse(
            id=pay_order.id,
            mode=pay_order.mode,
            status=pay_order.status,
            expires_at=pay_order.expires_at,

            source_currency=source_currency,
            deposit_address=pay_order.source_deposit_address,
            amount=pay_order.source_amount,
            ui_amount=exch.from_amount
        )





    #
    #   DEPOSIT
    #



    async def create_deposit(self, org_id: str, req: CreateDepositRequest) -> DepositResponse:
        """
        Create a deposit order

        org_id: str (Organization ID)
        req: CreateDepositRequest
            - metadata: dict
            - destination_currency: CurrencyBase


        Returns: DepositResponse
            - id: str
            - mode: PayOrderMode
            - status: PayOrderStatus

            - metadata: dict
            - destination_currency: Currency
        """

        # fetch destination currency info
        async with CoinGeckoService() as cg:
            destination_currency = await cg.get_token_info(req.destination_currency)

        if not destination_currency:
            raise HTTPException( status_code=400, detail="Invalid destination_currency")

        # Create PayOrder
        pay_order = PayOrder(
            organization_id=org_id,
            mode=PayOrderMode.DEPOSIT,
            status=PayOrderStatus.PENDING,
            metadata_=req.metadata,

            destination_currency_id=destination_currency.id,
        )

        try:
            self.db.add(pay_order)
            self.db.commit()
            self.db.refresh(pay_order)
        except Exception as e:
            logger.error("Error creating PayOrder: %s", e)
            raise HTTPException( status_code=500, detail="Error creating PayOrder" ) from e

        return DepositResponse(
            id=pay_order.id,
            mode=pay_order.mode,
            status=pay_order.status,
            metadata=pay_order.metadata_,
            destination_currency=destination_currency
        )



    async def update_deposit(self, payorder_id: str, req: UpdateDepositRequest) -> DepositResponse:
        """
        Update a deposit order

        order_id: str
        req: UpdateDepositRequest
            - metadata: dict
            - destination_currency: CurrencyBase

        Returns: DepositResponse
            - id: str
            - mode: PayOrderMode
            - status: PayOrderStatus

            - metadata: dict
            - destination_currency: Currency

        """

        # Fetch payorder
        pay_order = self.db.query(PayOrder).get(payorder_id)

        # Check if order exists
        if pay_order is None:
            raise HTTPException( status_code=404, detail="Deposit order not found")

        # Check if payorder is a deposit
        if pay_order.mode != PayOrderMode.DEPOSIT:
            raise HTTPException( status_code=400, detail="Order is not a deposit")

        # Check if payorder status is pending
        if pay_order.status != PayOrderStatus.PENDING:
            raise HTTPException( status_code=400, detail="Deposit status is not pending, cannot update")


        # Update fields
        async with CoinGeckoService() as cg:
            destination_currency = await cg.get_token_info(req.destination_currency)
        if not destination_currency:
            raise HTTPException( status_code=400, detail="Invalid destination_currency")

        pay_order.destination_currency_id = destination_currency.id
        pay_order.metadata_ = req.metadata

        try:
            self.db.commit()
            self.db.refresh(pay_order)
        except Exception as e:
            logger.error("Error updating PayOrder: %s", e)
            raise HTTPException(
                status_code=500,
                detail="Error updating PayOrder"
            )

        return DepositResponse(
            id=pay_order.id,
            mode=pay_order.mode,
            status=pay_order.status,
            metadata=pay_order.metadata_,
            destination_currency=destination_currency
        )


    async def pay_deposit(self, payorder_id: str, req: PayDepositRequest) -> PayDepositResponse:
        """
        Create payment details for a deposit order

        payorder_id: str
        req: PayDepositRequest
            - source_currency: CurrencyBase
            - destination_amount: float
            - destination_address: str
            - refund_address: str

        Returns: PayDepositResponse
            - id: str 
            - mode: PayOrderMode
            - status: PayOrderStatus
            - expires_at: datetime

            - source_currency: Currency
            - source_deposit_amount: int
            - source_deposit_ui_amount: float
            - deposit_address: str
            - refund_address: str

            - destination_currency: Currency
            - destination_amount: int
            - destination_ui_amount: float
            - destination_address: str

        """

        # Fetch payorder
        pay_order = self.db.query(PayOrder).get(payorder_id)
        if pay_order is None:
            raise HTTPException( status_code=404, detail="Order not found")

        # Check if payorder is a deposit
        if pay_order.mode != PayOrderMode.DEPOSIT:
            raise HTTPException( status_code=400, detail="Order is not a deposit")

        # Check if payorder status is pending
        if pay_order.status != PayOrderStatus.PENDING:
            raise HTTPException( status_code=400, detail="Deposit status is not pending, cannot update")

        async with CoinGeckoService() as cg:
            source_currency = await cg.get_token_info(req.source_currency)
            destination_currency = await cg.get_token_info(pay_order.destination_currency_id)

        if not source_currency:
            raise HTTPException( status_code=400, detail="Invalid source_currency")
        if not destination_currency:
            raise HTTPException( status_code=400, detail="Invalid destination_currency")


        # Get quote (Later on via different services)
        quote_service = QuoteService()
        quotes = await quote_service._get_quote_currency_out(
            from_currencies=[source_currency],
            to_currency=destination_currency,
            amount_out=req.destination_amount
        )

        quote = min(quotes, key=lambda x: x.value_usd)

        # Create ChangeNow exchange
        async with ChangeNowService() as cn:
            exch = await cn.exchange(
                address=req.destination_address,
                refund_address=req.refund_address,
                amount=quote.in_amount,
                currency_in=quote.in_currency,
                currency_out=quote.out_currency
            )

        # Update PayOrder
        pay_order.source_currency_id = source_currency.id
        pay_order.source_amount = source_currency.ui_amount_to_amount(exch.from_amount)
        pay_order.source_deposit_address = exch.deposit_address

        pay_order.destination_amount = destination_currency.ui_amount_to_amount(quote.out_amount)
        pay_order.destination_address = req.destination_address

        pay_order.refund_address = req.refund_address

        pay_order.status = PayOrderStatus.AWAITING_PAYMENT
        pay_order.expires_at = datetime.now(pytz.utc) + timedelta(minutes=15)


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

        return PayDepositResponse(
            id=pay_order.id,
            mode=pay_order.mode,
            status=pay_order.status,
            expires_at=pay_order.expires_at,
            source_currency=source_currency,
            source_deposit_amount=pay_order.source_amount,
            source_deposit_ui_amount=exch.from_amount,
            deposit_address=pay_order.source_deposit_address,
            refund_address=pay_order.refund_address,
            destination_currency=destination_currency,
            destination_amount=pay_order.destination_amount,
            destination_ui_amount=quote.out_amount,
            destination_address=pay_order.destination_address
        )
