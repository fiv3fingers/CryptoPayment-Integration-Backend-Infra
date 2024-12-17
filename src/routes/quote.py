# routes/quote.py

"""
    Gives a quote for a specific order.
"""


from fastapi import APIRouter, Depends, HTTPException
from pydantic import UUID4
from sqlalchemy.orm import Session
#from uuid import UUID
from typing import List
from database.dependencies import get_db, get_current_user
from services.changenow import ChangeNowClient
from services.quote import QuoteService
from models.schemas.quote import (
    QuoteRequest,
    QuoteResponse,
)
from models.database_models import User

router = APIRouter(prefix="/quotes", tags=["quotes"])

@router.post("/", response_model=QuoteResponse)
async def get_quote_for_order(
    quote_request: QuoteRequest,
    db: Session = Depends(get_db)
):
    """Get a quote for a specific order"""

    change_now_client = ChangeNowClient()
    quote_service = QuoteService(db, change_now_client)
    quotes = await quote_service.get_quotes(request=quote_request)

    if not quotes:
        raise HTTPException(status_code=404, detail="Quotes not found")

    return quotes

