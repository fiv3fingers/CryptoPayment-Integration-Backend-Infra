# services/payment.py
from uuid import UUID
from typing import Optional, List
from datetime import datetime, timedelta
import pytz
from sqlalchemy import select
from models.database_models import Payment, Order, PaymentStatus, RoutingServiceType
from models.schemas.payment import PaymentCreate, PaymentQuoteRequest
from fastapi import HTTPException
import logging

from services.base import BaseService

logger = logging.getLogger(__name__)

class PaymentService(BaseService[Payment]):
    async def create_payment(
        self, 
        user_id: UUID, 
        order_id: UUID, 
        data: PaymentCreate
    ) -> Payment:
        # TODO
        order = self.db.query(Order).filter(
            Order.id == order_id,
            Order.user_id == user_id
        ).first()

