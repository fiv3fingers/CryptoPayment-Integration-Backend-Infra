from typing import Dict, Optional, List, Union
import os
import logging
import asyncio
import aiohttp
from aiocache import Cache, cached
from aiocache.serializers import PickleSerializer

from src.utils.types import ServiceType, ChainId
from src.utils.currencies.types import Currency, CurrencyBase
from src.utils.coingecko.types import Price, VSCurrency, PriceParams, TokenInfo

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

logger = logging.getLogger(__name__)


class CoinGeckoError(Exception):
    """Base exception for CoinGecko service errors."""

    pass


class RateLimitError(CoinGeckoError):
    """Raised when rate limit is reached."""

    pass


class CoinGeckoService:
    """Service wrapper around CoinGecko API with caching."""

    BASE_URL = "https://pro-api.coingecko.com/api/v3"

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the CoinGecko service.

        Args:
            api_key: Optional API key for CoinGecko Pro
        """
        self.api_key = os.getenv("COINGECKO_API_KEY") if not api_key else api_key
        self.session = None
        self.headers = {"accept": "application/json"}
        if self.api_key:
            self.headers["x-cg-pro-api-key"] = self.api_key

        # Initialize cache
        self.cache = Cache(Cache.MEMORY)

    async def __aenter__(self):
        """Context manager entry."""

        if not self.session or self.session.closed:
            self.session = aiohttp.ClientSession(headers=self.headers)

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        if self.session and not self.session.closed:
            await self.session.close()

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=60, max=90),
        retry=retry_if_exception_type((aiohttp.ClientError, RateLimitError)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
    )
    @cached(
        ttl=24 * 60 * 60,
        cache=Cache.MEMORY,
        serializer=PickleSerializer(),
        key_builder=lambda f, self, chain_id, address: f"_get_token_info:{chain_id}-{address}",
    )
    async def _get_token_info(
        self, chain_id: ChainId, address: str
    ) -> Optional[TokenInfo]:
        """
        Get token info with caching.

        Args:
            chain_id: Chain ID of the token
            address: Token address
        """
        if not self.session:
            self.session = aiohttp.ClientSession(headers=self.headers)

        try:
            currency = CurrencyBase(chain_id=chain_id, address=address)

            if currency.is_native:
                token_id = currency.chain.nativeCurrency.get_alias(
                    ServiceType.COINGECKO
                )
                url = f"{self.BASE_URL}/coins/{token_id}"
            else:
                platform_id = currency.chain.get_alias(ServiceType.COINGECKO)
                url = f"{self.BASE_URL}/coins/{platform_id}/contract/{address}"

            async with self.session.get(url) as response:
                if response.status == 429:
                    print(
                        f"Rate limit reached: {response.headers}\n{await response.text()}"
                    )
                    raise RateLimitError("Rate limit reached")
                elif response.status == 404:
                    return None
                elif response.status >= 400:
                    print(
                        f"API error: {response.status}\n{await response.text()}\nheaders: {response.headers}"
                    )
                    raise CoinGeckoError(f"API error: {response.status}")

                response.raise_for_status()
                data = await response.json()
                return TokenInfo(**data)

        except Exception as e:
            logger.error(f"Error fetching token info: {e}")
            raise

    @cached(
        ttl=24 * 60 * 60,
        cache=Cache.MEMORY,
        key_builder=lambda f, self, chain_id, address: f"_get_coingecko_id:{chain_id}-{address}",
    )
    async def _get_coingecko_id(self, chain_id: ChainId, address: str) -> Optional[str]:
        """
        Get CoinGecko ID with caching.

        Args:
            chain_id: Chain ID of the token
            address: Token address
        """
        token_info = await self._get_token_info(chain_id, address)
        if token_info:
            return token_info.id
        return None

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=60, max=90),
        retry=retry_if_exception_type((aiohttp.ClientError, RateLimitError)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
    )
    @cached(
        ttl=300,
        cache=Cache.MEMORY,
        serializer=PickleSerializer(),
        key_builder=lambda f, self, ids, vs_currency, precision: f"_get_prices:{'@'.join(ids)}@{vs_currency}@{precision}",
    )
    async def _get_prices(
        self,
        ids: tuple[str, ...],
        vs_currency: VSCurrency = VSCurrency.USD,
        precision: Optional[int] = 8,
    ) -> Dict[str, Price]:
        """
        Get prices with caching.

        Args:
            ids: Tuple of CoinGecko IDs
            vs_currency: Currency to get prices in
            precision: Price precision
        """
        if not self.session:
            self.session = aiohttp.ClientSession(headers=self.headers)

        try:
            params = PriceParams(
                ids=list(ids),
                include_market_cap=False,
                include_24hr_vol=False,
                include_24hr_change=False,
                include_last_updated_at=True,
                precision=precision,
                vs_currencies=[vs_currency],
            )

            async with self.session.get(
                f"{self.BASE_URL}/simple/price", params=params.to_query_params()
            ) as response:
                if response.status == 429:
                    raise RateLimitError("Rate limit reached")
                elif response.status >= 400:
                    raise CoinGeckoError(f"API error: {response.status}")

                response.raise_for_status()
                data = await response.json()

                result = {}
                for id in ids:
                    coin_data = data.get(id, {})
                    if not coin_data:
                        continue

                    price = coin_data.get(vs_currency.value)
                    last_updated_at = coin_data.get("last_updated_at")

                    result[id] = Price(
                        currency_id=id,
                        price=price,
                        vs_currency=vs_currency,
                        last_updated_at=last_updated_at,
                    )
                return result

        except Exception as e:
            logger.error(f"Error fetching prices: {e}")
            raise

    async def get_token_info(
        self, currency: Union[Currency, CurrencyBase, str]
    ) -> Optional[Currency]:
        """
        Get detailed information about a token.

        Args:
            currency: Currency or CurrencyBase object or currency ID
        """
        if isinstance(currency, str):
            currency = CurrencyBase.from_id(currency)

        token_info = await self._get_token_info(currency.chain_id, currency.address)

        if token_info:
            platform_id = token_info.asset_platform_id

            try:
                detail_platform = token_info.detail_platforms.get(platform_id)
                decimals = None
                if detail_platform:
                    decimals = detail_platform.decimal_place
                if decimals is None and currency.is_native:
                    decimals = currency.chain.nativeCurrency.decimals
                if decimals is None:
                    return None

                return Currency(
                    chain_id=currency.chain_id,
                    address=currency.address,
                    name=token_info.name,
                    ticker=token_info.symbol,
                    decimals=decimals,
                    image=token_info.image.small,
                )
            except Exception as e:
                logger.error(f"Error creating Currency object: {e}")
                return None

        return None

    async def get_prices(
        self,
        currencies: Union[List[Currency], List[CurrencyBase]],
        vs_currency: VSCurrency = VSCurrency.USD,
        precision: Optional[int] = 8,
    ) -> List[Price]:
        """
        Get current prices for currencies.

        Args:
            currencies: List of currencies to get prices for
            vs_currency: Currency to get prices in
            precision: Price precision
        """
        # First, get all CoinGecko IDs (cached)
        id_currencies = []
        id_tasks = [
            self._get_coingecko_id(currency.chain_id, currency.address)
            for currency in currencies
        ]

        cg_ids = await asyncio.gather(*id_tasks)
        id_currencies = [
            (cg_id, currency) for cg_id, currency in zip(cg_ids, currencies) if cg_id
        ]

        if not id_currencies:
            return []

        # Get prices (cached)
        coin_ids = tuple(id_ for id_, _ in id_currencies)
        prices_dict = await self._get_prices(coin_ids, vs_currency, precision)

        # Format results
        result = []
        for cg_id, currency in id_currencies:
            if price := prices_dict.get(cg_id):
                result.append(
                    Price(
                        currency_id=currency.id,
                        price=price.price,
                        vs_currency=vs_currency,
                        last_updated_at=price.last_updated_at,
                    )
                )

        return result

    async def price(
        self,
        currencies: List[Union[Currency, CurrencyBase]],
        vs_currency: VSCurrency = VSCurrency.USD,
        precision: Optional[int] = 8,
    ) -> List[Currency]:
        """
        Get current prices for currencies.

        Args:
            currencies: List of currencies to get prices for
            vs_currency: Currency to get prices in
            precision: Price precision
        """
        # Use asyncio.gather to parallelize token info requests
        _currencies = await asyncio.gather(
            *[self.get_token_info(currency) for currency in currencies]
        )
        _currencies = [c for c in _currencies if c is not None]

        if not _currencies:
            return []

        # Get all prices in one request
        _prices = await self.get_prices(_currencies, vs_currency, precision)

        # Update prices efficiently
        for c in _currencies:
            c.price_usd = next(
                (p.price for p in _prices if p.currency_id == c.id), None
            )

        return _currencies
