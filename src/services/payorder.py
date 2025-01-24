# services/payorder.py

from src.models.enums import PayOrderStatus, PayOrderMode, RoutingServiceType
from src.models.schemas.payorder import (
    CreatePayOrderRequest, 
    PayOrderResponse,
    CreateQuoteRequest,
    CreateQuoteResponse,
    PaymentDetailsRequest,
    PaymentDetailsResponse,
)

from src.models.database_models import SettlementCurrency, PayOrder, Organization
from src.services.coingecko import CoinGeckoService
from src.utils.currencies.types import Currency
from src.utils.blockchain.blockchain import get_wallet_balances

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


    async def create_payorder(self, org_id: str, req: CreatePayOrderRequest) -> PayOrderResponse:
        """
        Create a pay order

        org_id: str (Organization ID)
        req: CreatePayOrderRequest
            - mode: PayOrderMode                          
            - destination_currency: Optional[CurrencyBase]
            - destination_amount: Optional[float]         
            - destination_value_usd: Optional[float]      
            - destination_receiving_address: Optional[str]
            - metadata: Optional[PayOrderMetadata]        
            
        Returns: PayOrderResponse
            - id: str
            - mode: PayOrderMode
            - status: PayOrderStatus

            - metadata: dict
            - destination_currency: Currency
        """

        destination_currency: Currency | None = None
        if req.destination_currency:
            async with CoinGeckoService() as cg:
                destination_currency = await cg.get_token_info(req.destination_currency)

            if not destination_currency:
                raise HTTPException( status_code=400, detail="Invalid destination_currency")
        
        if req.mode == PayOrderMode.DEPOSIT:
            if not req.destination_amount:
                raise HTTPException( status_code=400, detail="Destination amount is required for deposit orders")
            if req.destination_value_usd:
                raise HTTPException( status_code=400, detail="Destination value USD is not required for deposit orders")

        if req.mode == PayOrderMode.SALE:
            if req.destination_amount:
                if not destination_currency:
                    raise HTTPException( status_code=400, detail="Destination currency is required for destination amount")
            if req.destination_value_usd:
                if req.destination_currency:
                    raise HTTPException( status_code=400, detail="Destination value USD is not required for destination currency")

        # Convert user friendly destinatino amount to int amount
        _destination_amount: int | None = None
        if destination_currency and req.destination_amount:
            _destination_amount = destination_currency.ui_amount_to_amount(req.destination_amount)

        # Create PayOrder
        pay_order = PayOrder(
            organization_id=org_id,
            mode=req.mode,
            status=PayOrderStatus.PENDING,
            metadata_=req.metadata.model_dump() if req.metadata else {},

            destination_currency_id=destination_currency.id if destination_currency else None,
            destination_amount=_destination_amount if _destination_amount else None,
            destination_value_usd=req.destination_value_usd,
            destination_receiving_address=req.destination_receiving_address
        )

        try:
            self.db.add(pay_order)
            self.db.commit()
            self.db.refresh(pay_order)
        except Exception as e:
            logger.error("Error creating PayOrder: %s", e)
            raise HTTPException( status_code=500, detail="Error creating PayOrder" ) from e

        return PayOrderResponse(
            id=pay_order.id,
            mode=pay_order.mode,
            status=pay_order.status,
            metadata=pay_order.metadata_,
            destination_currency=destination_currency,
            destination_amount=req.destination_amount,
            destination_value_usd=pay_order.destination_value_usd
        )


    async def quote(self, payorder_id: str, req: CreateQuoteRequest) -> CreateQuoteResponse:
        """
        Get a quote for a pay order

        payorder_id: str
        req: CreateQuoteRequest
            - wallet_address: str
            - chain_id: ChainId

        Returns: QuoteDepositResponse
            source_currencies: List[Currency]
        """

        # Fetch payorder
        pay_order: PayOrder | None = self.db.query(PayOrder).get(payorder_id)
        if pay_order is None:
            raise HTTPException(status_code=404, detail="Order not found")

        # Check if payorder status is pending
        #if pay_order.status != PayOrderStatus.PENDING:
        #    raise HTTPException(status_code=400, detail="PayOrder status is not pending. Quote cannot be created")

        # Fetch wallet currencies
        all_wallet_balances = get_wallet_balances(req.wallet_address, req.chain_id)
        async with ChangeNowService() as cn:
            wallet_currencies = [b.currency for b in all_wallet_balances if await cn.is_supported(b.currency)]

        quote_service = QuoteService()

        # If SALE payOrder and the destination_currency_id is not set, quote based on settlement currencies 
        # (value_usd, NO destination_currency_id set)
        if (pay_order.mode == PayOrderMode.SALE) and (pay_order.destination_currency_id is None):
            org = self.db.query(Organization).get(pay_order.organization_id)
            if org is None:
                raise HTTPException( status_code=404, detail="Organization not found")
            settlement_currencies = [SettlementCurrency.from_dict(c) for c in org.settlement_currencies]

            async with CoinGeckoService() as cg:
                destination_currencies = [await cg.get_token_info(c.currency_id) for c in settlement_currencies]
            if not destination_currencies:
                raise HTTPException(status_code=400, detail="Invalid destination_currency")
            
            quotes = await quote_service._get_quote_value_usd(
                from_currencies=wallet_currencies,
                to_currencies=destination_currencies,
                value_usd=pay_order.destination_value_usd
            )

        # Otherwise quote based on destination currency
        else:
            async with CoinGeckoService() as cg:
                destination_currency = await cg.get_token_info(pay_order.destination_currency_id)
            if not destination_currency:
                raise HTTPException(status_code=400, detail="Invalid destination_currency")

            quotes = await quote_service._get_quote_currency_out(
                from_currencies=wallet_currencies,
                to_currency=destination_currency,
                amount_out=destination_currency.amount_to_ui_amount(pay_order.destination_amount)
            )

        response_source_currencies = [q.in_currency for q in quotes]
        for c in response_source_currencies:
            c.balance = next(b.amount for b in all_wallet_balances if b.currency.id == c.id)
            c.ui_balance = float(c.amount_to_ui_amount(c.balance))

        return CreateQuoteResponse(
            source_currencies=response_source_currencies,
        )

    async def payment_details(self, payorder_id: str, req: PaymentDetailsRequest) -> PaymentDetailsResponse:
        """
        Create payment details

        payorder_id: str
        req: PaymentDetailsRequest
            - source_currency: CurrencyBase
            - refund_address: str

        Returns: PaymentDetailsResponse
            - id: str 
            - mode: PayOrderMode
            - status: PayOrderStatus
            - expires_at: datetime

            - source_currency: Currency
            - deposit_address: str
            - refund_address: str

            - destination_currency: Optional[Currency]
            - destination_receiving_address: Optional[str]

        """

        # Fetch payorder
        pay_order = self.db.query(PayOrder).get(payorder_id)
        if pay_order is None:
            raise HTTPException( status_code=404, detail="Order not found")

        # Check if payorder status is pending
        if pay_order.status != PayOrderStatus.PENDING:
            raise HTTPException( status_code=400, detail="Deposit status is not pending, cannot update")

        quote_service = QuoteService()

        async with CoinGeckoService() as cg:
            source_currency = await cg.get_token_info(req.source_currency)
        if not source_currency:
            raise HTTPException( status_code=400, detail="Invalid source_currency")


        is_sale: bool = pay_order.mode == PayOrderMode.SALE


        # destination_currency_id for SALE is not set => payment details based on settlement currencies in organization
        if is_sale and (pay_order.destination_currency_id is None):
            org = self.db.query(Organization).get(pay_order.organization_id)
            if org is None:
                raise HTTPException( status_code=404, detail="Organization not found")
            settlement_currencies = [SettlementCurrency.from_dict(c) for c in org.settlement_currencies]

            async with CoinGeckoService() as cg:
                destination_currencies = [await cg.get_token_info(c.currency_id) for c in settlement_currencies]
            if not destination_currencies or len(destination_currencies) == 0:
                raise HTTPException(status_code=400, detail="Invalid settlement_currency")

            # Get quote
            quotes = await quote_service._get_quote_value_usd(
                from_currencies=[source_currency],
                to_currencies=destination_currencies,
                value_usd=pay_order.destination_value_usd
            )
            quote = min(quotes, key=lambda x: x.value_usd)

            destination_currency = quote.out_currency
            
            destination_receiving_address = next(c.address for c in settlement_currencies if c.currency_id == destination_currency.id)


        else:
            # destination_currency_id is set => payment details based on destination_currency_id

            async with CoinGeckoService() as cg:
                destination_currency = await cg.get_token_info(pay_order.destination_currency_id)
            if not destination_currency:
                raise HTTPException( status_code=400, detail="Invalid destination_currency")

            # Get quote
            quotes = await quote_service._get_quote_currency_out(
                from_currencies=[source_currency],
                to_currency=destination_currency,
                amount_out=destination_currency.amount_to_ui_amount(pay_order.destination_amount)
            )
            quote = min(quotes, key=lambda x: x.value_usd)

            destination_receiving_address = pay_order.destination_receiving_address


        # Create ChangeNow exchange
        async with ChangeNowService() as cn:
            exch = await cn.exchange(
                address=destination_receiving_address,
                refund_address=req.refund_address,
                amount=quote.in_currency.ui_amount,
                currency_in=quote.in_currency,
                currency_out=quote.out_currency
            )


        # Update amounts
        source_currency.ui_amount = exch.from_amount
        source_currency.amount = source_currency.ui_amount_to_amount(source_currency.ui_amount)

        destination_currency.ui_amount = quote.out_currency.ui_amount
        destination_currency.amount = destination_currency.ui_amount_to_amount(destination_currency.ui_amount)

        # Update PayOrder
        pay_order.source_currency_id = source_currency.id
        pay_order.source_amount = source_currency.amount
        pay_order.source_deposit_address = exch.deposit_address

        pay_order.destination_amount = destination_currency.amount
        pay_order.destination_receiving_address = destination_receiving_address

        pay_order.refund_address = req.refund_address

        pay_order.routing_reference = exch.id
        pay_order.routing_service = RoutingServiceType.CHANGENOW

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

        return PaymentDetailsResponse(
            id=pay_order.id,
            mode=pay_order.mode,
            status=pay_order.status,
            expires_at=pay_order.expires_at,
            source_currency=source_currency,
            deposit_address=pay_order.source_deposit_address,
            refund_address=pay_order.refund_address,
            
            destination_currency=None if is_sale else destination_currency,
            destination_receiving_address=None if is_sale else pay_order.destination_receiving_address
        )

    
