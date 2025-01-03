# models/schemas/payment.py
from models.database_models import PaymentStatus, RoutingServiceType
from .base import TimestampModel, MetadataModel
from pydantic import BaseModel, Field, UUID4
from typing import Optional, Dict
from datetime import datetime


class PaymentCreate(BaseModel):
    currency_id: str
    refund_address: str

class PaymentResponse(BaseModel):
    order_id: str
    in_value_usd: float = Field(gt=0)
    in_amount: str  # Keep as string to preserve precision
    in_address: str
    in_token: str
    expires_at: datetime
    

    @classmethod
    def from_orm(cls, obj):
        return cls(
            order_id=obj.order_id,
            in_value_usd=obj.in_value_usd,
            in_amount=f"{obj.in_amount}",
            in_address=obj.in_address,
            in_token=obj.in_token,
            expires_at=obj.expires_at
        )
