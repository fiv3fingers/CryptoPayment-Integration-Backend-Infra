# models/schemas/quote.py
from pydantic import BaseModel, UUID4
from typing import List
from datetime import datetime



class CurrencyQuote(BaseModel):
    currency_id: str
    price_usd: float
    value_usd: float
    amount: float


class QuoteRequest(BaseModel):
    order_id: UUID4
    currencies: List[str]


class QuoteResponse(BaseModel):
    order_id: UUID4
    timestamp: datetime
    quotes: List[CurrencyQuote]


