from typing import Optional 
from pydantic import BaseModel
from models.networks import Chain

class Token(BaseModel):
    address: str
    decimals: int
    chain_id: str

    name: str
    symbol: str
    logo: Optional[str]
    description: Optional[str]

    price_usd: Optional[float]
    is_stablecoin: Optional[bool]


class TokenBalance(BaseModel):
    token: Token
    balance: int

