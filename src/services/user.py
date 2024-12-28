# services/user.py
from uuid import UUID
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException
from models.database_models import User
from models.schemas.user import UserCreate 
from utils.common import generate_api_credentials, hash_secret
import secrets
import hashlib
import logging





from services.base import BaseService

logger = logging.getLogger(__name__)

class UserService(BaseService[User]):
    async def create(self, data: UserCreate) -> tuple[User, str]:
        """Create a new user with API credentials."""
        # Generate API credentials
        api_key, api_secret = generate_api_credentials()
        
        # Create user with hashed secret
        user = User(
            name=data.name,
            api_key=api_key,
            api_secret=hash_secret(api_secret),
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

    async def update(self, user_id: UUID, name: str) -> User:
        """Update user settings."""
        user = self.db.query(User).get(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        user.name = name
        
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
        
        api_key, api_secret = generate_api_credentials()
        
        user.api_key = api_key
        user.api_secret = hash_secret(api_secret)
        
        try:
            self.db.commit()
            return api_key, api_secret
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error rotating API key: {str(e)}")
            raise HTTPException(status_code=400, detail="Error rotating API key")
