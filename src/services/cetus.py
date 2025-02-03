import os
import aiohttp
from typing import Dict, Any, Optional, Union
from aiocache import Cache, cached

from ..utils.chains.queries import get_chain_by_id
from ..utils.currencies.types import Currency, CurrencyBase
from ..utils.logging import get_logger
from ..utils.types import ChainId, ServiceType

logger = get_logger(__name__)


class CetusService:
    """
    A service to fetch quotes from Jupiter Aggregator on Solana.
    """

    def __init__(self, chain_id: ChainId):
        chain = get_chain_by_id(chain_id)
        self.chain_name = chain.get_alias(ServiceType.UNISWAP)
        self.decimal = chain.nativeCurrency.decimals
        self.router_url = "https://api-sui.cetus.zone/router"
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Context manager entry - create aiohttp session if needed."""
        if not self.session or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close session."""
        if self.session and not self.session.closed:
            await self.session.close()

    @cached(
        ttl=900,
        cache=Cache.MEMORY,
    )
    async def get_quote(
            self,
            currency_in: CurrencyBase,
            currency_out: CurrencyBase,
            amount: int,
            by_amount_in: bool = False,
            order_split: bool = False,
            external_router: bool = False,
            request_id: str = None
    ) -> float:

        if not self.session or self.session.closed:
            self.session = aiohttp.ClientSession()

        params = {
            "from": currency_in.address,
            "to": currency_out.address,
            "amount": amount,
            "by_amount_in": by_amount_in,
            "order_split": order_split,
            "external_router": external_router,
            "request_id": request_id
        }

        print("param", params)

        async with self.session.get(self.router_url, params=params) as response:
            response.raise_for_status()
            data = await response.json()
            print("res data", data)
            return data.get("input_amount")
