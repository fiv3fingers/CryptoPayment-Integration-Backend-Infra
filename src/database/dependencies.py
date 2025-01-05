from fastapi import Depends, HTTPException, status

from fastapi.security import APIKeyHeader 
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from ..models.database_models import User, Organization
from .database import get_db

import jwt

import os


SECRET_KEY = os.getenv("AUTH_SECRET")
ALGORITHM = "HS256"


api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False)

security = HTTPBearer()

def get_current_organization(api_key: str = Depends(api_key_header), db: Session = Depends(get_db)) -> Organization:
    organization = db.query(Organization).filter(Organization.api_key == api_key).first()
    if organization is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API Key")
    return organization

