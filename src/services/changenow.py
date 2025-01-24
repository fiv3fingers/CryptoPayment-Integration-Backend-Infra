from typing import Optional, List, Union
import os
import aiohttp
from aiocache import Cache, cached

from src.utils.types import ServiceType
from src.utils.currencies.types import Currency, CurrencyBase
from src.utils.changenow.types import (
    ChangeNowCurrency,
    EstimateRequest,
    Estimate,
    ExchangeRequest,
    Exchange,
    ExchangeType,
    ExchangeStatus,
    Flow
)
from ..utils.logging import get_logger

logger = get_logger(__name__)

def get_currencies_cache_key(
    _,
    self,
    active: Optional[bool] = None,
    flow: Optional[str] = "standard",
    buy: Optional[bool] = None,
    sell: Optional[bool] = None
) -> str:
    """Build cache key for available currencies."""
    key_parts = ["currencies"]
    if active is not None:
        key_parts.append(f"active={str(active).lower()}")
    if flow:
        key_parts.append(f"flow={flow}")
    if buy is not None:
        key_parts.append(f"buy={str(buy).lower()}")
    if sell is not None:
        key_parts.append(f"sell={str(sell).lower()}")
    return ":".join(key_parts)

def get_estimate_cache_key(_, self, request: EstimateRequest) -> str:
    """Build cache key for estimates."""
    return f"estimate:{request.from_currency}:{request.to_currency}:{request.from_network}:{request.to_network}:{request.from_amount}:{request.flow}:{request.type}"

def get_currency_cache_key(_, self, currency: Union[Currency, CurrencyBase]) -> str:
    """Build cache key for ChangeNow currency lookup."""
    return f"cn_currency:{currency.id}"



