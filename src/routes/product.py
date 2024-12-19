# routes/product.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List
from database.dependencies import get_db, get_current_organization, get_current_user
from services.product import ProductService
from models.schemas.product import (
    Product,
    ProductBase,
    ProductUpdate,
)
from models.database_models import Organization, User

router = APIRouter(prefix="/products", tags=["products"])

@router.post("/", response_model=List[Product])
async def create_products(
    data: List[ProductBase],
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    """Create a new product for the authenticated organization."""
    service = ProductService(db)
    products = await service.create(org.id, data)
    return products


@router.put("/{product_id}", response_model=Product)
async def update_product(
    product_id: UUID,
    data: ProductUpdate,
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    """Update an existing product."""
    service = ProductService(db)
    return await service.update(org.id, product_id, data)

@router.get("/{product_id}", response_model=Product)
async def get_product(
    product_id: UUID,
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    """Get a specific product by ID."""
    service = ProductService(db)
    product = await service.get_by_id(product_id, org.id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.get("/", response_model=List[Product])
async def list_products(
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    """List all products for the authenticated organization."""
    service = ProductService(db)
    return await service.list_by_organization(
        org.id,
    )

@router.delete("/{product_id}")
async def delete_product(
    product_id: UUID,
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    """Delete a product."""
    service = ProductService(db)
    await service.delete(org.id, product_id)
    return {"status": "success"}

