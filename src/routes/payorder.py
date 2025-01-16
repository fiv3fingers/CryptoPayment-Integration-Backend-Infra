# routes/payorder.py
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from src.database.dependencies import get_db, get_current_organization
from src.models.schemas.payorder import (
    PayOrderCreate,
    PayOrderResponse
)
from src.models.database_models import Organization
from src.services.payorder import PayOrderService

router = APIRouter(prefix="/payorder", tags=["payorder"])


@router.post("/", response_model=PayOrderResponse)
async def create_order(
    req: PayOrderCreate,
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    """ API Route for create a new payorder """
    pay_order_service = PayOrderService(db)
    pay_order = await pay_order_service.create(org.id, req)
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