class ChangeNowService:
    """ChangeNow API service with caching."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize ChangeNow service."""
        self.api_key = api_key or os.getenv('CHANGENOW_API_KEY')
        if not self.api_key:
            raise ValueError("API key must be provided or set in CHANGENOW_API_KEY environment variable")

        self.base_url = "https://api.changenow.io/v2"
        self.headers = {
            'Content-Type': 'application/json',
            'x-changenow-api-key': self.api_key
        }
        self.session = None
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

    @cached(
        ttl=900,  # 15 minutes
        cache=Cache.MEMORY,
        key_builder=get_currencies_cache_key
    )
    async def get_available_currencies(
        self,
        active: Optional[bool] = None,
        flow: Optional[str] = "standard",
        buy: Optional[bool] = None,
        sell: Optional[bool] = None,
    ) -> List[ChangeNowCurrency]:
        """Get available currencies with caching."""
        if not self.session or self.session.closed:
            self.session = aiohttp.ClientSession(headers=self.headers)

        try:
            params = {}
            if active is not None:
                params['active'] = str(active).lower()
            if flow:
                params['flow'] = flow
            if buy is not None:
                params['buy'] = str(buy).lower()
            if sell is not None:
                params['sell'] = str(sell).lower()

            logger.debug(f"Fetching available currencies with params: {params}")

            async with self.session.get(
                f"{self.base_url}/exchange/currencies",
                params=params
            ) as response:
                response.raise_for_status()
                data = await response.json()
                return [ChangeNowCurrency.model_validate(currency) for currency in data]
        except Exception as e:
            logger.error(f"Error fetching available currencies: {e}")
            raise

    @cached(
        ttl=60,  # 1 minute
        cache=Cache.MEMORY,
        key_builder=get_estimate_cache_key
    )
    async def _create_estimate(self, request: EstimateRequest) -> Estimate:
        """Get exchange estimate with caching."""
        if not self.session or self.session.closed:
            self.session = aiohttp.ClientSession(headers=self.headers)

        try:
            params = request.to_api_params()

            async with self.session.get(
                f"{self.base_url}/exchange/estimated-amount",
                params=params
            ) as response:
                response.raise_for_status()
                data = await response.json()
                return Estimate.model_validate(data)
        except Exception as e:
            logger.error(f"Error creating estimate: {e}")
            raise

    async def _create_exchange(self, request: ExchangeRequest) -> Exchange:
        """Create exchange transaction."""
        if not self.session or self.session.closed:
            self.session = aiohttp.ClientSession(headers=self.headers)

        try:
            data = request.model_dump(by_alias=True, exclude_none=True)
            data["fromAmount"] = f"{float(data['fromAmount']):.5f}"

            logger.debug(f"Creating exchange with data: {data}")

            async with self.session.post(
                f"{self.base_url}/exchange",
                json=data
            ) as response:
                response.raise_for_status()
                data = await response.json()
                return Exchange.model_validate(data)
        except Exception as e:
            logger.error(f"Error creating exchange: {e}")
            raise

    async def _get_exchange_status(self, exchange_id: str) -> ExchangeStatus:
        """Get exchange status."""
        if not self.session or self.session.closed:
            self.session = aiohttp.ClientSession(headers=self.headers)

        try:
            async with self.session.get(
                f"{self.base_url}/exchange/by-id",
                params={"id": exchange_id}
            ) as response:
                response.raise_for_status()
                data = await response.json()
                return ExchangeStatus.model_validate(data)
        except Exception as e:
            logger.error("Error getting exchange status: %s", e)
            raise

    @cached(
        ttl=900,  # 15 minutes
        cache=Cache.MEMORY,
        key_builder=get_currency_cache_key
    )
    async def _get_changenow_currency(self, currency: Union[Currency, CurrencyBase]) -> ChangeNowCurrency:
        """Get ChangeNow currency with caching."""
        try:
            network_name = currency.chain.get_alias(ServiceType.CHANGENOW)

            cn_currencies = await self.get_available_currencies()
            relevant_currencies = [c for c in cn_currencies if c.network == network_name]

            if not relevant_currencies:
                raise ValueError(f"No currencies found for network {network_name}")

            if currency.is_native:
                result = next((c for c in relevant_currencies if c.token_contract is None), None)
            else:
                result = next((c for c in relevant_currencies if c.token_contract and c.token_contract.lower() == currency.address.lower()), None)

            if not result:
                raise ValueError(f"Currency {currency} not found")

            return result
        except Exception as e:
            #logger.error(f"Error getting ChangeNow currency: {e}")
            raise

    async def is_supported(self, currency: Union[Currency, CurrencyBase, str]) -> bool:
        if isinstance(currency, str):
            currency = CurrencyBase.from_id(currency)

        try:
            cn_currency = await self._get_changenow_currency(currency)
            return cn_currency is not None
        except Exception:
            return False

    async def estimate(
        self,
        currency_in: Union[Currency, CurrencyBase],
        currency_out: Union[Currency, CurrencyBase],
        amount: float,
        exchange_type: ExchangeType = ExchangeType.DIRECT,
    ) -> float:
        """Get exchange estimate."""
        try:
            cn_currency_in = await self._get_changenow_currency(currency_in)
            cn_currency_out = await self._get_changenow_currency(currency_out)

            if exchange_type == ExchangeType.DIRECT:
                est = await self._create_estimate(EstimateRequest(
                    from_currency=cn_currency_in.ticker,
                    to_currency=cn_currency_out.ticker,
                    from_network=cn_currency_in.network,
                    to_network=cn_currency_out.network,
                    from_amount=amount,
                    flow=Flow.STANDARD,
                    type=ExchangeType.DIRECT
                ))
                return est.to_amount
            if exchange_type == ExchangeType.REVERSE:
                est = await self._create_estimate(EstimateRequest(
                    from_currency=cn_currency_in.ticker,
                    to_currency=cn_currency_out.ticker,
                    from_network=cn_currency_in.network,
                    to_network=cn_currency_out.network,
                    to_amount=amount,
                    flow=Flow.FIXED,
                    type=ExchangeType.REVERSE
                ))
                return est.from_amount

            raise ValueError(f"Invalid exchange type {exchange_type}")
        except Exception as e:
            logger.error(f"Error estimating exchange: {e}")
            raise

    async def exchange(
        self,
        currency_in: Union[Currency, CurrencyBase],
        currency_out: Union[Currency, CurrencyBase],
        amount: float,
        address: str,
        refund_address: str,
        exchange_type: ExchangeType = ExchangeType.DIRECT,
    ) -> Exchange:
        """Create exchange transaction."""
        try:
            cn_currency_in = await self._get_changenow_currency(currency_in)
            cn_currency_out = await self._get_changenow_currency(currency_out)

            if exchange_type == ExchangeType.DIRECT:
                return await self._create_exchange(ExchangeRequest(
                    from_currency=cn_currency_in.ticker,
                    to_currency=cn_currency_out.ticker,
                    from_network=cn_currency_in.network,
                    to_network=cn_currency_out.network,
                    from_amount=amount,
                    address=address,
                    refund_address=refund_address,
                    flow=Flow.STANDARD,
                    type=ExchangeType.DIRECT
                ))
            if exchange_type == ExchangeType.REVERSE:
                return await self._create_exchange(ExchangeRequest(
                    from_currency=cn_currency_out.ticker,
                    to_currency=cn_currency_in.ticker,
                    from_network=cn_currency_out.network,
                    to_network=cn_currency_in.network,
                    from_amount=amount,
                    address=address,
                    refund_address=refund_address,
                    flow=Flow.STANDARD,
                    type=ExchangeType.REVERSE
                ))
        except Exception as e:
            logger.error(f"Error creating exchange: {e}")
            raise
