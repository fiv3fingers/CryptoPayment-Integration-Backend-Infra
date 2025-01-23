from typing import List, Optional
from src.utils.currencies.types import Currency, CurrencyBase
from pydantic import BaseModel, Field
from datetime import datetime

from src.models.enums import PayOrderMode, PayOrderStatus
from src.utils.types import ChainId

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
    


class CreatePayOrderResponse(BaseModel):
    id: str = Field(examples=["cm5h7ubkp0000v450cwvq6kc7"])
    mode: PayOrderMode = Field(examples=[PayOrderMode.DEPOSIT], title="PayOrder mode")
    status: PayOrderStatus = Field(examples=[PayOrderStatus.PENDING], title="PayOrder status")

    metadata: Optional[PayOrderMetadata] = Field(default_factory=PayOrderMetadata)
    destination_amount: Optional[float]  = Field(examples=[0.1], default=None)
    destination_currency: Optional[Currency]
    destination_value_usd: Optional[float] = Field(examples=[250], default=None)

# CREATE QUOTE

class CreateQuoteRequest(BaseModel):
    wallet_address: str = Field(examples=["0x311e128453EFd91a4c131761d9d535fF6E0EEF90"])
    chain_id: ChainId = Field(examples=[ChainId.ETH])
    # destination_ui_amount: Optional[float] = Field(examples=[3.5])

class CreateQuoteResponse(BaseModel):
    source_currencies: List[Currency]
    # destination_currency: Optional[Currency]

# CREATE PAYMENT DETAILS

class PaymentDetailsRequest(BaseModel):
    source_currency: CurrencyBase
    # destination_amount: float
    # destination_receiving_address: str
    refund_address: str

class PaymentDetailsResponse(BaseModel):
    id: str 
    mode: PayOrderMode
    status: PayOrderStatus
    expires_at: datetime

    source_currency: Currency
    deposit_address: str
    refund_address: str

    # Deposits Only 
    destination_currency: Optional[Currency] = Field(default=None)
    destination_receiving_address: Optional[str] = Field(default=None)

# class PaySaleRequest(BaseModel):
#     source_currency: CurrencyBase
#     refund_address: str

# class PaySaleResponse(BaseModel):
#     id: str
#     mode: PayOrderMode
#     status: PayOrderStatus
#     expires_at: datetime

#     source_currency: Currency
#     deposit_address: str
#     #amount: int
#     #ui_amount: float


# CREATE & UPDATE SALE
class CreateSaleRequest(BaseModel):
    metadata: Optional[PayOrderMetadata]    = Field(default_factory=PayOrderMetadata)
    destination_value_usd: float            = Field(examples=[250], default=None)


class UpdateSaleRequest(BaseModel):
    metadata: Optional[PayOrderMetadata]    = Field(default_factory=PayOrderMetadata)
    destination_value_usd: Optional[float]  = Field(examples=[250], default=None)

class SaleResponse(BaseModel):
    id: str
    mode: PayOrderMode
    status: PayOrderStatus

    metadata: dict
    destination_value_usd: float


# QUOTE
class QuoteSaleRequest(BaseModel):
    wallet_address: str = Field(examples=["0x311e128453EFd91a4c131761d9d535fF6E0EEF90"])
    chain_id: ChainId = Field(examples=[ChainId.ETH])

class QuoteSaleResponse(BaseModel):
    source_currencies: List[Currency]


# PAYMENT DETAILS
class PaySaleRequest(BaseModel):
    source_currency: CurrencyBase
    refund_address: str

class PaySaleResponse(BaseModel):
    id: str
    mode: PayOrderMode
    status: PayOrderStatus
    expires_at: datetime

    source_currency: Currency
    deposit_address: str
    #amount: int
    #ui_amount: float




# CREATE & UPDATE DEPOSIT
class CreateDepositRequest(BaseModel):
    metadata: Optional[PayOrderMetadata] = Field(default_factory=PayOrderMetadata)
    destination_currency: CurrencyBase = Field(
        examples=[
            dict(address="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48", chain_id=ChainId.ETH)],
        title="Destination currency"
    )


class UpdateDepositRequest(CreateDepositRequest):
    pass


