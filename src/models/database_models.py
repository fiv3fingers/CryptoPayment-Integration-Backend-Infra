from models.enums import OrderType, OrderStatus, PaymentStatus, RoutingServiceType
from sqlalchemy import (
    Column, Integer, String, ForeignKey, Float, 
    DateTime, BigInteger, Enum as SQLEnum, Text, func
)
from sqlalchemy.dialects.postgresql import JSONB, CUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import cuid


Base = declarative_base()


class TimestampMixin:
    """Mixin for adding timestamp fields to models"""
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

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
    __tablename__ = 'User'

    id = Column(CUID(as_cuid=True), primary_key=True, default=cuid.cuid)
    name = Column(String(255), nullable=True)
    email = Column(String, nullable=True, unique=True)
    wallet_address = Column(String(255), nullable=True)

    # Relationships
    #owner_of_organization = relationship("Organization", back_populates="owner", cascade="all, delete-orphan")
    #members_of_organization = relationship("OrganizationMember", back_populates="user", cascade="all, delete-orphan")


class Organization(Base, TimestampMixin):
    """Organization model representing merchants using the payment system"""
    __tablename__ = 'Organization'
    
    id = Column(CUID(as_cuid=True), primary_key=True, default=cuid.cuid)
    name = Column(String(255), nullable=False)
    
    api_key = Column(String(64), nullable=False, unique=True, index=True)
    api_secret = Column(String(128), nullable=False)

    owner_id = Column(CUID(as_cuid=True), ForeignKey('User.id', ondelete='CASCADE'), nullable=False)
    settlement_currencies = Column(JSONB, nullable=False)

    # Relationships
    #owner = relationship("User", back_populates="owner_of_organization")
    #members = relationship("OrganizationMember", back_populates="members_of_organization", cascade="all, delete-orphan")
    #products = relationship("Product", back_populates="organization", cascade="all, delete-orphan")


class OrganizationMember(Base, TimestampMixin):
    """Organization member model representing users within an organization"""
    __tablename__ = 'OrganizationMember'
    
    id = Column(CUID(as_cuid=True), primary_key=True, default=cuid.cuid)
    organization_id = Column(CUID(as_cuid=True), ForeignKey('Organization.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(CUID(as_cuid=True), ForeignKey('User.id', ondelete='CASCADE'), nullable=False)
    
    # Relationships
    organization = relationship("Organization", back_populates="members")
    #user = relationship("User", back_populates="organizations")
    

class Order(Base, TimestampMixin):
    """Order model representing a collection of products being purchased"""
    __tablename__ = 'Order'
    
    id = Column(CUID(as_cuid=True), primary_key=True, default=cuid.cuid)
    type = Column(SQLEnum(OrderType), nullable=False)
    organization_id = Column(CUID(as_cuid=True), ForeignKey('Organization.id', ondelete='CASCADE'), nullable=False)    
    status = Column(SQLEnum(OrderStatus), nullable=False, default=OrderStatus.PENDING)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    total_value_usd = Column(Float, nullable=False)
    metadata_ = Column(JSONB, nullable=False, default={}, name="metadata")
    
    # Relationships
    order_items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    

class OrderItem(Base, TimestampMixin):
    """Order item model representing individual products in an order"""
    __tablename__ = 'OrderItem'
    
    id = Column(CUID(as_cuid=True), primary_key=True, default=cuid.cuid)
    order_id = Column(CUID(as_cuid=True), ForeignKey('Order.id', ondelete='CASCADE'), nullable=False)
    product_id = Column(CUID(as_cuid=True), ForeignKey('Product.id'), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price_usd = Column(Float, nullable=False)
    total_price_usd = Column(Float, nullable=False)
    
    # Relationships
    order = relationship("Order", back_populates="order_items")
    product = relationship("Product", back_populates="order_items")


class Payment(Base, TimestampMixin):
    """Payment model representing cryptocurrency payments"""
    __tablename__ = 'Payment'
    
    id = Column(CUID(as_cuid=True), primary_key=True, default=cuid.cuid)
    order_id = Column(CUID(as_cuid=True), ForeignKey('Order.id', ondelete='CASCADE'), nullable=False)
    organization_id = Column(CUID(as_cuid=True), ForeignKey('Organization.id', ondelete='CASCADE'), nullable=False)
    
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

    metadata_ = Column(JSONB, nullable=False, default={}, name="metadata")


class Product(Base, TimestampMixin):
    """Product model representing items that can be purchased"""
    __tablename__ = 'Product'
    
    id = Column(CUID(as_cuid=True), primary_key=True, default=cuid.cuid)
    name = Column(String(255), nullable=False)
    description = Column(Text)

    # the organization the product belongs to
    organization_id = Column(CUID(as_cuid=True), ForeignKey('Organization.id', ondelete='CASCADE'), nullable=False)
    
    value_usd = Column(Float, nullable=False)
    metadata_ = Column(JSONB, nullable=False, default={}, name="metadata")

    # Relationships
    #organization = relationship("Organization", back_populates="product")
    order_items = relationship("OrderItem", back_populates="product", cascade="all, delete-orphan")
    