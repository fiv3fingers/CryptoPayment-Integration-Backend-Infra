from .base import TimestampModel
from pydantic import BaseModel, Field, UUID4, SecretStr
from typing import List, Dict, Optional
from uuid import UUID


class UserCreate(BaseModel):
    pass

class UserResponse(TimestampModel):
    id: str
    name: str
    email: Optional[str]
    email_verified: Optional[str]
    image: Optional[str]
    wallet_address: Optional[str]


class UserCredentialsResponse(BaseModel):
    """Response model for API credentials."""
    id: str
    api_key: str #SecretStr
    api_secret: str #SecretStr
