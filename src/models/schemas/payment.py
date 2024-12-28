# models/schemas/payment.py
from models.database_models import PaymentStatus, RoutingServiceType
from .base import TimestampModel, MetadataModel
from pydantic import BaseModel, Field, UUID4
from typing import Optional, Dict
from datetime import datetime

class PaymentBase(BaseModel):
    order_id: UUID4
    in_token: str
    in_chain: str

class PaymentCreate(PaymentBase):
    pass

class PaymentResponse(PaymentBase, MetadataModel, TimestampModel):
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
    metadata: Dict = Field(default_factory=dict)

