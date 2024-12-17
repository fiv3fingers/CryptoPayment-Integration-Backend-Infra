from .base import TimestampModel
from pydantic import BaseModel, Field, UUID4, SecretStr
from typing import List, Dict, Optional
from uuid import UUID

class SettlementCurrencySchema(BaseModel):
    token: str 
    chain: str
    address: str

class UserBase(BaseModel):
    settlement_currencies: List[SettlementCurrencySchema]

class UserCreate(UserBase):
    api_key: SecretStr
    api_secret: SecretStr

class UserUpdate(BaseModel):
    settlement_currencies: Optional[List[SettlementCurrencySchema]] = None

class UserResponse(UserBase, TimestampModel):
    id: UUID4
    api_key: str  # Only show masked version in responses

    class Config:
        orm_mode = True


# Add to models/schemas/user.py
class UserCredentialsResponse(BaseModel):
    """Response model for API credentials."""
    user_id: UUID
    api_key: str
    api_secret: str
    settlement_currencies: List[SettlementCurrencySchema]
