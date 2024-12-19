# routes/order.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List
from database.dependencies import get_db, get_current_organization
from services.order import OrderService
from models.schemas.order import (
    OrderCreate,
    OrderUpdate,
    OrderResponse,
)
from models.database_models import Organization

router = APIRouter(prefix="/orders", tags=["orders"])

@router.post("/", response_model=OrderResponse)
async def create_order(
    data: OrderCreate,
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    """Create a new order."""
    service = OrderService(db)
    return await service.create(org.id, data)


@router.put("/{order_id}", response_model=OrderResponse)
async def update_order(
    order_id: UUID,
    data: OrderUpdate,
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    """Update an existing order."""
    service = OrderService(db)
    return await service.update(org.id, order_id, data)



@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: UUID,
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    """Get a specific order by ID."""
    service = OrderService(db)
    order = await service.get_by_id(order_id, org.id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


