from typing import List, Optional
from pydantic import BaseModel, Field, model_validator
from datetime import datetime

from src.utils.chains.queries import get_chain_by_id
from src.utils.currencies.types import Currency, CurrencyBase
from src.models.enums import PayOrderMode, PayOrderStatus
from src.utils.types import ChainId, ChainType


class MetadataItems(BaseModel):
    name: Optional[str] = Field(examples=["t-shirt"], default=None)
    description: Optional[str] = Field(examples=["A nice t-shirt"], default=None)
    image: Optional[str] = Field(
        examples=["https://example.com/image.png"], default=None
    )
    quantity: Optional[int] = Field(examples=[1], default=None)
    unit_price: Optional[float] = Field(examples=[0.1], default=None)
    currency: Optional[str] = Field(examples=["USD"], default=None)


class PayOrderMetadata(BaseModel):
    items: Optional[List[MetadataItems]] = Field(default_factory=list)


class CreatePayOrderRequest(BaseModel):
    """Request model for creating a PayOrder"""

    mode: PayOrderMode = Field(examples=[PayOrderMode.SALE], title="PayOrder mode")
    metadata: Optional[PayOrderMetadata] = Field(default_factory=PayOrderMetadata)
    destination_currency: Optional[CurrencyBase] = Field(
        examples=[
            {
                "address": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
                "chain_id": 30000000000001,
            }
        ],
        default=None,
        title="Destination currency",
    )
    destination_amount: Optional[float] = Field(
        examples=[0.01],
        default=None,
        title="Destination amount of currency tokens (UI amount)",
        ge=0,
    )
    destination_value_usd: Optional[float] = Field(
        examples=[269.42],
        default=None,
        title="Destination value in USD (for sale orders)",
        ge=0,
    )
    destination_receiving_address: Optional[str] = Field(
        examples=["0x311e128453EFd91a4c131761d9d535fF6E0EEF90"],
        default=None,
        title="Destination receiving address",
    )

    @model_validator(mode="before")
    @classmethod
    def validate_field_combinations(cls, values: dict) -> dict:
        mode = values.get("mode")
        dest_currency = values.get("destination_currency")
        dest_amount = values.get("destination_amount")
        dest_value_usd = values.get("destination_value_usd")
        dest_address = values.get("destination_receiving_address")

        if not dest_value_usd and not dest_amount:
            raise ValueError("destination_value_usd or destination_amount is required")

        if mode == PayOrderMode.DEPOSIT:
            # required dest_address, dest_currency and dest_value_usd or dest_amount
            if not dest_address:
                raise ValueError("[Deposit mode]: destination_receiving_address is required")
            if not dest_currency:
                raise ValueError("[Deposit mode]: destination_currency is required")
  
        if mode == PayOrderMode.SALE:
           if dest_amount and not dest_currency:
                raise ValueError("[Sale mode]: destination_amount should be combined with destination_currency")
      
        return values


class PayOrderResponse(BaseModel):
    """Response model for PayOrder"""

    id: str = Field(examples=["cm5h7ubkp0000v450cwvq6kc7"], title="PayOrder ID")
    mode: PayOrderMode = Field(examples=[PayOrderMode.DEPOSIT], title="PayOrder mode")
    status: PayOrderStatus = Field(
        examples=[PayOrderStatus.PENDING], title="PayOrder status"
    )

    metadata: Optional[PayOrderMetadata] = Field(
        default_factory=PayOrderMetadata, title="PayOrder metadata"
    )
    destination_amount: Optional[float] = Field(
        examples=[0.1], default=None, title="Destination amount (UI amount)"
    )
    destination_currency: Optional[Currency] = Field(
        default=None, title="Destination currency"
    )
    destination_value_usd: Optional[float] = Field(
        examples=[269.42], default=None, title="Destination value in USD"
    )


class CreateQuoteRequest(BaseModel):
    """Request model for creating a quote for a PayOrder"""

    wallet_address: str = Field(examples=["0x311e128453EFd91a4c131761d9d535fF6E0EEF90"])
    chain_type: ChainType = Field(examples=[ChainType.EVM])
    chain_ids: Optional[List[ChainId]] = Field(
        default=None, 
        examples=[[ChainId.ETH, ChainId.BASE]], 
        title="Chain IDs",
        description="Granular filtering by ChainId, mainly used for EVM chains"
    )

    @model_validator(mode="before")
    @classmethod
    def validate_field_combinations(cls, values: dict) -> dict:
        chain_type = values.get("chain_type")
        chain_ids = values.get("chain_ids")

        if chain_ids:
            for chain_id in chain_ids:
                chain = get_chain_by_id(chain_id)
                if chain.chain_type != chain_type:
                    raise ValueError(f"Chain {chain_id} is not an {chain_type} chain.")

        return values



class PaymentDetailsRequest(BaseModel):
    """Request model for creating payment details for a PayOrder"""

    source_currency: CurrencyBase = Field(
        examples=[
            {"address": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913", "chain_id": 8453}
        ]
    )
    refund_address: str = Field(examples=["0x311e128453EFd91a4c131761d9d535fF6E0EEF90"])


class PaymentDetailsResponse(BaseModel):
    """Response model for creating payment details for a PayOrder"""

    id: str = Field(examples=["cm5h7ubkp0000v450cwvq6kc7"])
    mode: PayOrderMode = Field(examples=[PayOrderMode.DEPOSIT], title="PayOrder mode")
    status: PayOrderStatus = Field(
        examples=[PayOrderStatus.PENDING], title="PayOrder status"
    )
    expires_at: datetime = Field(
        examples=["2025-01-24T18:37:31.430985+01:00"], title="PayOrder expiration date"
    )

    source_currency: Currency
    deposit_address: str = Field(
        examples=["0x311e128453EFd91a4c131761d9d535fF6E0EEF90"]
    )
    refund_address: str = Field(examples=["0x311e128453EFd91a4c131761d9d535fF6E0EEF90"])

    # Deposits Only
    destination_currency: Optional[Currency] = Field(default=None)
    destination_receiving_address: Optional[str] = Field(default=None)


class ProcessPaymentResponse(BaseModel):
    """Response model for processing a payment for a PayOrder"""

    deposit_tx_hash: Optional[str] = Field(
        default=None,
        examples=["0xbc0c9c8646c6cd5e6225ecc8dfc54259bcc586c6c5fe46810f4ea98c6adaae59"]
    )
    status: PayOrderStatus = Field(
        examples=[PayOrderStatus.PENDING], title="PayOrder status"
    )
