# routes/payorder.py
from typing import List, Union
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from src.database.dependencies import get_db, get_current_organization
from src.models.schemas.payorder import (
    CreatePaymentRequest,
    CreatePaymentResponse,
    PayOrderCreate,
    PayOrderResponse,
    UpdatePayOrderRequest,
)
from src.models.database_models import Organization
from src.services.payorder import PayOrderService

router = APIRouter(prefix="/payorder", tags=["payorder"])


@router.post("/create", response_model=PayOrderResponse)
async def create_order(
    req: PayOrderCreate,
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    """ API Route for create a new payorder """
    pay_order_service = PayOrderService(db)
    pay_order = await pay_order_service.create(org.id, req)
    return pay_order

@router.post("/update", response_model=PayOrderResponse)
async def update_order(
    id: str,
    req: UpdatePayOrderRequest,
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    """ API Route for update a payorder """
    pay_order_service = PayOrderService(db)
    pay_order = await pay_order_service.update(id, req)
    return pay_order

@router.post("/pay", response_model=CreatePaymentResponse)
async def pay_sale_order(
    req: CreatePaymentRequest,
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    """ API Route for pay a payorder """
    pay_order_service = PayOrderService(db)
    pay_order = await pay_order_service.pay(
        payorder_id=req.id,
        in_token_address=req.token_address,
        in_chain_id=req.token_chain_id,
        refund_address=req.refund_address,
    )
    return pay_order


@router.get("/", response_model=List[PayOrderResponse])
async def get_orders(
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization)
):
    """ API Route for get all payorders of an organization """
    pay_order_service = PayOrderService(db)
    pay_orders = await pay_order_service.get_all(org.id)
    return pay_orders


@router.get("/{order_id}", response_model=PayOrderResponse)
async def get_order(
    order_id: str,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization)
):
    """ API Route for get a payorder by id """
    pay_order_service = PayOrderService(db)
    pay_order = await pay_order_service.get(org.id, order_id)
    return pay_order
