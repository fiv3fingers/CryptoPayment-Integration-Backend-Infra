# services/order.py
from uuid import UUID
from typing import Optional, List
from datetime import datetime, timedelta
import pytz
from sqlalchemy import select
from models.database_models import Order, OrderItem, Product
from models.schemas.order import OrderCreate, OrderUpdate, OrderStatus, OrderResponse
from fastapi import HTTPException
import logging

from services.base import BaseService

logger = logging.getLogger(__name__)

class OrderService(BaseService[Order]):
    async def create(self, organization_id: UUID, data: OrderCreate) -> OrderResponse:
        expires_at = datetime.now(pytz.UTC) + timedelta(hours=1)
        logger.info(f"Creating order for organization {organization_id} with expiration at {expires_at}")
        
        order = Order(
            organization_id=organization_id,
            status=OrderStatus.PENDING,
            expires_at=expires_at,
            total_value_usd=0,
            extra_data=data.extra_data
        )
        
        total_value = 0
        order_items = []
        
        # Process order items
        for item_data in data.order_items:
            product = self.db.query(Product).get(item_data.product_id)
            if not product:
                raise HTTPException(
                    status_code=404,
                    detail=f"Product {item_data.product_id} not found"
                )
            
            if product.organization_id != organization_id:
                raise HTTPException(
                    status_code=403,
                    detail="Product does not belong to organization"
                )
            
            total_price = product.value_usd * item_data.quantity
            order_item = OrderItem(
                product_id=product.id,
                quantity=item_data.quantity,
                unit_price_usd=product.value_usd,
                total_price_usd=total_price
            )
            total_value += total_price
            order_items.append(order_item)
        
        order.total_value_usd = total_value
        order.order_items = order_items
        
        return await self._handle_db_operation(
            lambda: self.db.add(order) or order
        )

    async def get_by_id(self, order_id: UUID, organization_id: UUID) -> Optional[Order]:
        return self.db.query(Order).filter(
            Order.id == order_id,
            Order.organization_id == organization_id
        ).first()

    async def update(self, organization_id: UUID, order_id: UUID, data: OrderUpdate) -> Order:
        """Update an order with new items and recalculate totals."""
        order = await self.get_by_id(order_id, organization_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        if order.status != OrderStatus.PENDING:
            raise HTTPException(status_code=400, detail="Order is not in pending state")

        if data.extra_data is not None:
            order.extra_data = data.extra_data

        if data.items is not None:
            # Remove existing items
            for item in order.order_items:
                self.db.delete(item)
            
            # Reset total value
            order.total_value_usd = 0
            
            # Add new items
            new_items = []
            for item_data in data.items:
                product = self.db.query(Product).get(item_data.product_id)
                if not product:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Product {item_data.product_id} not found"
                    )
                
                if product.organization_id != organization_id:
                    raise HTTPException(
                        status_code=403,
                        detail="Product does not belong to organization"
                    )
                
                total_price = product.value_usd * item_data.quantity
                order_item = OrderItem(
                    order_id=order.id,
                    product_id=product.id,
                    quantity=item_data.quantity,
                    unit_price_usd=product.value_usd,
                    total_price_usd=total_price
                )
                order.total_value_usd += total_price
                new_items.append(order_item)
            
            order.order_items = new_items

        return await self._handle_db_operation(lambda: order)
