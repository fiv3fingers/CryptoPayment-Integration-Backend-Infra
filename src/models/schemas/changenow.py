from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict, model_validator

from enum import Enum
from datetime import datetime

class FlowType(str, Enum):
    STANDARD = "standard"
    FIXED_RATE = "fixed-rate"

class TransactionType(str, Enum):
    DIRECT = "direct"
    REVERSE = "reverse"

class TransactionStatus(str, Enum):
    NEW = "new"
    WAITING = "waiting"
    CONFIRMING = "confirming"
    EXCHANGING = "exchanging"
    SENDING = "sending"
    FINISHED = "finished"
    FAILED = "failed"
    REFUNDED = "refunded"
    EXPIRED = "expired"


class Currency(BaseModel):
    """Model for currency information"""
    ticker: str
    name: str
    image: str
    has_external_id: bool = Field(alias="hasExternalId")
    is_fiat: bool = Field(alias="isFiat")
    featured: bool
    is_stable: bool = Field(alias="isStable")
    supports_fixed_rate: bool = Field(alias="supportsFixedRate")
    network: str
    token_contract: Optional[str] = Field(alias="tokenContract")
    buy: bool
    sell: bool
    legacy_ticker: str = Field(alias="legacyTicker")
    
    model_config = ConfigDict(populate_by_name=True)


class ExchangeEstimate(BaseModel):
    """Response model for exchange estimation endpoint"""
    from_amount: float = Field(..., alias="fromAmount")
    to_amount: float = Field(..., alias="toAmount")
    from_currency: str = Field(..., alias="fromCurrency")
    to_currency: str = Field(..., alias="toCurrency")
    from_network: str = Field(..., alias="fromNetwork")
    to_network: str = Field(..., alias="toNetwork")
    flow: Optional[str] = Field(default="standard")
    type: Optional[str] = Field(default="direct")
    rate_id: Optional[str] = Field(None, alias="rateId")
    valid_until: Optional[str] = Field(None, alias="validUntil")
    transaction_speed_forecast: Optional[str] = Field(None, alias="transactionSpeedForecast")
    warning_message: Optional[str] = Field(None, alias="warningMessage")
    deposit_fee: Optional[float] = Field(None, alias="depositFee")
    withdrawal_fee: Optional[float] = Field(None, alias="withdrawalFee")
    user_id: Optional[str] = Field(None, alias="userId")

    model_config = ConfigDict(
        populate_by_name=True,
        use_enum_values=True,
        extra='ignore'
    )

class ExchangeTransaction(BaseModel):
    """Response model for created exchange transactions"""
    id: str
    from_amount: float = Field(..., alias="fromAmount")
    to_amount: float = Field(..., alias="toAmount")
    from_currency: str = Field(..., alias="fromCurrency")
    to_currency: str = Field(..., alias="toCurrency")
    from_network: str = Field(..., alias="fromNetwork")
    to_network: str = Field(..., alias="toNetwork")
    payin_address: str = Field(..., alias="payinAddress")
    payout_address: str = Field(..., alias="payoutAddress")
    expected_to_amount: Optional[float] = Field(None, alias="expectedToAmount")
    status: Optional[TransactionStatus] = Field(default=TransactionStatus.NEW)
    refund_address: Optional[str] = Field(None, alias="refundAddress")
    created_at: Optional[str] = Field(None, alias="createdAt")
    updated_at: Optional[str] = Field(None, alias="updatedAt")
    hash: Optional[str] = None
    payout_hash: Optional[str] = Field(None, alias="payoutHash")
    payout_extra_id: Optional[str] = Field(None, alias="payoutExtraId")
    payment_status: Optional[str] = Field(None, alias="paymentStatus")
    message: Optional[str] = None

    model_config = ConfigDict(
        populate_by_name=True,
        use_enum_values=True,
        extra='ignore'
    )


class ExchangeRequestBase(BaseModel):
    """Base model for exchange-related requests"""
    from_currency: str = Field(..., alias="fromCurrency")
    to_currency: str = Field(..., alias="toCurrency")
    from_network: str = Field(..., alias="fromNetwork")
    to_network: str = Field(..., alias="toNetwork")
    flow: FlowType = Field(default=FlowType.STANDARD)
    type: TransactionType = Field(default=TransactionType.DIRECT)

    model_config = ConfigDict(
        populate_by_name=True,
        use_enum_values=True,
        extra='ignore'
    )

