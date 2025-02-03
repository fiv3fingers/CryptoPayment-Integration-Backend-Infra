import os
import aiohttp
import asyncio
from aiocache import Cache, cached
from typing import Optional, Union
from eth_utils import to_checksum_address
from web3 import Web3, AsyncWeb3

from src.utils.chains.queries import get_chain_by_id
from src.utils.currencies.types import Currency, CurrencyBase
from src.utils.logging import get_logger
from src.utils.types import ChainId, ServiceType
from src.utils.uniswap.ABI import uniswap_v2_Factory_ABI, uniswap_v2_router_ABI, uniswap_v2_pair_ABI, \
    uniswap_v3_Factory_ABI, uniswap_v3_quoter_ABI, uniswap_v3_pool_ABI
from src.utils.uniswap.data import CONTRACT_ADDRESS, V3_QUOTER_ADDRESS, NULL_ADDRESS

ALCHEMY_API_KEY = os.getenv("ALCHEMY_API_KEY")
logger = get_logger(__name__)


class UniswapService:
    """
    A service to fetch quotes from Uniswap on EVM.
    """

    def __init__(self, chain_id: ChainId):
        chain = get_chain_by_id(chain_id)
        self.chain_name = chain.get_alias(ServiceType.UNISWAP)
        self.decimal = chain.nativeCurrency.decimals
        # url = f"https://{self.chain_name}.g.alchemy.com/v2/{ALCHEMY_API_KEY}"
        url = "https://hardworking-muddy-wish.quiknode.pro/5513598aadc4b76b20f85a2faef738ca00ecc948"
        self.w3 = AsyncWeb3(Web3.AsyncHTTPProvider(url))
        self.chain_id = chain_id
        self.v2factory_contract = self.w3.eth.contract(address=CONTRACT_ADDRESS[chain_id][0],
                                                       abi=uniswap_v2_Factory_ABI)
        self.v2router_contract = self.w3.eth.contract(address=CONTRACT_ADDRESS[chain_id][1], abi=uniswap_v2_router_ABI)
        self.v3factory_contract = self.w3.eth.contract(address=CONTRACT_ADDRESS[chain_id][2],
                                                       abi=uniswap_v3_Factory_ABI)
        self.v3quoter_contract = self.w3.eth.contract(address=V3_QUOTER_ADDRESS, abi=uniswap_v3_quoter_ABI)

        self.session = None


    def _float_to_uint256(self, amount: float) -> int:
        factor = 10 ** self.decimal
        return int(amount * factor)

    async def _get_pair(self, currency_in: CurrencyBase, currency_out: CurrencyBase) -> Optional[str]:
        v2factory_contract = self.w3.eth.contract(address=CONTRACT_ADDRESS[self.chain_id][0],
                                                       abi=uniswap_v2_Factory_ABI)
        pair_address = await v2factory_contract.functions.getPair(to_checksum_address(currency_in.address),
                                                                 to_checksum_address(
                                                                     currency_out.address)).call()  # Await the contract function call
        if pair_address == NULL_ADDRESS:
            logger.error(f"No pair found for {currency_in.address} and {currency_out.address}")
            return None
        return pair_address

    async def _get_pool(self, currency_in: CurrencyBase, currency_out: CurrencyBase) -> dict:
        fee_list = [100, 500, 3000, 10000]
        v3factory_contract = self.w3.eth.contract(address=CONTRACT_ADDRESS[self.chain_id][2],
                                                  abi=uniswap_v3_Factory_ABI)
        pools = []
        for fee in fee_list:
            pool = await v3factory_contract.functions.getPool(
                to_checksum_address(currency_in.address),
                to_checksum_address(currency_out.address),
                fee
            ).call()
            pools.append((fee, pool))

        # Create a dictionary with valid pools
        return {fee: pool for fee, pool in pools if pool != NULL_ADDRESS}

    async def _get_amount_out(self, amount: int, currency_in: CurrencyBase, currency_out: CurrencyBase,
                              sqrt_limit: int = 0):
        if not self.session or self.session.closed:
            self.session = aiohttp.ClientSession()

        quotes = []
        pair_address = await self._get_pair(currency_in, currency_out)
        if not pair_address:
            logger.error(f"Failed to get pair address {pair_address}")
            return 0
        pair_contract = self.w3.eth.contract(address=pair_address, abi=uniswap_v2_pair_ABI)
        reserves = await pair_contract.functions.getReserves().call()
        if not reserves:
            logger.error(f"Failed to get reserve {reserves}")
            return 0
        expected_out_amount = await self.v2router_contract.functions.getAmountOut(amount, reserves[1], reserves[0]).call()
        quotes.append(expected_out_amount)

        pool_fee_map = await self._get_pool(currency_in, currency_out)

        best_liquidity = 0
        best_fee = float('inf')  # Start with an infinitely high fee
        for fee, pool in pool_fee_map.items():
            pool_contract = self.w3.eth.contract(address=pool, abi=uniswap_v3_pool_ABI)
            liquidity = await pool_contract.functions.liquidity().call()
            if liquidity > best_liquidity or (liquidity == best_liquidity and fee < best_fee):
                best_liquidity = liquidity
                best_fee = fee
        v3quoter_contract =  self.w3.eth.contract(address=V3_QUOTER_ADDRESS, abi=uniswap_v3_quoter_ABI)
        expected_out_amount_v3 = await v3quoter_contract.functions.quoteExactOutputSingle(
            to_checksum_address(currency_in.address), to_checksum_address(currency_out.address), best_fee, amount, sqrt_limit
        ).call()
        quotes.append(expected_out_amount_v3)
        return min(quotes)

    async def __aenter__(self):
        return self


    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()


    @cached(ttl=900, cache=Cache.MEMORY)
    async def get_quote(self, currency_in: CurrencyBase, currency_out: CurrencyBase,
                        amount: int) -> int:
        amount_out = await self._get_amount_out(amount, currency_in, currency_out)
        return amount_out
