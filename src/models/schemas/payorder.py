"""
export type PayOrder = {
  id: string
  mode: PayOrderMode.SALE | PayOrderMode.CHOOSE_AMOUNT | PayOrderMode.FIXED 
  status: PayOrderStatus
  
  organization_id: string
  
  // total_value_usd: number

  metadata?: PayOrderMetadata
  
  source_token: PayTokenAmount | null
  source_transaction_hash: string | null
  source_status: PayOrderStatusSource | null

  destination_token: PayTokenAmount | null
  destination_transaction_hash: string | null
  destination_status: PayOrderStatusDest | null 
  destination_address: string;

  expires_at: number | null
}

export interface PayTokenAmount {
  token: Token
  amount: string
  value_usd: number
}


"""

from typing import Optional
from src.utils.currencies.types import Currency
from pydantic import BaseModel, Field
from datetime import datetime, timezone

from src.models.enums import PayOrderMode, PayOrderStatus


class PayOrderCreate(BaseModel):
    mode: PayOrderMode = Field(examples=[PayOrderMode.SALE], title="PayOrder mode")
    in_currency_id: str = Field(examples=["1-0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"])
    out_currency_id: Optional[str] = Field(examples=["30000000000001"]) # only for deposits
    out_amount: Optional[float] = Field(examples=[200]) # only for deposits
    out_address: Optional[str] = Field(examples=["9zUcFmUcdMwgH84vKofyL9xzULXh9F7uviNSYWb81f7e"])      # only for deposits

    refund_address: str = Field(examples=["0x311e128453EFd91a4c131761d9d535fF6E0EEF90"])            # refund address
    out_value_usd: Optional[float] = Field(examples=[250])  # only for sales
    metadata: Optional[dict] = Field(default_factory=dict, examples=[{
        "items": [{
            "name": "T-shirt",
            "description": "A cool t-shirt",
            "image": "https://example.com/tshirt.jpg",
            "price": 250,
        }]
    }])


class PayOrderResponse(BaseModel):
    id: str = Field(examples=["cm5h7ubkp0000v450cwvq6kc7"])
    mode: PayOrderMode = Field(examples=[PayOrderMode.SALE], title="PayOrder mode")
    status: PayOrderStatus = Field(examples=[PayOrderStatus.PENDING], title="PayOrder status")

    in_currency: Currency
    in_amount: float = Field(examples=[0.1])
    in_value_usd: float = Field(examples=[250])
    in_address: str = Field(examples=["0x311e128453EFd91a4c131761d9d535fF6E0EEF90"])

    out_currency: Optional[Currency]          # only for deposits
    out_amount: Optional[float]             # only for deposits
    out_value_usd: Optional[float]          # only for deposits
    out_address: Optional[str]              # only for deposits

    created_at: datetime
    expires_at: datetime
    metadata: dict = Field(default_factory=dict)
