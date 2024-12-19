from .base import TimestampModel
from pydantic import BaseModel, Field, UUID4, SecretStr
from typing import List, Dict, Optional
from uuid import UUID

class UserBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)

class UserCreate(UserBase):
    pass

class UserResponse(UserBase, TimestampModel):
    id: UUID4
    api_key: str #SecretStr
    api_secret: str #SecretStr

class UserCredentialsResponse(BaseModel):
    """Response model for API credentials."""
    id: UUID
    api_key: str #SecretStr
    api_secret: str #SecretStr
