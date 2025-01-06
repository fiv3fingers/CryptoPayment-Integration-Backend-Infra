# models/schemas/quote.py
from pydantic import BaseModel, UUID4
from typing import List
from datetime import datetime

from src.utils.types import ChainId

from src.utils.currencies.types import Currency


class CurrencyQuote(BaseModel):
    currency: Currency
    amount: float
    value_usd: float
    currency_out: Currency


class QuoteRequest(BaseModel):
    address: str        # wallet address of the user
    chain_id: ChainId


class QuoteResponse(BaseModel):
    order_id: str
    timestamp: datetime
    quotes: List[CurrencyQuote]


