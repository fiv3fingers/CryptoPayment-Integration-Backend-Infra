import os
import aiohttp
from typing import Dict, Any, Optional
from aiocache import Cache, cached
from ..utils.logging import get_logger

logger = get_logger(__name__)


class JupiterService:
    """
    A service to fetch quotes from Jupiter Aggregator on Solana.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.base_url = "https://quote-api.jup.ag/v6/"
        self.quote_url = "https://quote-api.jup.ag/v6/quote/"
        self.swap_url = "https://quote-api.jup.ag/v6/swap/"
        self.token_url = "https://tokens.jup.ag/"
        self.api_key = api_key or os.getenv("JUPITER_API_KEY")
        """No need api key on dev mode"""
        # if not self.api_key:
        #     raise ValueError("API key must be provided or set in JUPITER_API_KEY environment variable")

        self.base_url = "https://tokens.jup.ag/"
        self.headers = {"Content-Type": "application/json", "x-api-key": self.api_key}
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
        ttl=900,  # 15 minutes
        cache=Cache.MEMORY,
    )
    async def estimate(
        self,
        input_token: str,
        output_token: str,
        amount: int,
        slippage_bps: int = 50,
        only_direct_routes: bool = False,
    ) -> float:

        if not self.session or self.session.closed:
            self.session = aiohttp.ClientSession()

        params = {
            "inputMint": input_token,
            "outputMint": output_token,
            "amount": amount,
            "slippageBps": slippage_bps,
            "onlyDirectRoutes": str(only_direct_routes).lower(),
        }

        async with self.session.get(self.quote_url, params=params) as response:
            # Raise an HTTPError if status != 200
            response.raise_for_status()
            data = await response.json()
            return data.get("outAmount")
