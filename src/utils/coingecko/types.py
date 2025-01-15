from typing import Dict, Optional, List 
from enum import Enum
from pydantic import BaseModel, Field, field_validator


class VSCurrency(str, Enum):
    """Supported vs currencies"""
    USD = "usd"
    EUR = "eur"
    BTC = "btc"
    ETH = "eth"

class PriceParams(BaseModel):
    """Parameters for price requests"""
    ids: List[str] = Field(..., description="Coin IDs to query")
    vs_currencies: List[VSCurrency] = Field(default=[VSCurrency.USD], description="Currencies to convert to")
    include_market_cap: bool = Field(default=False)
    include_24hr_vol: bool = Field(default=False)
    include_24hr_change: bool = Field(default=False)
    include_last_updated_at: bool = Field(default=False)
    precision: Optional[int] = Field(default=None, ge=0, le=18)

    def to_query_params(self) -> Dict[str, str]:
        params = {
            "ids": ",".join(self.ids),
            "vs_currencies": ",".join([c.value for c in self.vs_currencies])
        }
        if self.include_market_cap:
            params["include_market_cap"] = "true"
        if self.include_24hr_vol:
            params["include_24h_vol"] = "true"
        if self.include_24hr_change:
            params["include_24h_change"] = "true"
        if self.include_last_updated_at:
            params["include_last_updated_at"] = "true"
        if self.precision is not None:
            params["precision"] = str(self.precision)
        return params

class Image(BaseModel):
    thumb: str
    small: str
    large: str

class Platform(BaseModel):
    decimal_place: Optional[int] = None
    contract_address: Optional[str] = None

class Links(BaseModel):
    homepage: List[str] = Field(default_factory=list)
    blockchain_site: List[str] = Field(default_factory=list)
    twitter_screen_name: Optional[str] = None
    telegram_channel_identifier: Optional[str] = None
    subreddit_url: Optional[str] = None

class MarketData(BaseModel):
    current_price: Dict[str, float] = Field(default_factory=dict)
    market_cap: Dict[str, float] = Field(default_factory=dict)
    total_volume: Dict[str, float] = Field(default_factory=dict)
    price_change_percentage_24h: Optional[float] = None
    price_change_percentage_7d: Optional[float] = None
    price_change_percentage_30d: Optional[float] = None
    price_change_24h: Optional[float] = None
    market_cap_change_24h: Optional[float] = None
    total_supply: Optional[float] = None
    max_supply: Optional[float] = None
    circulating_supply: Optional[float] = None
    last_updated: str

class TokenInfo(BaseModel):
    id: str
    symbol: str
    name: str
    asset_platform_id: Optional[str] = None
    platforms: Optional[Dict[str, str]] = Field(default_factory=dict)
    detail_platforms: Dict[str, Platform] = Field(default_factory=dict)
    image: Image
    contract_address: Optional[str] = None
    market_cap_rank: Optional[int] = None
    market_data: Optional[MarketData] = None
    last_updated: str
    links: Links = Field(default_factory=Links)

    @field_validator('detail_platforms', mode='before')
    def ensure_detail_platforms(cls, v):
        """Ensure detail_platforms is properly formatted"""
        if not v:
            return {}
        return v

class Price(BaseModel):
    """Price information for a token"""
    currency_id: str
    price: float
    vs_currency: VSCurrency
    last_updated_at: Optional[int] = None
