# services/base.py
from typing import Generic, TypeVar
import logging
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException

T = TypeVar("T")

logger = logging.getLogger(__name__)


class BaseService(Generic[T]):
    def __init__(self, db: Session):
        self.db = db

    async def _handle_db_operation(self, operation):
        try:
            result = operation()
            self.db.commit()
            return result
        except IntegrityError as e:
            self.db.rollback()
            logger.error("Database integrity error: %s", str(e))
            raise HTTPException(
                status_code=400, detail="Database constraint violation"
            ) from e
        except Exception as e:
            self.db.rollback()
            logger.error("Database operation error: %s", str(e))
            raise HTTPException(status_code=500, detail="Internal server error") from e
