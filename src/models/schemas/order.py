# models/schemas/order.py
from src.models.enums import OrderStatus, OrderType
from .base import TimestampModel, MetadataModel
from pydantic import BaseModel, Field, UUID4
from typing import List, Dict, Optional
from datetime import datetime

class OrderItemBase(BaseModel):
    product_id: str
    quantity: int = Field(gt=0)

class OrderItem(OrderItemBase):
    pass

class OrderItemResponse(OrderItemBase, TimestampModel):
    id: str
    order_id: str
    unit_price_usd: float = Field(gt=0)
    total_price_usd: float = Field(gt=0)


class OrderBase(MetadataModel):
    type: OrderType
    metadata: Dict = Field(default_factory=dict)


class OrderCreate(OrderBase):
    order_items: List[OrderItem]

class OrderUpdate(OrderBase):
    order_items: Optional[List[OrderItem]] = None

class OrderResponse(OrderBase, TimestampModel):
    id: str
    organization_id: str
    status: OrderStatus
    expires_at: datetime
    total_value_usd: float = Field(gt=0)
    order_items: List[OrderItemResponse]



