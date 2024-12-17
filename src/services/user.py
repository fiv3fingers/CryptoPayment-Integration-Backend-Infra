# services/user.py
from uuid import UUID
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException
from models.database_models import User
from models.schemas.user import UserCreate, UserUpdate
import secrets
import hashlib
import logging

from services.base import BaseService

logger = logging.getLogger(__name__)

class UserService(BaseService[User]):
    def _generate_api_credentials(self) -> tuple[str, str]:
        """Generate secure API key and secret."""
        api_key = secrets.token_urlsafe(32)
        api_secret = secrets.token_urlsafe(64)
        return api_key, api_secret

    def _hash_secret(self, secret: str) -> str:
        """Hash the API secret for storage."""
        return hashlib.sha256(secret.encode()).hexdigest()

    async def create(self, data: UserCreate) -> tuple[User, str]:
        """Create a new user with API credentials."""
        # Generate API credentials
        api_key, api_secret = self._generate_api_credentials()
        
        # Create user with hashed secret
        user = User(
            api_key=api_key,
            api_secret=self._hash_secret(api_secret),
            settlement_currencies=[
                currency.model_dump() for currency in data.settlement_currencies
            ]
        )
        
        try:
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            # Return both user and unhashed secret
            return user, api_secret
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating user: {str(e)}")
            raise HTTPException(status_code=400, detail="Error creating user")

    async def update(self, user_id: UUID, data: UserUpdate) -> User:
        """Update user settings."""
        user = self.db.query(User).get(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if data.settlement_currencies:
            user.settlement_currencies = [
                currency.model_dump() for currency in data.settlement_currencies
            ]
        
        try:
            self.db.commit()
            self.db.refresh(user)
            return user
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating user: {str(e)}")
            raise HTTPException(status_code=400, detail="Error updating user")

    async def rotate_api_key(self, user_id: UUID) -> tuple[str, str]:
        """Generate new API credentials for user."""
        user = self.db.query(User).get(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        api_key, api_secret = self._generate_api_credentials()
        
        user.api_key = api_key
        user.api_secret = self._hash_secret(api_secret)
        
        try:
            self.db.commit()
            return api_key, api_secret
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error rotating API key: {str(e)}")
            raise HTTPException(status_code=400, detail="Error rotating API key")


