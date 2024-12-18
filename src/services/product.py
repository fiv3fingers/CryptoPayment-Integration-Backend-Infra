# services/product.py
from uuid import UUID
from typing import Optional, List
from sqlalchemy import select
from models.database_models import Product
from models.schemas.product import ProductUpdate, ProductBase
from fastapi import HTTPException
import logging

from services.base import BaseService

logger = logging.getLogger(__name__)

class ProductService(BaseService[Product]):
    async def create(self, user_id: UUID, data: List[ProductBase]) -> List[Product]:
        results = []
        for product_data in data:
            print(f"product_data: {product_data}")
            product = Product(
                user_id=user_id,
                name=product_data.name,
                description=product_data.description,
                value_usd=product_data.value_usd,
                extra_data=product_data.extra_data
            )
            print(f"product: {product}")

            results.append(
                await self._handle_db_operation( lambda: self.db.add(product) or product)
            )


        print(f"results: {results}")
        return results

        
    async def update(self, user_id: UUID, product_id: UUID, data: ProductUpdate) -> Product:
        product = await self.get_by_id(product_id, user_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(product, field, value)

        return await self._handle_db_operation(lambda: product)

    async def get_by_id(self, product_id: UUID, user_id: UUID) -> Optional[Product]:
        return self.db.query(Product).filter(
            Product.id == product_id,
            Product.user_id == user_id
        ).first()

    async def list_by_user(
        self, 
        user_id: UUID, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Product]:
        return self.db.query(Product)\
            .filter(Product.user_id == user_id)\
            .offset(skip)\
            .limit(limit)\
            .all()

    async def delete(self, user_id: UUID, product_id: UUID) -> bool:
        product = await self.get_by_id(product_id, user_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        return await self._handle_db_operation(
            lambda: self.db.delete(product) or True
        )


