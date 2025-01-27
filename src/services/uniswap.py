import os
import aiohttp
from aiocache import Cache, cached
from typing import Optional
from web3 import Web3

from src.utils.logging import get_logger
from src.utils.uniswap.ABI import uniswap_v2_Factory_ABI, uniswap_v2_router_ABI, uniswap_v2_pair_ABI
from src.utils.uniswap.types import NetworkId, NETWORK_ADDRESS

EVM_RPC_URL = os.getenv("EVM_RPC_URL")
if EVM_RPC_URL is None:
    raise ValueError("EVM_RPC_URL is not set")


logger = get_logger(__name__)

class UniswapService:
    """
    A service to fetch quotes from Uniswap on EVM.
    """
    def __init__(self, network_id: Optional[NetworkId] = NetworkId.MAINNET):
        self.w3 = Web3(
            Web3.HTTPProvider(EVM_RPC_URL))
        self.networkId = network_id
        self.factory_contract = self.w3.eth.contract(address=NETWORK_ADDRESS[network_id][0], abi=uniswap_v2_Factory_ABI)
        self.v2router_contract = self.w3.eth.contract(address=NETWORK_ADDRESS[network_id][1], abi=uniswap_v2_router_ABI)

    def _get_pair(self, token_a: str, token_b: str) -> str:
        pair_address = self.factory_contract.functions.getPair(token_a, token_b).call()
        return pair_address

    def _get_reserves(self, token_a: str, token_b: str):
        pair_address = self._get_pair(token_a, token_b)
        print('pair_address', pair_address)
        if not pair_address:
            raise ConnectionError(f"Failed to get pair address {pair_address}")
        pair_contract = self.w3.eth.contract(address=pair_address, abi=uniswap_v2_pair_ABI)
        reserves = pair_contract.functions.getReserves().call()
        print('reserves', reserves)
        print('reserves type', type(reserves))
        return reserves

    def _get_amount_out(self, amount: float, token_a: str, token_b: str):
        reserves = self._get_reserves(token_a, token_b)
        if not reserves:
            raise ConnectionError(f"Failed to get pair address {reserves}")
        print('reserves', type(reserves[0]))
        expected_out_amount = self.v2router_contract.functions.getAmountOut(amount, reserves[0], reserves[1]).call()
        print('expected_out_amount', expected_out_amount)
        return expected_out_amount


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