class EstimateRequest(BaseModel):
    """Request model for exchange estimation"""
    from_currency: str = Field(..., alias="fromCurrency")
    to_currency: str = Field(..., alias="toCurrency")
    from_network: str = Field(..., alias="fromNetwork")
    to_network: str = Field(..., alias="toNetwork")
    from_amount: Optional[float] = Field(None, alias="fromAmount")
    to_amount: Optional[float] = Field(None, alias="toAmount")
    flow: FlowType = Field(default=FlowType.STANDARD)
    type: TransactionType = Field(default=TransactionType.DIRECT)

    model_config = ConfigDict(
        populate_by_name=True,
        use_enum_values=True,
        extra='ignore'
    )

    @model_validator(mode='before')
    @classmethod
    def validate_amounts(cls, values):
        """Ensure either fromAmount or toAmount is provided based on type"""
        type_ = values.get('type', TransactionType.DIRECT)
        from_amount = values.get('fromAmount')
        to_amount = values.get('toAmount')

        if type_ == TransactionType.DIRECT and from_amount is None:
            raise ValueError("fromAmount is required for direct exchanges")
        elif type_ == TransactionType.REVERSE and to_amount is None:
            raise ValueError("toAmount is required for reverse exchanges")
        
        return values


class CreateExchangeRequest(ExchangeRequestBase):
    """Request model for creating exchange transactions"""
    from_amount: float = Field(..., alias="fromAmount")
    address: str 
    refund_address: str = Field(..., alias="refundAddress")
    to_amount: Optional[str] = Field("", alias="toAmount")
    extra_id: Optional[str] = Field("", alias="extraId")
    refund_extra_id: Optional[str] = Field("", alias="refundExtraId")
    user_id: Optional[str] = Field("", alias="userId")
    payload: Optional[str] = Field("")
    contact_email: Optional[str] = Field("", alias="contactEmail")
    source: Optional[str] = Field("")
    rate_id: Optional[str] = Field("", alias="rateId")

    model_config = ConfigDict(
        populate_by_name=True,
        use_enum_values=True,
        extra='ignore',
        
    )

class ExchangeStatusResponse(BaseModel):
    """Response model for exchange status endpoint"""
    id: str
    status: str
    actions_available: bool = Field(..., alias="actionsAvailable")
    
    from_currency: str = Field(..., alias="fromCurrency")
    from_network: str = Field(..., alias="fromNetwork")
    to_currency: str = Field(..., alias="toCurrency")
    to_network: str = Field(..., alias="toNetwork")
    from_legacy_ticker: str = Field(..., alias="fromLegacyTicker")
    to_legacy_ticker: str = Field(..., alias="toLegacyTicker")
    
    expected_amount_from: float = Field(..., alias="expectedAmountFrom")
    expected_amount_to: float = Field(..., alias="expectedAmountTo")
    amount_from: Optional[float] = Field(None, alias="amountFrom")
    amount_to: Optional[float] = Field(None, alias="amountTo")
    
    payin_address: str = Field(..., alias="payinAddress")
    payout_address: str = Field(..., alias="payoutAddress")
    payin_extra_id: Optional[str] = Field(None, alias="payinExtraId")
    payout_extra_id: Optional[str] = Field(None, alias="payoutExtraId")
    refund_address: Optional[str] = Field(None, alias="refundAddress")
    refund_extra_id: Optional[str] = Field(None, alias="refundExtraId")
    
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: datetime = Field(..., alias="updatedAt")
    valid_until: Optional[datetime] = Field(None, alias="validUntil")
    deposit_received_at: Optional[datetime] = Field(None, alias="depositReceivedAt")
    
    payin_hash: Optional[str] = Field(None, alias="payinHash")
    payout_hash: Optional[str] = Field(None, alias="payoutHash")
    refund_hash: Optional[str] = Field(None, alias="refundHash")
    
    refund_amount: Optional[float] = Field(None, alias="refundAmount")
    user_id: Optional[str] = Field(None, alias="userId")
    original_exchange_info: Optional[dict] = Field(None, alias="originalExchangeInfo")
    related_exchanges_info: List[dict] = Field([], alias="relatedExchangesInfo")
    repeated_exchanges_info: List[dict] = Field([], alias="repeatedExchangesInfo")

    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={datetime: lambda v: v.isoformat()},
        extra='ignore'
    )
