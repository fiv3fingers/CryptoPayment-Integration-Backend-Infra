from pydantic import BaseModel, Field, computed_field, field_validator, ConfigDict, model_validator
from typing import Optional, Union, ClassVar
from decimal import Decimal

from src.utils.types import ChainId
from src.utils.chains.types import Chain
from src.utils.chains.queries import get_chain_by_id

SEPARATOR_SYMBOL: str = "-"

class CurrencyAmount(BaseModel):
    ui_amount: float = Field(examples=[0.1], description="Amount of currency tokens (UI amount)")
    raw_amount: int = Field(examples=[100000000000000000], description="Amount of currency tokens (raw amount)")
    value_usd: Optional[float] = Field(examples=[269.42], default=None, description="Amount of value in USD")

    @field_validator("value_usd")
    @classmethod
    def validate_ticker(cls, v: Optional[float]) -> Optional[float]:
        """ Normalize value to two decimal places."""

        if v is None:
            return None
        return round(v, 2)


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
    """Full currency information including metadata.
    
    Represents a blockchain currency with complete information including
    name, ticker symbol, decimals, and optional price data.
    """
    model_config = ConfigDict(
        validate_default=True,
        arbitrary_types_allowed=True,
        str_strip_whitespace=True
    )
    
    # Constants
    MAX_DECIMALS: ClassVar[int] = 18
    DEFAULT_DISPLAY_DECIMALS: ClassVar[int] = 8

    # Required fields
    name: str = Field(description="Full currency name")
    ticker: str = Field(description="Ticker symbol")
    decimals: int = Field(description="Number of decimal places", ge=0, le=MAX_DECIMALS)

    # Optional fields
    image_uri: Optional[str] = Field(default=None, description="URI for currency logo")
    price_usd: Optional[float] = Field(default=None, description="Current USD price")

    @field_validator("ticker")
    @classmethod
    def validate_ticker(cls, v: str) -> str:
        """Normalize ticker to uppercase."""
        return v.upper()

    def _calculate_ui_amount_precision(self) -> int:
        """Calculate optimal display precision based on price."""
        if not self.price_usd or self.price_usd <= 0:
            return min(self.decimals, self.DEFAULT_DISPLAY_DECIMALS)

        one_cent_in_raw = (10 ** self.decimals / self.price_usd) / 100
        
        for precision in range(self.decimals + 1):
            unit = 10 ** (self.decimals - precision)
            if unit <= one_cent_in_raw:
                return max(precision, self.DEFAULT_DISPLAY_DECIMALS)

                
        return max(self.DEFAULT_DISPLAY_DECIMALS, self.decimals)

    def with_price(self, price_usd: Optional[float]) -> "Currency":
        """Create new instance with updated price."""
        return self.model_copy(update={"price_usd": price_usd})

    def _amount_from_usd(self, value_usd: float, precision: int) -> CurrencyAmount:
        """Initialize from USD value."""
        if self.price_usd is None:
            raise ValueError("Price not available for currency")

        _ui_amount = float(f"{value_usd / self.price_usd:.{precision}f}")
        _raw_amount = int(Decimal(str(_ui_amount)) * (10 ** self.decimals))
        _value_usd = value_usd

        return CurrencyAmount(
            ui_amount=_ui_amount,
            raw_amount=_raw_amount,
            value_usd=_value_usd
        )

    def _amount_from_raw(self, raw_amount: int, precision: int) -> CurrencyAmount:
        """Initialize from raw amount."""
        _raw_amount = raw_amount
        _ui_amount = float(f"{Decimal(str(raw_amount)) / Decimal(10 ** self.decimals):.{precision}f}")
        _value_usd = _ui_amount * self.price_usd if self.price_usd else None

        return CurrencyAmount(
            ui_amount=_ui_amount,
            raw_amount=_raw_amount,
            value_usd=_value_usd
        )

    def _amount_from_ui(self, ui_amount: Union[float, Decimal], precision: int) -> CurrencyAmount:
        """Initialize from UI amount."""
        _ui_amount = float(f"{ui_amount:.{precision}f}")
        _raw_amount = int(Decimal(str(ui_amount)) * (10 ** self.decimals))
        _value_usd = _ui_amount * self.price_usd if self.price_usd else None

        return CurrencyAmount(
            ui_amount=_ui_amount,
            raw_amount=_raw_amount,
            value_usd=_value_usd
        )


    def amount(self, ui_amount: Optional[Union[float, Decimal]] = None, 
               raw_amount: Optional[int] = None, 
               value_usd: Optional[float] = None) -> CurrencyAmount:
        """Create a CurrencyAmount instance for this currency."""
        precision = self._calculate_ui_amount_precision()

        if ui_amount is not None:
            return self._amount_from_ui(ui_amount, precision)
        
        if raw_amount is not None:
            return self._amount_from_raw(raw_amount, precision)
        
        if value_usd is not None:
            return self._amount_from_usd(value_usd, precision)

        raise ValueError("One of ui_amount, raw_amount, or value_usd must be provided")

