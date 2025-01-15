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
from datetime import datetime

from src.models.enums import PayOrderMode, PayOrderStatus

from enum import Enum


class PayOrderCreate(BaseModel):
    mode: PayOrderMode
    in_currency_id: str
    out_currency_id: Optional[str]  # only for deposits
    out_amount: Optional[float]     # only for deposits
    out_address: Optional[str]      # only for deposits

    refund_address: str             # refund address
    out_value_usd: Optional[float]  # only for sales
    metadata: Optional[dict] = Field(default_factory=dict)


class PayOrderResponse(BaseModel):
    id: str
    mode: PayOrderMode
    status: PayOrderStatus

    in_currency: Currency
    in_amount: float
    in_value_usd: float
    in_address: str

    out_currency: Optional[Currency]          # only for deposits
    out_amount: Optional[float]             # only for deposits
    out_value_usd: Optional[float]          # only for deposits
    out_address: Optional[str]              # only for deposits

    created_at: datetime
    expires_at: datetime
    metadata: dict = Field(default_factory=dict)
