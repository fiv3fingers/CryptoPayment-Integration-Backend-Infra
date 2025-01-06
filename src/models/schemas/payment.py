# models/schemas/payment.py
from src.models.database_models import PaymentStatus, RoutingServiceType
from src.utils.currencies.types import Currency
from .base import TimestampModel, MetadataModel
from pydantic import BaseModel, Field, UUID4
from typing import Optional, Dict
from datetime import datetime


class PaymentCreate(BaseModel):
    currency_id: str
    refund_address: str

class PaymentResponse(BaseModel):
    order_id: str
    value_usd: float = Field(gt=0)
    currency: Currency
    amount: float  # Keep as string to preserve precision
    address: str
    expires_at: datetime
