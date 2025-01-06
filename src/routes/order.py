# routes/order.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.models.schemas.payment import PaymentResponse
from src.database.dependencies import get_db, get_current_organization
from src.services.order import OrderService
from src.models.schemas.order import (
    OrderCreate,
    OrderUpdate,
    OrderResponse,
)
from src.models.database_models import Organization

from src.services.quote import QuoteService
from src.models.schemas.quote import (
    QuoteRequest,
    QuoteResponse,
)

from src.services.payment import PaymentService

from src.utils.blockchain.blockchain import get_wallet_currencies
import datetime


router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("/", response_model=OrderResponse)
async def create_order(
    data: OrderCreate,
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    """Create a new order."""
    service = OrderService(db)
    r_orm = await service.create(org.id, data)

    return OrderResponse.from_orm(r_orm)


@router.put("/{order_id}", response_model=OrderResponse)
async def update_order(
    order_id: str,
    data: OrderUpdate,
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    """Update an existing order."""
    service = OrderService(db)
    r_orm = await service.update(org.id, order_id, data)
    return OrderResponse.from_orm(r_orm)


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: str,
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    """Get a specific order by ID."""
    service = OrderService(db)
    order = await service.get_by_id(order_id, org.id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    return OrderResponse.from_orm(order)


@router.post("/{order_id}/quote", response_model=QuoteResponse)
async def get_quote_for_order(
    order_id: str,
    quote_request: QuoteRequest,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization)
):
    """Get a quote for a specific order"""

    # retrieve the order
    order_service = OrderService(db)
    order = await order_service.get_by_id(order_id, org.id)
    settlement_currencies = await order_service.get_settlement_currencies(order_id)
    settlement_currency_ids = [currency.currency_id for currency in settlement_currencies]
    user_currencies = get_wallet_currencies(quote_request.address, quote_request.chain_id)

    quote_service = QuoteService()
    quotes = await quote_service._get_quote(
        value_usd=order.total_value_usd,
        from_currencies=user_currencies,
        to_currencies=settlement_currency_ids
    )

    if not quotes:
        raise HTTPException(status_code=404, detail="Quotes not found")


    return QuoteResponse(
        order_id=order_id,
        timestamp=datetime.datetime.now(),
        quotes=quotes
    )

@router.post("/{order_id}/pay", response_model=PaymentResponse)
async def create_payment(
    order_id: str,
    curency_id: str,
    refund_address: str,
    db: Session = Depends(get_db),
):
    """Create a payment for a specific order"""

    payment_service = PaymentService(db)
    payment = await payment_service.create(order_id, curency_id, refund_address)
    return payment

