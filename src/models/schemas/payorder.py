from typing import Optional
from src.utils.currencies.types import Currency, CurrencyBase
from pydantic import BaseModel, Field
from datetime import datetime

from src.models.enums import PayOrderMode, PayOrderStatus
from src.utils.types import ChainId

from pydantic import BaseModel, Field


# CREATE & UPDATE SALE
class CreateSaleRequest(BaseModel):
    metadata: dict 
    destination_value_usd: float

class UpdateSaleRequest(CreateSaleRequest):
    pass

class SaleResponse(BaseModel):
    id: str
    mode: PayOrderMode
    status: PayOrderStatus

    metadata: dict
    destination_value_usd: float


# QUOTE
class QuoteSaleRequest(BaseModel):
    source_currency: CurrencyBase

class QuoteSaleResponse(BaseModel):
    source_currency: Currency
    destination_currency: Currency
    destination_ui_amount: float


# PAY
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
    amount: int
    ui_amount: float





# CREATE & UPDATE DEPOSIT
class CreateDepositRequest(BaseModel):
    metadata: Optional[dict] = Field(default_factory=dict)
    destination_currency: CurrencyBase

class UpdateDepositRequest(CreateDepositRequest):
    pass

class DepositResponse(BaseModel):
    id: str = Field(examples=["cm5h7ubkp0000v450cwvq6kc7"])
    mode: PayOrderMode = Field(examples=[PayOrderMode.DEPOSIT], title="PayOrder mode")
    status: PayOrderStatus = Field(examples=[PayOrderStatus.PENDING], title="PayOrder status")

    metadata: dict = Field(default_factory=dict)
    destination_currency: Currency


# QUOTE
class QuoteDepositRequest(BaseModel):
    source_currency: CurrencyBase
    destination_ui_amount: float

class QuoteDepositResponse(BaseModel):
    source_currency: Currency
    destination_currency: Currency
    source_ui_amount: float
    destination_ui_amount: float


# PAY
class PayDepositRequest(BaseModel):
    source_currency: CurrencyBase
    destination_amount: float
    destination_address: str
    refund_address: str

class PayDepositResponse(BaseModel):
    id: str 
    mode: PayOrderMode
    status: PayOrderStatus
    expires_at: datetime

    source_currency: Currency
    source_deposit_amount: int
    source_deposit_ui_amount: float
    deposit_address: str
    refund_address: str

    destination_currency: Currency
    destination_amount: int
    destination_ui_amount: float
    destination_address: str

