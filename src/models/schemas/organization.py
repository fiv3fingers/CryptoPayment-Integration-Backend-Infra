from .base import TimestampModel
from pydantic import BaseModel, Field, UUID4, SecretStr
from typing import List, Dict, Optional
from uuid import UUID
from datetime import datetime

class OrganizationBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    settlement_currencies: List[str]

class OrganizationCreate(OrganizationBase):
    pass

class OrganizationCreateResponse(OrganizationBase, TimestampModel):
    id: UUID4
    api_key: str
    owner_id: UUID4

class OrganizationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    settlement_currencies: Optional[List[str]] = None

class OrganizationCredentialsResponse(BaseModel):
    api_key: str
    api_secret: str

class MemberOperation(BaseModel):
    member_ids: List[UUID] = Field(..., min_items=1)

class MemberOperationResponse(BaseModel):
    successful_ids: List[UUID]
    failed_ids: List[UUID]
    message: str

class OrganizationMemberResponse(TimestampModel):
    id: UUID4
    organization_id: UUID4
    user_id: UUID4

    class Config:
        orm_mode = True

class OrganizationFullResponse(OrganizationCreateResponse):
    members: List[OrganizationMemberResponse] = []
