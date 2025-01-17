from typing import Optional
from src.utils.currencies.types import Currency
from pydantic import BaseModel, Field
from datetime import datetime

from src.models.enums import PayOrderMode, PayOrderStatus
from src.utils.types import ChainId

from pydantic import BaseModel, Field


class PayOrderSaleCreate(BaseModel):
    metadata: Optional[dict] = Field(default_factory=dict)
    
    # Sale-specific fields
    out_value_usd: Optional[float] = Field(examples=[250], default=None)


class PayOrderDepositCreate(BaseModel):
    metadata: Optional[dict] = Field(default_factory=dict)
    
    # Common fields
    refund_address: Optional[str] = Field(examples=["0x311e128453EFd91a4c131761d9d535fF6E0EEF90"], default=None)
    
    # Deposit-specific fields
    out_token_address: Optional[str] = Field(examples=["0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"], default=None)
    out_token_chain_id: Optional[ChainId] = Field(examples=[ChainId.ETH], default=None)
    out_amount: Optional[float] = Field(examples=[200], default=None)
    out_address: Optional[str] = Field(examples=["9zUcFmUcdMwgH84vKofyL9xzULXh9F7uviNSYWb81f7e"], default=None)


class PayOrderResponse(BaseModel):
    id: str = Field(examples=["cm5h7ubkp0000v450cwvq6kc7"])
    mode: PayOrderMode = Field(examples=[PayOrderMode.SALE], title="PayOrder mode")
    status: PayOrderStatus = Field(examples=[PayOrderStatus.PENDING], title="PayOrder status")

    in_currency: Optional[Currency] = Field(default=None)
    in_amount: Optional[float] = Field(examples=[0.1], default=None)
    in_value_usd: Optional[float] = Field(examples=[250], default=None)
    in_address: Optional[str] = Field(examples=["0x311e128453EFd91a4c131761d9d535fF6E0EEF90"], default=None)

    out_currency: Optional[Currency] = Field(default=None)
    out_amount: Optional[float] = Field(examples=[0.1], default=None)
    out_value_usd: Optional[float] = Field(examples=[250], default=None)
    out_address: Optional[str] = Field(examples=["0x311e128453EFd91a4c131761d9d535fF6E0EEF90"], default=None)

    refund_address: Optional[str] = Field(examples=["0x311e128453EFd91a4c131761d9d535fF6E0EEF90"], default=None)

    created_at: datetime
    expires_at: datetime
    metadata: dict = Field(default_factory=dict)


class UpdatePayOrderRequest(BaseModel):
    out_token_address: Optional[str] = Field(examples=["0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"], default=None)
    out_token_chain_id: Optional[ChainId] = Field(examples=[ChainId.ETH], default=None)
    out_amount: Optional[float] = Field(examples=[200], default=None)
    out_address: Optional[str] = Field(examples=["9zUcFmUcdMwgH84vKofyL9xzULXh9F7uviNSYWb81f7e"], default=None)

    in_token_address: Optional[str] = Field(examples=["0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"], default=None)
    in_token_chain_id: Optional[ChainId] = Field(examples=[ChainId.ETH], default=None)

    metadata: Optional[dict] = Field(default_factory=dict)
    refund_address: Optional[str] = Field(examples=["0x311e128453EFd91a4c131761d9d535fF6E0EEF90"], default=None)
 
    out_value_usd: Optional[float] = Field(examples=[250], default=None)


class CreatePaymentRequest(BaseModel):
    id: str = Field(examples=["cm5h7ubkp0000v450cwvq6kc7"])
    token_address: str
    token_chain_id: ChainId
    refund_address: str


class CreatePaymentResponse(BaseModel):
    id: str = Field(examples=["cm5h7ubkp0000v450cwvq6kc7"])
    currency: Currency
    amount: float
    address: str
    expires_at: datetime
