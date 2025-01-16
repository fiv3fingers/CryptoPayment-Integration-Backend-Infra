from typing import NamedTuple
from .enums import PayOrderStatus, PayOrderMode, RoutingServiceType
from sqlalchemy import (
    ARRAY, Column, String, ForeignKey, Float, 
    DateTime, Enum as SQLEnum, func
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
import cuid2


Base = declarative_base()

class SettlementCurrency(NamedTuple):
    currency_id: str
    address: str

    def to_dict(self):
        return {
            "currency_id": self.currency_id,
            "address": self.address
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            currency_id=data["currency_id"],
            address=data["address"] # TODO: Change to settlement_address
        )



class TimestampMixin:
    """Mixin for adding timestamp fields to models"""
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

class Organization(Base, TimestampMixin):
    """Organization model representing merchants using the payment system"""
    __tablename__ = 'Organization'
    
    id = Column(String, primary_key=True, default=cuid2.cuid_wrapper())
    name = Column(String(255), nullable=False)
    
    api_key = Column(String(64), nullable=False, unique=True, index=True)

    owner_id = Column(String, nullable=False)
    settlement_currencies = Column(ARRAY(JSONB), nullable=False)   # list of currency ids

class PayOrder(Base):
    """ PayOrder model """
    __tablename__ = 'PayOrder'

    id = Column(String, primary_key=True, default=cuid2.cuid_wrapper())
    organization_id = Column(String, ForeignKey('Organization.id', ondelete='CASCADE'), nullable=False)

    mode = Column(SQLEnum(PayOrderMode), nullable=False)
    status = Column(
        SQLEnum(
                PayOrderStatus,
                values_callable=lambda obj: [e.value for e in obj],
                native_enum=False
            ),
        default=PayOrderStatus.PENDING)

    # Input payment details
    in_currency_id = Column(String, nullable=True)
    in_amount = Column(Float, nullable=True) 
    in_address = Column(String, nullable=True)
    in_value_usd = Column(Float, nullable=True)
    
    # Output payment details
    out_currency_id = Column(String, nullable=True)
    out_amount = Column(Float, nullable=True)
    out_address = Column(String, nullable=True)
    out_value_usd = Column(Float, nullable=True)

    refund_address = Column(String, nullable=True)
    
    # External service details
    routing_service = Column(SQLEnum(RoutingServiceType), nullable=True)
    routing_reference = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)

    metadata_ = Column(JSONB, nullable=False, default={}, name="metadata")

