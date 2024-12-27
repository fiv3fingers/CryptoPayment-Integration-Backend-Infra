# models/schemas/order.py
from models.database_models import OrderStatus, OrderType
from .base import TimestampModel
from pydantic import BaseModel, Field, UUID4
from typing import List, Dict, Optional
from datetime import datetime
from enum import Enum

class OrderItemBase(BaseModel):
    product_id: UUID4
    quantity: int = Field(gt=0)

class OrderItem(OrderItemBase):
    pass

class OrderItemResponse(OrderItemBase, TimestampModel):
    id: UUID4
    order_id: UUID4
    unit_price_usd: float = Field(gt=0)
    total_price_usd: float = Field(gt=0)

    class Config:
        orm_mode = True



class OrderBase(BaseModel):
    type: OrderType
    metadata: Dict = Field(default_factory=dict)

class OrderCreate(OrderBase):
    order_items: List[OrderItem]

class OrderUpdate(BaseModel):
    order_items: Optional[List[OrderItem]] = None
    metadata: Optional[Dict] = None

class OrderResponse(OrderBase, TimestampModel):
    id: UUID4
    organization_id: UUID4
    status: OrderStatus
    expires_at: datetime
    total_value_usd: float = Field(gt=0)
    order_items: List[OrderItemResponse]

    class Config:
        orm_mode = True


