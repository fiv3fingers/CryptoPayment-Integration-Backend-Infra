# services/product.py
from uuid import UUID
from typing import Optional, List
from models.database_models import Product
from models.schemas.product import ProductUpdate, ProductBase
from fastapi import HTTPException
import logging

from services.base import BaseService

logger = logging.getLogger(__name__)

class ProductService(BaseService[Product]):
    async def create(self, organization_id: UUID, data: List[ProductBase]) -> List[Product]:
        results = []
        for product_data in data:
            product = Product(
                organization_id=organization_id,
                name=product_data.name,
                description=product_data.description,
                value_usd=product_data.value_usd,
                metadata_=product_data.metadata
            )

            results.append(
                await self._handle_db_operation( lambda: self.db.add(product) or product)
            )

        return results

        
    async def update(self, organization_id: UUID, product_id: UUID, data: ProductUpdate) -> Product:
        product = await self.get_by_id(product_id, organization_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        update_data = data.to_orm_dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(product, field, value)

        return await self._handle_db_operation(lambda: product)

    async def get_by_id(self, product_id: UUID, organization_id: UUID) -> Optional[Product]:
        return self.db.query(Product).filter(
            Product.id == product_id,
            Product.organization_id == organization_id
        ).first()

    async def list_by_organization(
        self, 
        organization_id: UUID, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Product]:
        return self.db.query(Product)\
            .filter(Product.organization_id == organization_id)\
            .offset(skip)\
            .limit(limit)\
            .all()

    async def delete(self, organization_id: UUID, product_id: UUID) -> bool:
        product = await self.get_by_id(product_id, organization_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        return await self._handle_db_operation(
            lambda: self.db.delete(product) or True
        )


