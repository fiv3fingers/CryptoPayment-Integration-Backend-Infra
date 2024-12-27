# services/payment.py
from uuid import UUID
from models.database_models import Payment, Order
from models.schemas.payment import PaymentCreate
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

