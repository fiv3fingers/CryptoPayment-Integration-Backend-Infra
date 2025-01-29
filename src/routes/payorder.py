from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.database.dependencies import (
    get_db,
    get_current_organization,
    validate_authorization_header,
    authorization_header,
    api_key_header,
)
from src.models.enums import PayOrderMode, PayOrderStatus
from src.models.schemas.payorder import (
    CreatePayOrderRequest,
    PayOrderResponse,
    CreateQuoteRequest,
    PaymentDetailsRequest,
    PaymentDetailsResponse,
    CurrencyQuote,
)
from src.models.database_models import Organization
from src.services.payorder import PayOrderService
from src.utils.currencies.types import Currency

router = APIRouter(prefix="/pay-orders", tags=["Pay Orders"])


@router.post("/", response_model=PayOrderResponse)
async def create_payorder(
    req: CreatePayOrderRequest,
    db: Session = Depends(get_db),
    api_key=Depends(api_key_header),
    auth_header=Depends(authorization_header),
):

    try:
        if req.mode == PayOrderMode.DEPOSIT:
            org = get_current_organization(api_key, db)
        if req.mode == PayOrderMode.SALE:
            org = validate_authorization_header(auth_header, db)

        if org is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API Key or Signature")

        pay_order_service = PayOrderService(db)
        return await pay_order_service.create_payorder(org.id, req)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{payorder_id}/quote", response_model=List[CurrencyQuote])
async def quote_payorder(
    payorder_id: str,
    req: CreateQuoteRequest,
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """API Route for creating the final quote including deposit details to submit the transaction"""

    pay_order_service = PayOrderService(db)
    resp = await pay_order_service.quote(payorder_id, req, org)

    return resp


@router.post("/{payorder_id}/payment-details", response_model=PaymentDetailsResponse)
async def create_payment_details(
    payorder_id: str,
    req: PaymentDetailsRequest,
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """API Route for creating the final quote including deposit details to submit the transaction"""

    pay_order_service = PayOrderService(db)
    pay_order = await pay_order_service.get(payorder_id)
    if pay_order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    # Check if payorder status is pending
    if pay_order.status != PayOrderStatus.PENDING:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Deposit status is not pending, cannot update")
    
    resp = await pay_order_service.payment_details(pay_order, req, org)

    return resp


@router.get("/{payorder_id}", response_model=PayOrderResponse)
async def get_payorder(
    payorder_id: str,
    db: Session = Depends(get_db),
    _: Organization = Depends(get_current_organization),
):
    """API Route for get a payorder by id"""

    pay_order_service = PayOrderService(db)
    pay_order = await pay_order_service.get(payorder_id)
    if pay_order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return pay_order


@router.get("/{payorder_id}/process", response_model=None)
async def process_payorder(
    payorder_id: str,
    tx_hash: str,
    db: Session = Depends(get_db),
    _: Organization = Depends(get_current_organization),
):
    """API Route for processing a payorder"""

    pay_order_service = PayOrderService(db)
    pay_order = await pay_order_service.get(payorder_id)
    if pay_order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PayOrder not found")

    # Validation
    if pay_order.status != PayOrderStatus.AWAITING_PAYMENT:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="PayOrder status is not awaiting payment"
        )

    pay_order = await pay_order_service.process_payment_txhash(payorder_id, tx_hash)
    await pay_order_service.update(pay_order)

    if pay_order.status == PayOrderStatus.AWAITING_CONFIRMATION:
        # TODO: build in retry mechanism
        pass


#  Admin Routes
@router.get("/", response_model=List[PayOrderResponse])
async def get_orders(
    db: Session = Depends(get_db), org: Organization = Depends(get_current_organization)
):
    """API Route for get all payorders of an organization"""

    # TODO: add pagination
    # TODO: only from dashboard server

    pay_order_service = PayOrderService(db)
    pay_orders = await pay_order_service.get_all(org.id)
    return pay_orders