class DepositResponse(BaseModel):
    id: str = Field(examples=["cm5h7ubkp0000v450cwvq6kc7"])
    mode: PayOrderMode = Field(examples=[PayOrderMode.DEPOSIT], title="PayOrder mode")
    status: PayOrderStatus = Field(examples=[PayOrderStatus.PENDING], title="PayOrder status")

    metadata: Optional[PayOrderMetadata] = Field(default_factory=PayOrderMetadata)
    destination_currency: Currency 


# QUOTE
class QuoteDepositRequest(BaseModel):
    wallet_address: str = Field(examples=["0x311e128453EFd91a4c131761d9d535fF6E0EEF90"])
    chain_id: ChainId = Field(examples=[ChainId.ETH])
    destination_ui_amount: float = Field(examples=[3.5])

class QuoteDepositResponse(BaseModel):
    source_currencies: List[Currency]
    destination_currency: Currency


# PAYMENT DETAILS
class PayDepositRequest(BaseModel):
    source_currency: CurrencyBase
    destination_amount: float
    destination_receiving_address: str
    refund_address: str

class PayDepositResponse(BaseModel):
    id: str 
    mode: PayOrderMode
    status: PayOrderStatus
    expires_at: datetime

    source_currency: Currency
    destination_currency: Currency
    deposit_address: str
    refund_address: str

    destination_receiving_address: str


# class PayOrderResponse(BaseModel):
#     id: str =                                       Field(examples=["cm5h7ubkp0000v450cwvq6kc7"])
#     mode: PayOrderMode =                            Field(examples=[PayOrderMode.SALE], title="PayOrder mode")
#     status: PayOrderStatus =                        Field(examples=[PayOrderStatus.PENDING], title="PayOrder status")

#     source_currency: Optional[Currency] =           Field(default=None)
#     source_amount: Optional[float] =                Field(examples=[0.1], default=None)
#     source_value_usd: Optional[float] =             Field(examples=[250], default=None)
#     source_address: Optional[str] =                 Field(examples=["0x311e128453EFd91a4c131761d9d535fF6E0EEF90"], default=None)
#     source_transaction_hash: Optional[str] =        Field(default=None)

#     destination_currency: Optional[Currency] =      Field(default=None)
#     destination_amount: Optional[float] =           Field(examples=[0.1], default=None)
#     destination_value_usd: Optional[float] =        Field(examples=[250], default=None)
#     destination_receiving_address: Optional[str] =            Field(examples=["0x311e128453EFd91a4c131761d9d535fF6E0EEF90"], default=None)
#     destination_transaction_hash: Optional[str] =   Field(default=None)

#     refund_address: Optional[str] =                 Field(examples=["0x311e128453EFd91a4c131761d9d535fF6E0EEF90"], default=None)

#     created_at: Optional[datetime] =                Field(default=None)
#     expires_at: Optional[datetime] =                Field(default=None)
#     metadata: Optional[PayOrderMetadata] =          Field(default_factory=dict)


# class CreatePaymentRequest(BaseModel):
#     token_address: Optional[str] = Field(examples=["0x311e128453EFd91a4c131761d9d535fF6E0EEF90"], default=None)
#     token_chain_id: ChainId = Field(examples=[ChainId.ETH])
#     refund_address: str = Field(examples=["0x311e128453EFd91a4c131761d9d535fF6E0EEF90"])


# class CreatePaymentResponse(BaseModel):
#     id: str = Field(examples=["cm5h7ubkp0000v450cwvq6kc7"])
#     mode: PayOrderMode = Field(examples=[PayOrderMode.SALE], title="PayOrder mode")
#     status: PayOrderStatus = Field(examples=[PayOrderStatus.PENDING], title="PayOrder status")
#     expires_at: datetime = Field(examples=["2021-09-01T00:00:00Z"])

#     source_currency: Currency
#     source_amount: float = Field(examples=[0.1])
#     destination_currency: Optional[Currency] = Field(default=None)
#     destination_amount: Optional[float] = Field(examples=[200.0], default=None)
#     deposit_address: str = Field(examples=["0x311e128453EFd91a4c131761d9d535fF6E0EEF90"])
