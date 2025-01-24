from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from src.utils.currencies.types import Currency, CurrencyBase
from src.models.enums import PayOrderMode, PayOrderStatus
from src.utils.types import ChainId, ChainType

from pydantic import BaseModel, Field


class MetadataItems(BaseModel):
    name: str                       = Field(examples=["t-shirt"], default=None)
    description: Optional[str]      = Field(examples=["A nice t-shirt"], default=None)
    image: Optional[str]            = Field(examples=["https://example.com/image.png"], default=None)
    quantity: Optional[int]         = Field(examples=[1], default=None)
    unit_price: Optional[float]     = Field(examples=[0.1], default=None)
    currency: Optional[str]         = Field(examples=["USD"], default=None)


class PayOrderMetadata(BaseModel):
    items: Optional[List[MetadataItems]] = Field(default_factory=list)


# CREATE PAYORDER
class CreatePayOrderRequest(BaseModel):
    mode: PayOrderMode                           = Field(examples=[PayOrderMode.SALE], title="PayOrder mode")
    metadata: Optional[PayOrderMetadata]         = Field(default_factory=PayOrderMetadata)

    # if destination_currency and destination_amount is set omit destination_value_usd
    destination_currency: Optional[CurrencyBase] = Field(default=None)
    destination_amount: Optional[float]          = Field(examples=[0.1], default=None)

    # if destination_value_usd is set omit destination_amount and destination_currency
    destination_value_usd: Optional[float]       = Field(examples=[250], default=None)

    destination_receiving_address: Optional[str] = Field(examples=["0x311e128453EFd91a4c131761d9d535fF6E0EEF90"], default=None)
    
class PayOrderResponse(BaseModel):
    id: str = Field(examples=["cm5h7ubkp0000v450cwvq6kc7"])
    mode: PayOrderMode = Field(examples=[PayOrderMode.DEPOSIT], title="PayOrder mode")
    status: PayOrderStatus = Field(examples=[PayOrderStatus.PENDING], title="PayOrder status")

    metadata: Optional[PayOrderMetadata] = Field(default_factory=PayOrderMetadata)
    destination_amount: Optional[float]  = Field(examples=[0.1], default=None)
    destination_currency: Optional[Currency] = Field(default=None)
    destination_value_usd: Optional[float] = Field(examples=[250], default=None)



# CREATE QUOTE
class CreateQuoteRequest(BaseModel):
    wallet_address: str = Field(examples=["0x311e128453EFd91a4c131761d9d535fF6E0EEF90"])
    chain_type: ChainType = Field(examples=[ChainType.EVM])
    evm_chain_ids: Optional[List[ChainId]] = Field(default=None, examples=[[ChainId.ETH, ChainId.BASE]])
    # destination_ui_amount: Optional[float] = Field(examples=[3.5])

class CreateQuoteResponse(BaseModel):
    source_currencies: List[Currency]


# CREATE PAYMENT DETAILS
class PaymentDetailsRequest(BaseModel):
    source_currency: CurrencyBase
    refund_address: str = Field(examples=["0x311e128453EFd91a4c131761d9d535fF6E0EEF90"])

class PaymentDetailsResponse(BaseModel):
    id: str  = Field(examples=["cm5h7ubkp0000v450cwvq6kc7"])
    mode: PayOrderMode = Field(examples=[PayOrderMode.DEPOSIT], title="PayOrder mode")
    status: PayOrderStatus = Field(examples=[PayOrderStatus.PENDING], title="PayOrder status")
    expires_at: datetime = Field(examples=["2025-01-24T18:37:31.430985+01:00"], title="PayOrder expiration date")

    source_currency: Currency
    deposit_address: str = Field(examples=["0x311e128453EFd91a4c131761d9d535fF6E0EEF90"])
    refund_address: str = Field(examples=["0x311e128453EFd91a4c131761d9d535fF6E0EEF90"])

    # Deposits Only 
    destination_currency: Optional[Currency] = Field(default=None)
    destination_receiving_address: Optional[str] = Field(default=None)
