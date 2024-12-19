from fastapi import Depends, HTTPException, status

from fastapi.security import APIKeyHeader, OAuth2PasswordBearer
from sqlalchemy.orm import Session
from database.database import get_db
from models.database_models import User, Organization

import os


SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"


api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False)

def get_current_user(api_key: str = Depends(api_key_header), db: Session = Depends(get_db)) -> User:
    user = db.query(User).filter(User.api_key == api_key).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API Key")
    return user

def get_current_organization(api_key: str = Depends(api_key_header), db: Session = Depends(get_db)) -> Organization:
    organization = db.query(Organization).filter(Organization.api_key == api_key).first()
    if organization is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API Key")
    return organization

