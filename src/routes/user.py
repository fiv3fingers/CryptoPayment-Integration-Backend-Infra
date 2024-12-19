# routes/user.py
from fastapi import APIRouter, Depends, HTTPException, Security
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from database.dependencies import get_db, get_current_user
from services.user import UserService
from models.schemas.user import (
    UserCreate,
    UserResponse,
    UserCredentialsResponse
)
from models.database_models import User

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/register", response_model=UserCredentialsResponse)
async def register_user(
    data: UserCreate,
    db: Session = Depends(get_db)
):
    """Register a new user and get API credentials."""
    service = UserService(db)
    user, api_secret = await service.create(data)
    return UserCredentialsResponse(
        id=user.id,
        api_key=user.api_key,
        api_secret=api_secret,
    )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    user: User = Depends(get_current_user)
):
    """Get current user information."""
    return user

@router.put("/me", response_model=UserResponse)
async def update_user(
    name: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user settings."""
    service = UserService(db)
    return await service.update(user.id, name)

@router.post("/me/rotate-key", response_model=UserCredentialsResponse)
async def rotate_api_key(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate new API credentials."""
    service = UserService(db)
    api_key, api_secret = await service.rotate_api_key(user.id)
    return UserCredentialsResponse(
        id=user.id,
        api_key=api_key,
        api_secret=api_secret,
    )


