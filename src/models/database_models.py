from typing import NamedTuple
from .enums import OrderType, OrderStatus, PaymentStatus, RoutingServiceType
from sqlalchemy import (
    ARRAY, Column, Integer, String, ForeignKey, Float, 
    DateTime, BigInteger, Enum as SQLEnum, Text, func
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
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
            address=data["address"]
        )



class TimestampMixin:
    """Mixin for adding timestamp fields to models"""
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

class User(Base, TimestampMixin):
    """User model representing users of the system"""
    __tablename__ = 'User'
    
    id = Column(String, primary_key=True, default=cuid2.cuid_wrapper())
    name = Column(String(255), nullable=True)
    email = Column(String, nullable=True, unique=True)
    email_verified = Column(DateTime, nullable=True)
    image = Column(String, nullable=True)
    wallet_address = Column(String(255), nullable=True)

    # Relationships
    accounts = relationship("Account", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    owned_organizations = relationship("Organization", back_populates="owner")
    organization_memberships = relationship("OrganizationMember", back_populates="user")

class Account(Base, TimestampMixin):
    """Account model for authentication providers"""
    __tablename__ = 'Account'
    
    id = Column(String, primary_key=True, default=cuid2.cuid_wrapper())
    user_id = Column(String, ForeignKey('User.id', ondelete='CASCADE'), nullable=False)
    type = Column(String, nullable=False)
    provider = Column(String, nullable=False)
    provider_account_id = Column(String, nullable=False)
    refresh_token = Column(String, nullable=True)
    access_token = Column(String, nullable=True)
    expires_at = Column(Integer, nullable=True)
    token_type = Column(String, nullable=True)
    scope = Column(String, nullable=True)
    id_token = Column(String, nullable=True)
    session_state = Column(String, nullable=True)

    # Relationships
    user = relationship("User", back_populates="accounts")


class Session(Base, TimestampMixin):
    """Session model for user sessions"""
    __tablename__ = 'Session'
    
    session_token = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey('User.id', ondelete='CASCADE'), nullable=False)
    expires = Column(DateTime, nullable=False)

    # Relationships
    user = relationship("User", back_populates="sessions")


class Organization(Base, TimestampMixin):
    """Organization model representing merchants using the payment system"""
    __tablename__ = 'Organization'
    
    id = Column(String, primary_key=True, default=cuid2.cuid_wrapper())
    name = Column(String(255), nullable=False)
    
    api_key = Column(String(64), nullable=False, unique=True, index=True)

    owner_id = Column(String, ForeignKey('User.id', ondelete='CASCADE'), nullable=False)
    settlement_currencies = Column(ARRAY(JSONB), nullable=False)   # list of currency ids

    # Relationships
    owner = relationship("User", back_populates="owned_organizations")
    members = relationship("OrganizationMember", back_populates="organization", cascade="all, delete-orphan")
    #products = relationship("Product", back_populates="organization", cascade="all, delete-orphan")


class OrganizationMember(Base, TimestampMixin):
    """Organization member model representing users within an organization"""
    __tablename__ = 'OrganizationMember'
    
    id = Column(String, primary_key=True, default=cuid2.cuid_wrapper())
    organization_id = Column(String, ForeignKey('Organization.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(String, ForeignKey('User.id', ondelete='CASCADE'), nullable=False)
    
    # Relationships
    organization = relationship("Organization", back_populates="members")
    user = relationship("User", back_populates="organization_memberships")
    

class Order(Base, TimestampMixin):
    """Order model representing a collection of products being purchased"""
    __tablename__ = 'Order'
    
    id = Column(String, primary_key=True, default=cuid2.cuid_wrapper())
    type = Column(SQLEnum(OrderType), nullable=False)
    organization_id = Column(String, ForeignKey('Organization.id', ondelete='CASCADE'), nullable=False)    
    status = Column(SQLEnum(OrderStatus), nullable=False, default=OrderStatus.PENDING)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    total_value_usd = Column(Float, nullable=False)
    metadata_ = Column(JSONB, nullable=False, default={}, name="metadata")
    
    # Relationships
    order_items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    

class OrderItem(Base, TimestampMixin):
    """Order item model representing individual products in an order"""
    __tablename__ = 'OrderItem'
    
    id = Column(String, primary_key=True, default=cuid2.cuid_wrapper())
    order_id = Column(String, ForeignKey('Order.id', ondelete='CASCADE'), nullable=False)
    product_id = Column(String, ForeignKey('Product.id'), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price_usd = Column(Float, nullable=False)
    total_price_usd = Column(Float, nullable=False)
    
    # Relationships
    order = relationship("Order", back_populates="order_items")
    product = relationship("Product", back_populates="order_items")


class Payment(Base, TimestampMixin):
    """Payment model representing cryptocurrency payments"""
    __tablename__ = 'Payment'
    
    id = Column(String, primary_key=True, default=cuid2.cuid_wrapper())
    order_id = Column(String, ForeignKey('Order.id', ondelete='CASCADE'), nullable=False)
    organization_id = Column(String, ForeignKey('Organization.id', ondelete='CASCADE'), nullable=False)

    refund_address = Column(String, nullable=False)
    
    # Input payment details
    in_value_usd = Column(Float, nullable=False)
    in_amount = Column(Float, nullable=False) 
    in_currency = Column(String, nullable=False)
    in_address = Column(String, nullable=False)
    
    # Output payment details
    out_value_usd = Column(Float, nullable=False)
    out_amount = Column(Float, nullable=False)
    out_currency = Column(String, nullable=False)
    out_address = Column(String, nullable=False)
    
    # External service details
    routing_service = Column(SQLEnum(RoutingServiceType), nullable=True)
    routing_reference = Column(String, nullable=True)

    expires_at = Column(DateTime(timezone=True), nullable=False)
    status = Column(SQLEnum(PaymentStatus), nullable=False, default=PaymentStatus.PENDING)

    metadata_ = Column(JSONB, nullable=False, default={}, name="metadata")


class Product(Base, TimestampMixin):
    """Product model representing items that can be purchased"""
    __tablename__ = 'Product'
    
    id = Column(String, primary_key=True, default=cuid2.cuid_wrapper())
    name = Column(String(255), nullable=False)
    description = Column(Text)

    # the organization the product belongs to
    organization_id = Column(String, ForeignKey('Organization.id', ondelete='CASCADE'), nullable=False)
    
    value_usd = Column(Float, nullable=False)
    metadata_ = Column(JSONB, nullable=False, default={}, name="metadata")

    # Relationships
    #organization = relationship("Organization", back_populates="product")
    order_items = relationship("OrderItem", back_populates="product", cascade="all, delete-orphan")
    
