# utils/currencies/types.py
from pydantic import BaseModel, Field, computed_field, field_validator
from typing import Optional, Union

from src.utils.types import ChainId

from src.utils.chains.types import Chain
from src.utils.chains.queries import get_chain_by_id

from decimal import Decimal

SEPARATOR_SYMBOL: str = "-"


class CurrencyBase(BaseModel):
    """Base class for all currencies.

    A CurrencyBase represents either:
    - A native blockchain currency (ETH, BTC, SOL etc.)
    - A token contract on a specific blockchain

    Attributes:
        address: The contract address, or None for native currencies
        chain_id: The blockchain's identifier where this currency exists

    The currency's unique identifier is constructed as:
        - For tokens: "{chain_id}-{lowercase_address}"
        - For native currencies: "{chain_id}"
    """

    # Fields
    address: Optional[str] = Field(
        default=None,
        description="Contract address, or None for native currencies",
    )
    chain_id: ChainId = Field(
        description="Identifier of the blockchain where this currency exists"
    )

    @field_validator("address")
    @classmethod
    def validate_address(cls, v: Optional[str]) -> Optional[str]:
        """Validate the address format.

        - Must not contain '-' character (used as separator in ID)
        - Converts to lowercase for consistency
        """
        if v is None:
            return None

        if SEPARATOR_SYMBOL in v:
            raise ValueError(f"Address cannot contain {SEPARATOR_SYMBOL} character")
        if v == "":
            return None

        return v.lower()  # normalize to lowercase

    @computed_field
    def id(self) -> str:
        """Generate the unique identifier for this currency."""
        if self.address:
            return f"{self.chain_id.value}{SEPARATOR_SYMBOL}{self.address}"
        return str(self.chain_id.value)

    @classmethod
    def from_id(cls, id: str) -> "CurrencyBase":
        """Create a CurrencyBase instance from its string identifier.

        Args:
            id: String in format "{chain_id}" or "{chain_id}-{address}"

        Returns:
            CurrencyBase instance

        Raises:
            ValueError: If the id format is invalid
        """

        if SEPARATOR_SYMBOL not in id:
            return cls(chain_id=ChainId(int(id)))
        parts = id.split(SEPARATOR_SYMBOL)
        if len(parts) == 1:
            return cls(chain_id=ChainId(int(parts[0])))
        else:
            chain_id, address = parts
            return cls(chain_id=ChainId(int(chain_id)), address=address)

    @classmethod
    def from_chain(cls, chain: Union[Chain, ChainId]) -> "CurrencyBase":
        """Create a Native CurrencyBase instance from a Chain instance or ChainId enum.

        Args:
            chain: Chain instance or ChainId enum

        Returns:
            CurrencyBase instance
        """

        if isinstance(chain, Chain):
            return cls(chain_id=chain.id, address=chain.nativeCurrency.address)

        _chain = get_chain_by_id(chain)
        return cls(chain_id=_chain.id, address=_chain.nativeCurrency.address)

    @property
    def chain(self) -> Chain:
        """Get the Chain instance for this currency's chain."""
        return get_chain_by_id(self.chain_id)

    @property
    def is_native(self) -> bool:
        """Whether this is a native blockchain currency."""

        address = self.address
        if address is not None:
            address = address.lower()

        native_currency_address = self.chain.nativeCurrency.address
        if native_currency_address is not None:
            native_currency_address = native_currency_address.lower()

        if address == native_currency_address:
            return True
        return False

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, CurrencyBase):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

    def __str__(self) -> str:
        return self.id


class Currency(CurrencyBase):
    name: str = Field(examples=["Wrapped Ethereum"], description="Currency name")
    ticker: str = Field(examples=["WETH"], description="Currency ticker symbol")
    decimals: int = Field(examples=[18], description="Number of decimal places")
    image: Optional[str] = Field(
        examples=["https://example.com/logo.png"],
        default=None,
        description="URL to currency logo",
    )
    price_usd: Optional[float] = Field(
        examples=[3400.0], default=None, description="Price in USD"
    )
    amount: Optional[int] = Field(
        examples=[1000000000000000000],
        default=None,
        description="Amount in smallest unit",
    )
    ui_amount: Optional[float] = Field(
        examples=[1.0], default=None, description="Amount in user-friendly unit"
    )
    balance: Optional[int] = Field(
        examples=[1000000000000000000],
        default=None,
        description="Balance in smallest unit",
    )
    ui_balance: Optional[float] = Field(
        examples=[1.0], default=None, description="Balance in user-friendly unit"
    )

    def __str__(self) -> str:
        return f"{self.ticker} ({self.name})"

    def amount_ui_to_raw(self, ui_amount: Union[float, Decimal]) -> int:
        return int(ui_amount * (10**self.decimals))

    def amount_raw_to_ui(self, amount: int) -> Decimal:
        """Convert the smallest unit amount to a user-friendly amount."""
        return Decimal(str(amount)) / Decimal(10) ** self.decimals
