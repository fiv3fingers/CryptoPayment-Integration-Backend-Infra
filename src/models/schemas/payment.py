# models/schemas/payment.py
from .base import TimestampModel
from pydantic import BaseModel, Field, UUID4
from typing import Optional, Dict, List
from datetime import datetime
from enum import Enum

class PaymentStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"
    REFUNDED = "refunded"

class RoutingServiceType(int, Enum):
    OTHER = 0
    CHANGENOW = 1
    UNISWAP = 2



class PaymentBase(BaseModel):
    order_id: UUID4
    in_token: str
    in_chain: str

class PaymentCreate(PaymentBase):
    pass

class PaymentResponse(PaymentBase, TimestampModel):
    id: UUID4
    order_id: UUID4
    in_value_usd: float = Field(gt=0)
    in_amount: str  # Keep as string to preserve precision
    in_address: str
    
    out_value_usd: float = Field(gt=0)
    out_amount: str  # Keep as string to preserve precision
    out_token: str 
    out_chain: str
    out_address: str
    
    routing_service: Optional[RoutingServiceType]
    routing_reference: Optional[str]
    
    expires_at: datetime
    status: PaymentStatus
    extra_data: Dict = Field(default_factory=dict)

    class Config:
        orm_mode = True

