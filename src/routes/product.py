# routes/product.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List
from database.dependencies import get_db, get_current_user
from services.product import ProductService
from models.schemas.product import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
)
from models.database_models import User

router = APIRouter(prefix="/products", tags=["products"])

@router.post("/", response_model=ProductResponse)
async def create_product(
    data: ProductCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new product for the authenticated user."""
    service = ProductService(db)
    return await service.create(user.id, data)

@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: UUID,
    data: ProductUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an existing product."""
    service = ProductService(db)
    return await service.update(user.id, product_id, data)

@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific product by ID."""
    service = ProductService(db)
    product = await service.get_by_id(product_id, user.id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.get("/", response_model=List[ProductResponse])
async def list_products(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all products for the authenticated user."""
    service = ProductService(db)
    return await service.list_by_user(
        user.id,
        skip=(pagination.page - 1) * pagination.size,
        limit=pagination.size
    )

@router.delete("/{product_id}")
async def delete_product(
    product_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a product."""
    service = ProductService(db)
    await service.delete(user.id, product_id)
    return {"status": "success"}

