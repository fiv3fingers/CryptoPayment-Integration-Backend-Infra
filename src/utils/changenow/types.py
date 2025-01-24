from enum import Enum
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class Flow(str, Enum):
    STANDARD = "standard"
    FIXED = "fixed-rate"

class ExchangeType(str, Enum):
    DIRECT = "direct"
    REVERSE = "reverse"

class Status(str, Enum):
    NEW = "new"
    WAITING = "waiting"
    CONFIRMING = "confirming"
    EXCHANGING = "exchanging"
    SENDING = "sending"
    FINISHED = "finished"
    FAILED = "failed"
    REFUNDED = "refunded"
    EXPIRED = "expired"

class BaseRequest(BaseModel):
    """Base model for all exchange requests"""
    model_config = ConfigDict(
        populate_by_name=True,
        use_enum_values=True,
        alias_generator=lambda x: ''.join(word.capitalize() if i else word for i, word in enumerate(x.split('_')))
    )

class ChangeNowCurrency(BaseRequest):
    """Available currency for exchange"""
    ticker: str
    name: str
    network: str
    image: str
    token_contract: Optional[str] = None
    is_fiat: bool
    is_stable: bool
    has_external_id: bool
    supports_fixed_rate: bool
    featured: bool
    buy: bool
    sell: bool
    legacy_ticker: str

class EstimateRequest(BaseRequest):
    """Exchange estimation request"""
    from_currency: str
    to_currency: str
    from_network: str
    to_network: str
    from_amount: Optional[float] = None
    to_amount: Optional[float] = None
    flow: Flow = Flow.STANDARD
    type: ExchangeType = ExchangeType.DIRECT

    def to_api_params(self) -> dict:
        """Convert to API parameters"""
        params = self.model_dump(by_alias=True, exclude_none=True)
        
        # Format amounts to 8 decimal places if present
        if self.from_amount is not None:
            params["fromAmount"] = f"{self.from_amount:.8f}"
        if self.to_amount is not None:
            params["toAmount"] = f"{self.to_amount:.8f}"
            
        return params

class ExchangeRequest(BaseRequest):
    """Create exchange request"""
    from_currency: str
    to_currency: str
    from_network: str
    to_network: str
    from_amount: float
    recipient_address: str = Field(alias="address")
    refund_address: str
    flow: Flow = Flow.STANDARD
    type: ExchangeType = ExchangeType.DIRECT
    rate_id: Optional[str] = None
    extra_id: Optional[str] = None
    refund_extra_id: Optional[str] = None
    user_id: Optional[str] = None
    contact_email: Optional[str] = None

    def to_api_params(self) -> dict:
        """Convert to API parameters"""
        params = self.model_dump(by_alias=True, exclude_none=True)
        params["fromAmount"] = f"{self.from_amount:.8f}"
        return params

class Estimate(BaseRequest):
    """Exchange estimation response"""
    from_currency: str
    to_currency: str
    from_network: str
    to_network: str
    from_amount: float
    to_amount: float
    flow: str
    type: str
    rate_id: Optional[str] = None
    valid_until: Optional[str] = None
    transaction_speed: Optional[str] = Field(None, alias="transactionSpeedForecast")
    warning: Optional[str] = Field(None, alias="warningMessage")
    deposit_fee: Optional[float] = None
    withdrawal_fee: Optional[float] = None

class Exchange(BaseRequest):
    """Exchange transaction"""
    id: str
    status: Status = Status.NEW
    from_currency: str
    to_currency: str
    from_network: str
    to_network: str
    from_amount: float
    to_amount: float
    deposit_address: str = Field(alias="payinAddress")
    recipient_address: str = Field(alias="payoutAddress")
    deposit_hash: Optional[str] = Field(None, alias="payinHash")
    payout_hash: Optional[str] = None
    expected_amount: Optional[float] = Field(None, alias="expectedToAmount")
    refund_address: Optional[str] = None
    message: Optional[str] = None


class ExchangeStatus(BaseRequest):
    """Detailed exchange status"""
    id: str
    status: Status
    has_actions: bool = Field(alias="actionsAvailable")
    
    from_currency: str
    to_currency: str
    from_network: str
    to_network: str
    #from_ticker: str = Field(alias="fromLegacyTicker")
    #to_ticker: str = Field(alias="toLegacyTicker")
    
    expected_send_amount: Optional[float] = Field(None, alias="expectedAmountFrom")
    expected_receive_amount: Optional[float] = Field(None, alias="expectedAmountTo")
    actual_send_amount: Optional[float] = Field(None, alias="amountFrom")
    actual_receive_amount: Optional[float] = Field(None, alias="amountTo")
    
    deposit_address: str = Field(alias="payinAddress")
    recipient_address: str = Field(alias="payoutAddress")
    refund_address: Optional[str] = None
    
    created_at: datetime
    updated_at: datetime
    valid_until: Optional[datetime] = Field(None, alias="validUntil")
    deposit_received_at: Optional[datetime] = None
    
    deposit_hash: Optional[str] = Field(None, alias="payinHash")
    payout_hash: Optional[str] = None
    refund_hash: Optional[str] = None
    refund_amount: Optional[float] = None
