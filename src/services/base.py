# services/base.py
from typing import Generic, TypeVar, Optional, List, Type
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
import logging

T = TypeVar('T')

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
            logger.error(f"Database integrity error: {str(e)}")
            raise HTTPException(status_code=400, detail="Database constraint violation")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Database operation error: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error")


