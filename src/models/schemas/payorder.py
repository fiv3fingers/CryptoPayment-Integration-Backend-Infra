from typing import Optional
from src.utils.currencies.types import Currency
from pydantic import BaseModel, Field
from datetime import datetime

from src.models.enums import PayOrderMode, PayOrderStatus
from src.utils.types import ChainId

from pydantic import BaseModel, Field


class CreateSaleRequest(BaseModel):
    metadata: Optional[dict] = Field(default_factory=dict)
    destination_value_usd: Optional[float] = Field(examples=[250], default=None)


class CreateDepositRequest(BaseModel):
    metadata: Optional[dict] = Field(default_factory=dict)
    refund_address: Optional[str] = Field(examples=["0x311e128453EFd91a4c131761d9d535fF6E0EEF90"], default=None)
    destination_token_address: Optional[str] = Field(examples=["0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"], default=None)
    destination_token_chain_id: Optional[ChainId] = Field(examples=[ChainId.ETH], default=None)
    destination_amount: Optional[float] = Field(examples=[200], default=None)
    destination_address: Optional[str] = Field(examples=["9zUcFmUcdMwgH84vKofyL9xzULXh9F7uviNSYWb81f7e"], default=None)



class UpdateSaleRequest(CreateSaleRequest):
    id: str = Field(examples=["cm5h7ubkp0000v450cwvq6kc7"])

class UpdateDepositRequest(CreateDepositRequest):
    id: str = Field(examples=["cm5h7ubkp0000v450cwvq6kc7"])




class PayOrderResponse(BaseModel):
    id: str =                                       Field(examples=["cm5h7ubkp0000v450cwvq6kc7"])
    mode: PayOrderMode =                            Field(examples=[PayOrderMode.SALE], title="PayOrder mode")
    status: PayOrderStatus =                        Field(examples=[PayOrderStatus.PENDING], title="PayOrder status")

    source_currency: Optional[Currency] =           Field(default=None)
    source_amount: Optional[float] =                Field(examples=[0.1], default=None)
    source_value_usd: Optional[float] =             Field(examples=[250], default=None)
    source_address: Optional[str] =                 Field(examples=["0x311e128453EFd91a4c131761d9d535fF6E0EEF90"], default=None)
    source_transaction_hash: Optional[str] =        Field(default=None)

    destination_currency: Optional[Currency] =      Field(default=None)
    destination_amount: Optional[float] =           Field(examples=[0.1], default=None)
    destination_value_usd: Optional[float] =        Field(examples=[250], default=None)
    destination_address: Optional[str] =            Field(examples=["0x311e128453EFd91a4c131761d9d535fF6E0EEF90"], default=None)
    destination_transaction_hash: Optional[str] =   Field(default=None)

    refund_address: Optional[str] =                 Field(examples=["0x311e128453EFd91a4c131761d9d535fF6E0EEF90"], default=None)

    created_at: Optional[datetime] =                Field(default=None)
    expires_at: Optional[datetime] =                Field(default=None)
    metadata: dict =                                Field(default_factory=dict)




class CreatePaymentRequest(BaseModel):
    id: str = Field(examples=["cm5h7ubkp0000v450cwvq6kc7"])
    token_address: Optional[str] = Field(examples=["0x311e128453EFd91a4c131761d9d535fF6E0EEF90"], default=None)
    token_chain_id: ChainId
    refund_address: str


class CreatePaymentResponse(BaseModel):
    id: str = Field(examples=["cm5h7ubkp0000v450cwvq6kc7"])
    mode: PayOrderMode
    status: PayOrderStatus
    expires_at: datetime


    source_currency: Currency
    source_amount: float
    destination_currency: Optional[Currency] = Field(default=None)
    destination_amount: Optional[float] = Field(default=None)
    deposit_address: str














