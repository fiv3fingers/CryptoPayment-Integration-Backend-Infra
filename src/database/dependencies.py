from fastapi import Depends, HTTPException, status

from fastapi.security import APIKeyHeader 
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from src.models.database_models import Organization
from src.database.database import get_db
from src.utils.signature import parse_header, validate_signature


api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False)
authorization_header = APIKeyHeader(name="Authorization", auto_error=False)

security = HTTPBearer()

def get_current_organization(api_key: str = Depends(api_key_header), db: Session = Depends(get_db)) -> Organization:
    organization = db.query(Organization).filter(Organization.api_key == api_key).first()
    if organization is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API Key")
    return organization


def validate_authorization_header(auth_header: str = Depends(authorization_header), db: Session = Depends(get_db)) -> Organization:
    if auth_header is None:
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Signature")
    
    header_parts = parse_header(auth_header)
    organization = db.query(Organization).filter(Organization.api_key == header_parts["apiKey"]).first()

    valid = validate_signature(header_parts, organization.secret)
    if not valid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Signature")
    
    return organization

