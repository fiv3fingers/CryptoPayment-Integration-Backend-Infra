from models.schemas.order import OrderType
from sqlalchemy import (
    Column, Integer, String, ForeignKey, Float, 
    DateTime, BigInteger, Enum as SQLEnum, Text, func
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from enum import Enum
import uuid


Base = declarative_base()


class TimestampMixin:
    """Mixin for adding timestamp fields to models"""
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

class PaymentStatus(str, Enum):
    PENDING = "pending"
    FIXED = "fixed" # Payment amounts are fixed
    SUBMITTED = "submitted"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"
    REFUNDED = "refunded"

class OrderStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"
    REFUNDED = "refunded"

class OrderType(str, Enum):
    SALE = "sale", # product or item sale
    CHOOSE_AMOUNT = "choose_amount", # let the user specify the amount to pay, e.g. donation or when depositing into a wallet

class RoutingServiceType(int, Enum):
    OTHER = 0
    CHANGENOW = 1
    UNISWAP = 2


class SettlementCurrency:
    """Class representing a settlement currency"""
    def __init__(self, token: str, chain: str, address: str):
        self.token = token
        self.chain = chain
        self.address = address

    def to_dict(self):
        return {
            'token': self.token,
            'chain': self.chain,
            'address': self.address
        }

    @staticmethod
    def from_dict(data: dict):
        return SettlementCurrency(data['token'], data['chain'], data['address'])


class User(Base, TimestampMixin):
    """ User model representing users of the system """
    __tablename__ = 'users'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    api_key = Column(String(64), nullable=False, unique=True, index=True)
    api_secret = Column(String(128), nullable=False)

    # Relationships
    #organizations = relationship("Organization", back_populates="owner", cascade="all, delete-orphan")
    #memberships = relationship("OrganizationMember", back_populates="user", cascade="all, delete-orphan")


class Organization(Base, TimestampMixin):
    """Organization model representing merchants using the payment system"""
    __tablename__ = 'organizations'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    api_key = Column(String(64), nullable=False, unique=True, index=True)
    api_secret = Column(String(128), nullable=False)

    owner_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    settlement_currencies = Column(JSONB, nullable=False)


    # Relationships
    #owner = relationship("User", back_populates="organizations")
    #members = relationship("OrganizationMember", back_populates="organization", cascade="all, delete-orphan")
    #products = relationship("Product", back_populates="organization", cascade="all, delete-orphan")


class OrganizationMember(Base, TimestampMixin):
    """Organization member model representing users within an organization"""
    __tablename__ = 'organization_members'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    
    # Relationships
    #organization = relationship("Organization", back_populates="members")
    #user = relationship("User", back_populates="organizations")
    

class Product(Base, TimestampMixin):
    """Product model representing items that can be purchased"""
    __tablename__ = 'products'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # the organization the product belongs to
    organization_id = Column(UUID(as_uuid=True), ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False)

    name = Column(String(255), nullable=False)
    description = Column(Text)
    value_usd = Column(Float, nullable=False)
    metadata = Column(JSONB, nullable=False, default={})
    
    # Relationships
    #organization = relationship("Organization", back_populates="products")
    order_items = relationship("OrderItem", back_populates="product", cascade="all, delete-orphan")
    

class Order(Base, TimestampMixin):
    """Order model representing a collection of products being purchased"""
    __tablename__ = 'orders'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type = Column(SQLEnum(OrderType), nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False)
    status = Column(SQLEnum(OrderStatus), nullable=False, default=OrderStatus.PENDING)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    total_value_usd = Column(Float, nullable=False)
    metadata = Column(JSONB, nullable=False, default={})
    
    # Relationships
    order_items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    

class OrderItem(Base, TimestampMixin):
    """Order item model representing individual products in an order"""
    __tablename__ = 'order_items'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey('orders.id', ondelete='CASCADE'), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey('products.id'), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price_usd = Column(Float, nullable=False)
    total_price_usd = Column(Float, nullable=False)
    
    # Relationships
    order = relationship("Order", back_populates="order_items")
    product = relationship("Product", back_populates="order_items")


class Payment(Base, TimestampMixin):
    """Payment model representing cryptocurrency payments"""
    __tablename__ = 'payments'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey('orders.id', ondelete='CASCADE'), nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False)
    
    # Input payment details
    in_value_usd = Column(Float, nullable=False)
    in_amount = Column(String, nullable=False)  # Store as string to preserve precision
    in_token = Column(String, nullable=False)
    in_chain = Column(String, nullable=False)
    in_address = Column(String, nullable=False)
    
    # Output payment details
    out_value_usd = Column(Float, nullable=False)
    out_amount = Column(BigInteger, nullable=False)  # Store as string to preserve precision
    out_token = Column(String, nullable=False)
    out_chain = Column(String, nullable=False)
    out_address = Column(String, nullable=False)
    
    # External service details
    routing_service = Column(SQLEnum(RoutingServiceType), nullable=True)
    routing_reference = Column(String, nullable=True)

    expires_at = Column(DateTime(timezone=True), nullable=False)
    status = Column(SQLEnum(PaymentStatus), nullable=False, default=PaymentStatus.PENDING)

    metadata = Column(JSONB, nullable=False, default={})
