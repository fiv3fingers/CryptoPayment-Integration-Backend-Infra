# models/schemas/product.py
from .base import TimestampModel
from pydantic import BaseModel, Field, UUID4
from typing import Optional, Dict

class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    value_usd: float = Field(..., gt=0)
    extra_data: Dict = Field(default_factory=dict)

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    value_usd: Optional[float] = Field(None, gt=0)
    extra_data: Optional[Dict] = None

class ProductResponse(ProductBase, TimestampModel):
    id: UUID4
    user_id: UUID4

    class Config:
        orm_mode = True


