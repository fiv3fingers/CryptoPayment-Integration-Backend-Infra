# models/schemas/product.py
from pydantic import Field, UUID4
from typing import Optional, Dict 

from .base import MetadataModel

class ProductBase(MetadataModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    value_usd: float = Field(..., gt=0)
    metadata: Dict = Field(default_factory=dict)

class Product(ProductBase):
    id: str


class ProductUpdate(ProductBase):
    pass

