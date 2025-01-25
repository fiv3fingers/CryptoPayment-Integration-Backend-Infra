from pydantic import BaseModel
from typing import List
from datetime import datetime

from src.utils.types import ChainId
from src.utils.currencies.types import Currency


class CurrencyQuote(BaseModel):
    value_usd: float
    in_currency: Currency
    out_currency: Currency


class QuoteRequest(BaseModel):
    address: str  # wallet address of the user
    chain_id: ChainId


class QuoteResponse(BaseModel):
    timestamp: datetime
    quotes: List[CurrencyQuote]
