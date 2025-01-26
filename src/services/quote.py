import asyncio
from typing import List, TypeVar, Sequence, Union
from dataclasses import dataclass
from decimal import Decimal

from src.utils.currencies.helpers import to_currency_base
from src.utils.currencies.types import Currency, CurrencyBase
from src.utils.logging import get_logger
from src.services.changenow import ChangeNowService, ExchangeType
from src.services.coingecko import CoinGeckoService
from src.utils.types import ChainId

logger = get_logger(__name__)

CurrencyType = TypeVar("CurrencyType", str, CurrencyBase, Currency)


@dataclass
class CurrencyQuote:
    """Represents a currency exchange quote."""

    source_currency: Currency
    destination_currency: Currency

    @property
    def source_value_usd(self) -> float:
        """Calculate the USD value of the source amount."""
        if not self.source_currency.price_usd:
            raise ValueError(f"Price not available for {self.source_currency.id}")
        if not self.source_currency.ui_amount:
            raise ValueError("Source amount not set")
        return self.source_currency.ui_amount * self.source_currency.price_usd

    @property
    def destination_value_usd(self) -> float:
        """Calculate the USD value of the destination amount."""
        if not self.destination_currency.price_usd:
            raise ValueError(f"Price not available for {self.destination_currency.id}")
        if not self.destination_currency.ui_amount:
            raise ValueError("Destination amount not set")
        return self.destination_currency.ui_amount * self.destination_currency.price_usd

    def __str__(self) -> str:
        """Human-readable representation of the quote."""
        return (
            f"{self.source_currency.ui_amount} {self.source_currency.ticker} "
            f"({self.source_value_usd:.2f} USD) → "
            f"{self.destination_currency.ui_amount} {self.destination_currency.ticker} "
            f"({self.destination_value_usd:.2f} USD)"
        )


class QuoteService:
    """Service for getting cryptocurrency exchange quotes.

    It supports quoting by either USD value or specific cryptocurrency amounts.
    """

    def __init__(self):
        self.coingecko = CoinGeckoService()
        self.changenow = ChangeNowService()

    async def __aenter__(self):
        """Set up external service connections."""
        await self.coingecko.__aenter__()
        await self.changenow.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Clean up external service connections."""
        await self.coingecko.__aexit__(exc_type, exc_val, exc_tb)
        await self.changenow.__aexit__(exc_type, exc_val, exc_tb)

    async def _fetch_currency_prices(
        self, currencies: Sequence[CurrencyType]
    ) -> List[Currency]:
        """Fetch prices for a list of currencies using CoinGecko."""
        currency_bases = [to_currency_base(c) for c in currencies]
        return await self.coingecko.price(currencies=currency_bases)

    async def _get_exchange_estimate(
        self,
        source_currency: Currency,
        destination_currency: Currency,
        destination_amount: Decimal,
    ) -> CurrencyQuote:
        """Get an exchange estimate for a currency pair.

        Uses ChangeNow to estimate how much source currency is needed for the
        desired destination amount.
        """
        if not destination_currency.price_usd:
            raise ValueError(f"Price not available for {destination_currency.id}")

        try:
            source_amount = await self.changenow.estimate(
                currency_in=source_currency,
                currency_out=destination_currency,
                amount=destination_amount,
                exchange_type=ExchangeType.REVERSE,
            )

            # Update currency objects with amounts
            source_currency.ui_amount = source_amount
            source_currency.amount = source_currency.amount_ui_to_raw(source_amount)
            destination_currency.ui_amount = float(destination_amount)
            destination_currency.amount = destination_currency.amount_ui_to_raw(
                destination_amount
            )

            return CurrencyQuote(
                source_currency=source_currency,
                destination_currency=destination_currency,
            )

        except Exception as e:
            logger.error(
                f"Error estimating {source_currency.id} to {destination_currency.id}: {str(e)}"
            )
            raise

    async def _get_best_quote(
        self,
        source_currency: Currency,
        destination_currencies: List[Currency],
        destination_value_usd: float,
    ) -> CurrencyQuote:
        """Find the best quote among multiple destination currencies.

        Returns the quote requiring the lowest source currency amount in USD terms.
        """
        quotes = []

        tasks = []
        for dest_currency in destination_currencies:
            if not dest_currency.price_usd:
                logger.warning(f"Price not available for {dest_currency.id}")
                continue

            dest_amount = Decimal(str(destination_value_usd / dest_currency.price_usd))
            task = self._get_exchange_estimate(
                source_currency=source_currency,
                destination_currency=dest_currency,
                destination_amount=dest_amount,
            )
            tasks.append(task)

        if not tasks:
            raise ValueError("No viable destination currencies found")

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter successful quotes
        for result in results:
            if isinstance(result, BaseException):
                logger.error(f"Exchange estimation failed: {str(result)}")
                continue
            quotes.append(result)

        if not quotes:
            raise ValueError("No quotes available")

        # Return quote with lowest source USD value
        return min(quotes, key=lambda q: q.source_value_usd)

    async def quote_usd(
        self,
        source_currencies: List[CurrencyType],
        destination_currencies: List[CurrencyType],
        destination_value_usd: float,
    ) -> List[CurrencyQuote]:
        """Get quotes based on a desired USD value.

        For each source currency, finds the best destination currency that will
        provide the desired USD value for the lowest input cost.
        """
        src_currencies, dest_currencies = await asyncio.gather(
            self._fetch_currency_prices(source_currencies),
            self._fetch_currency_prices(destination_currencies),
        )

        # Get best quote for each source currency
        quote_tasks = [
            self._get_best_quote(
                source_currency=src_cur,
                destination_currencies=dest_currencies,
                destination_value_usd=destination_value_usd,
            )
            for src_cur in src_currencies
        ]

        results = await asyncio.gather(*quote_tasks, return_exceptions=True)

        # Filter successful quotes
        return [quote for quote in results if not isinstance(quote, BaseException)]

    async def quote(
        self,
        source_currencies: List[CurrencyType],
        destination_currency: CurrencyType,
        destination_ui_amount: Union[float, Decimal],
    ) -> List[CurrencyQuote]:
        """Get quotes based on a desired destination amount.

        For each source currency, estimates how much would be needed to obtain
        the specified amount of the destination currency.
        """
        src_currencies, [dest_currency] = await asyncio.gather(
            self._fetch_currency_prices(source_currencies),
            self._fetch_currency_prices([destination_currency]),
        )

        quote_tasks = [
            self._get_exchange_estimate(
                source_currency=src_cur,
                destination_currency=dest_currency,
                destination_amount=destination_ui_amount,
            )
            for src_cur in src_currencies
        ]

        results = await asyncio.gather(*quote_tasks, return_exceptions=True)

        # Filter successful quotes
        return [quote for quote in results if not isinstance(quote, BaseException)]
