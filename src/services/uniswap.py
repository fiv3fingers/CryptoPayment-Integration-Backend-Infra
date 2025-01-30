import os
import aiohttp
from aiocache import Cache, cached
from typing import Optional
from web3 import Web3

from src.utils.chains.queries import get_chain_by_id
from src.utils.logging import get_logger
from src.utils.types import ChainId, ServiceType
from src.utils.uniswap.ABI import uniswap_v2_Factory_ABI, uniswap_v2_router_ABI, uniswap_v2_pair_ABI, \
    uniswap_v3_Factory_ABI, uniswap_v3_quoter_ABI, uniswap_v3_pair_ABI
from src.utils.uniswap.types import CONTRACT_ADDRESS, V3QuoterAddress

ALCHEMY_API_KEY = os.getenv("ALCHEMY_API_KEY")
logger = get_logger(__name__)


class UniswapService:
    """
    A service to fetch quotes from Uniswap on EVM.
    """

    def __init__(self, chain_id: Optional[ChainId] = ChainId.ETH):
        chain = get_chain_by_id(chain_id)
        self.chain_name = chain.get_alias(ServiceType.UNISWAP)
        url = f"https://{self.chain_name}.g.alchemy.com/v2/{ALCHEMY_API_KEY}"
        self.w3 = Web3(
            Web3.HTTPProvider(url))
        self.networkId = chain_id
        self.v2factory_contract = self.w3.eth.contract(address=CONTRACT_ADDRESS[chain_id][0],
                                                       abi=uniswap_v2_Factory_ABI)
        self.v2router_contract = self.w3.eth.contract(address=CONTRACT_ADDRESS[chain_id][1], abi=uniswap_v2_router_ABI)
        self.v3factory_contract = self.w3.eth.contract(address=CONTRACT_ADDRESS[chain_id][2],
                                                       abi=uniswap_v3_Factory_ABI)
        self.v3quoter_contract = self.w3.eth.contract(address=V3QuoterAddress, abi=uniswap_v3_quoter_ABI)

    def _get_pair(self, token_a: str, token_b: str) -> str:
        pair_address = self.v2factory_contract.functions.getPair(token_a, token_b).call()
        return pair_address

    async def _get_pool(self, token_a: str, token_b: str) -> list:
        url = f"https://api.dexscreener.com/token-pairs/v1/{self.chain_name}/{token_a}"
        try:
            async with self.session.get(
                    url
            ) as response:
                response.raise_for_status()
                data = await response.json()
                return data
        except Exception as e:
            logger.error(f"Failed to get pool addresses from dexscreener {str(e)}")
            return []


    async def _get_amount_out(self, amount: float, token_a: str, token_b: str, sqrt_limit: int = 0):
        pools = await self._get_pool(token_a, token_b)
        quotes = []
        for pool in pools:
            labels = pool.get("labels", [])
            quote_token_addr = pool.get("quoteToken", {}).get("address", "").lower()
            if quote_token_addr == token_b.lower():
                if "v3" in labels:
                    pair_address = pool.get("pairAddress", "").lower()
                    pair_contract = self.w3.eth.contract(address=pair_address, abi=uniswap_v3_pair_ABI)
                    fee = pair_contract.functions.fee().call()
                    expected_out_amount = self.v3quoter_contract.functions.quoteExactOutputSingle(token_a, token_b, fee, amount, sqrt_limit)
                    quotes.append(expected_out_amount)
                elif "v2" in labels:
                    pair_address = self._get_pair(token_a, token_b)
                    if not pair_address:
                        logger.error(f"Failed to get pair address {pair_address}")
                        continue
                    pair_contract = self.w3.eth.contract(address=pair_address, abi=uniswap_v2_pair_ABI)
                    reserves = pair_contract.functions.getReserves().call()
                    if not reserves:
                        logger.error(f"Failed to get reserve {reserves}")
                        continue
                    expected_out_amount = self.v2router_contract.functions.getAmountOut(amount, reserves[0], reserves[1]).call()
                    quotes.append(expected_out_amount)
                else:
                    logger.error("No pool for this token pair")

        return min(quotes)

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
    async def get_quote(
            self,
            input_token: str,
            output_token: str,
            amount: int,
    ) -> float:

        if not self.session or self.session.closed:
            self.session = aiohttp.ClientSession()

        """Get a quote for a Uniswap"""
        amount_out = self._get_amount_out(amount, input_token, output_token)

        return amount_out
