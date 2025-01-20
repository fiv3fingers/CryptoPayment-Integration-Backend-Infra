from fastapi import Depends, HTTPException, status

from fastapi.security import APIKeyHeader 
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from src.models.database_models import Organization
from src.database.database import get_db


api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False)
authorization_header = APIKeyHeader(name="Authorization", auto_error=False)

security = HTTPBearer()

def get_current_organization(api_key: str = Depends(api_key_header), db: Session = Depends(get_db)) -> Organization:
    organization = db.query(Organization).filter(Organization.api_key == api_key).first()
    if organization is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API Key")
    return organization


def validate_signature(authorization: str = Depends(authorization_header)) -> bool:
    # TODO: Implement this
    if authorization is None:
        return False
    else:
        return True

