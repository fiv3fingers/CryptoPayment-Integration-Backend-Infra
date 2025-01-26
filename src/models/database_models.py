from typing import NamedTuple
from .enums import PayOrderStatus, PayOrderMode, RoutingServiceType
from sqlalchemy import (
    ARRAY,
    Column,
    String,
    ForeignKey,
    Float,
    NUMERIC,
    DateTime,
    Enum as SQLEnum,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
import cuid2


Base = declarative_base()


class SettlementCurrency(NamedTuple):
    """Settlement currency model for Organization model"""

    currency_id: str
    address: str

    def to_dict(self):
        return {"currency_id": self.currency_id, "address": self.address}

    @classmethod
    def from_dict(cls, data):
        return cls(currency_id=data["currency_id"], address=data["address"])


class TimestampMixin:
    """Mixin for adding timestamp fields to models"""

    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class Organization(Base, TimestampMixin):
    """Organization model representing merchants using the payment system"""

    __tablename__ = "Organization"

    id = Column(String, primary_key=True, default=cuid2.cuid_wrapper())
    name = Column(String(255), nullable=False)

    api_key = Column(String(64), nullable=False, unique=True, index=True)
    api_secret = Column(String(64), nullable=False)

    owner_id = Column(String, nullable=False)
    settlement_currencies = Column(ARRAY(JSONB), nullable=False)


class PayOrder(TimestampMixin, Base):
    """PayOrder model"""

    __tablename__ = "PayOrder"

    id = Column(String, primary_key=True, default=cuid2.cuid_wrapper())
    organization_id = Column(
        String, ForeignKey("Organization.id", ondelete="CASCADE"), nullable=False
    )

    mode = Column(SQLEnum(PayOrderMode), nullable=False)
    status = Column(
        SQLEnum(
            PayOrderStatus,
            values_callable=lambda obj: [e.value for e in obj],
            native_enum=False,
        ),
        default=PayOrderStatus.PENDING,
    )

    # Input payment details
    source_currency_id = Column(String, nullable=True)
    source_amount = Column(NUMERIC(78, 0), nullable=True)
    source_value_usd = Column(Float, nullable=True)
    source_transaction_hash = Column(String, nullable=True)
    source_deposit_address = Column(String, nullable=True)

    # Output payment details
    destination_currency_id = Column(String, nullable=True)
    destination_amount = Column(NUMERIC(78, 0), nullable=True)
    destination_receiving_address = Column(String, nullable=True)
    destination_value_usd = Column(Float, nullable=True)
    destination_transaction_hash = Column(String, nullable=True)

    refund_address = Column(String, nullable=True)

    # External service details
    routing_service = Column(SQLEnum(RoutingServiceType), nullable=True)
    routing_reference = Column(String, nullable=True)

    expires_at = Column(DateTime(timezone=True), nullable=True)

    metadata_ = Column(JSONB, nullable=False, default={}, name="metadata")
