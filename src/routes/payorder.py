# routes/payorder.py
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


@router.post("/create", response_model=PayOrderResponse)
async def create_order(
    req: PayOrderCreate,
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    pay_order_service = PayOrderService(db)
    pay_order = await pay_order_service.create(org.id, req)
    return pay_order


