# services/order.py
from typing import Optional, List
from datetime import datetime, timedelta
import pytz
from src.models.database_models import Order, OrderItem, Product, Organization, SettlementCurrency
from src.models.schemas.order import OrderCreate, OrderUpdate, OrderResponse
from src.models.database_models import OrderStatus
from fastapi import HTTPException
import logging

from .base import BaseService

from src.services.organization import OrganizationService

logger = logging.getLogger(__name__)

class OrderService(BaseService[Order]):
    async def create(self, organization_id: str, data: OrderCreate) -> OrderResponse:
        expires_at = datetime.now(pytz.UTC) + timedelta(hours=1)
        logger.info(f"Creating order for organization {organization_id} with expiration at {expires_at}")
               
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
        
        order = Order(
            organization_id=organization_id,
            type=data.type,
            expires_at=expires_at,
            metadata_=data.metadata,
            total_value_usd=total_value,
            order_items=order_items
        )
        
        return await self._handle_db_operation(
            lambda: self.db.add(order) or order
        )

    async def get_by_id(self, order_id: str, organization_id: str) -> Optional[Order]:
        return self.db.query(Order).filter(
            Order.id == order_id,
            Order.organization_id == organization_id
        ).first()

    async def update(self, organization_id: str, order_id: str, data: OrderUpdate) -> Order:
        """Update an order with new items and recalculate totals."""
        order = await self.get_by_id(order_id, organization_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        if order.status != OrderStatus.PENDING:
            raise HTTPException(status_code=400, detail="Order is not in pending state")

        if data.metadata is not None:
            order.metadata_ = data.metadata

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


    async def get_settlement_currencies(self, order_id: str) -> List[SettlementCurrency]:
        """Get the list of settlement currencies for an order."""
        order = self.db.query(Order).get(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        organization = self.db.query(Organization).get(order.organization_id)
        if not organization:
            raise HTTPException(status_code=404, detail="Organization not found")

        return await OrganizationService(self.db).get_settlement_currencies(organization.id)




