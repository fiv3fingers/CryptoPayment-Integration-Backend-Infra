# routes/payorder.py
from typing import List, Union
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from src.database.dependencies import get_db, get_current_organization, validate_authorization_header
from src.models.schemas.payorder import (
    CreatePayOrderRequest,
    CreatePayOrderResponse,
    CreateQuoteRequest,
    CreateQuoteResponse,
    PaymentDetailsRequest,
    PaymentDetailsResponse,
    DepositResponse,
    SaleResponse,
)
from src.models.database_models import Organization
from src.services.payorder import PayOrderService

router = APIRouter(prefix="/pay-orders", tags=["Pay Orders"])

@router.post("/", response_model=CreatePayOrderResponse)
async def create_pay_order(
    #request: Request,  # Inject the Request object
    req: CreatePayOrderRequest,
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    """ API Route for create a new pay-order """
    pay_order_service = PayOrderService(db)

    return await pay_order_service.create_payorder(org.id, req)


@router.post("/{order_id}/quote", response_model=CreateQuoteResponse)
async def quote_pay_order(
    order_id: str,
    req: CreateQuoteRequest,
    _: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    """ API Route for creating the final quote including deposit details to submit the transaction """

    pay_order_service = PayOrderService(db)
    resp = await pay_order_service.quote(order_id, req)

    return resp


@router.post("/{order_id}/payment-details", response_model=PaymentDetailsResponse)
async def create_payment_details(
    order_id: str,
    req: PaymentDetailsRequest,
    _: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    """ API Route for creating the final quote including deposit details to submit the transaction """

    pay_order_service = PayOrderService(db)
    resp = await pay_order_service.payment_details(order_id, req)

    return resp



@router.get("/{order_id}", response_model=Union[DepositResponse, SaleResponse])
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
@router.get("/", response_model=List[Union[DepositResponse, SaleResponse]])
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


