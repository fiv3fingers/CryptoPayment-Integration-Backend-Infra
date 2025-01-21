# routes/payorder.py
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.database.dependencies import get_db, get_current_organization, validate_authorization_header
from src.models.schemas.payorder import (
    CreatePaymentRequest,
    CreatePaymentResponse,
    PayOrderResponse,
    CreateDepositRequest,
    CreateSaleRequest,
    UpdateDepositRequest,
    UpdateSaleRequest
)
from src.models.database_models import Organization
from src.services.payorder import PayOrderService

router = APIRouter(prefix="/pay-orders", tags=["Pay Orders"])


@router.post("/deposit", response_model=PayOrderResponse)
async def create_deposit_pay_order(
    req: CreateDepositRequest,
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    """ API Route for create a new pay-order of type DEPOSIT """
    pay_order_service = PayOrderService(db)

    return await pay_order_service.create_deposit(org.id, req)


@router.put("/{order_id}/deposit", response_model=PayOrderResponse)
async def update_deposit_pay_order(
    order_id: str,
    req: UpdateDepositRequest,
    _: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    """ API Route for update a payorder """
    pay_order_service = PayOrderService(db)
    return await pay_order_service.update_deposit(order_id, req)


@router.post("/sale", response_model=PayOrderResponse)
async def create_sale_pay_order(
    req: CreateSaleRequest,
    org: Organization = Depends(validate_authorization_header),
    db: Session = Depends(get_db)
):
    """ API Route for create a new pay-order of type SALE """

    pay_order_service = PayOrderService(db)
    return await pay_order_service.create_sale(org.id, req)


@router.put("/{order_id}/sale", response_model=PayOrderResponse)
async def update_sale_pay_order(
    order_id: str,
    req: UpdateSaleRequest,
    _: Organization = Depends(validate_authorization_header),
    db: Session = Depends(get_db)
):
    """ API Route for update a payorder """

    pay_order_service = PayOrderService(db)
    return await pay_order_service.update_sale(order_id, req)


@router.post("/{order_id}/payment-details", response_model=CreatePaymentResponse)
async def create_payment_details(
    order_id: str,
    req: CreatePaymentRequest,
    _: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    """ API Route for creating the final quote including deposit details to submit the transaction """

    pay_order_service = PayOrderService(db)
    pay_order = await pay_order_service.pay(
        payorder_id=order_id,
        source_token_address=req.token_address,
        source_chain_id=req.token_chain_id,
        refund_address=req.refund_address,
    )

    # TODO: return partial PayOrderResponse omitting destination values
    return pay_order


@router.get("/{order_id}", response_model=PayOrderResponse)
async def get_order(
    order_id: str,
    db: Session = Depends(get_db),
    _: Organization = Depends(get_current_organization)
):
    """ API Route for get a payorder by id """

    pay_order_service = PayOrderService(db)
    pay_order = await pay_order_service.get(order_id)
    if pay_order is None:
        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )
    return pay_order


#  Admin Routes
@router.get("/", response_model=List[PayOrderResponse])
async def get_orders(
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization)
):
    """ API Route for get all payorders of an organization """

    # TODO: add pagination
    # TODO: only from dashboard server

    pay_order_service = PayOrderService(db)
    pay_orders = await pay_order_service.get_all(org.id)
    return pay_orders


