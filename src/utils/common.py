# utils/common.py
import secrets
import hashlib
import logging


logger = logging.getLogger(__name__)

def generate_api_credentials() -> tuple[str, str]:
    """Generate secure API key and secret."""
    api_key = secrets.token_urlsafe(32)
    api_secret = secrets.token_urlsafe(64)
    return api_key, api_secret

def hash_secret(secret: str) -> str:
    """Hash the API secret for storage."""
    return hashlib.sha256(secret.encode()).hexdigest()


