# models/schemas/quote.py
from pydantic import BaseModel, UUID4
from typing import List
from datetime import datetime

from models.schemas.currency import Currency



class CurrencyQuote(BaseModel):
    currency: Currency
    amount: float


class QuoteRequest(BaseModel):
    user_address: str
    chain_name: str


class QuoteResponse(BaseModel):
    order_id: str
    timestamp: datetime
    quotes: List[CurrencyQuote]


