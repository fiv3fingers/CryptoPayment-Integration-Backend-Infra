import os
import asyncio
from dataclasses import dataclass
from typing import List
import aiohttp

from .types import Balance
from src.utils.types import ChainId
from src.utils.currencies.types import CurrencyBase
from src.utils.logging import get_logger

logger = get_logger(__name__)

BTC_API_URL = "https://api.blockchain.info/haskoin-store/btc/address"

HEADERS = {
    "Content-Type": "application/json",
}


@dataclass
class Metadata:
    mint: str
    name: str
    symbol: str
    uri: str


async def get_btc_balance(session: aiohttp.ClientSession, pubkey: str) -> Balance:
    """
    fetch all token balances for a Bitcoin wallet address.
    """

    try:
        async with session.get(
            "{BTC_API_URL}/{address}/balance".format(
                BTC_API_URL=BTC_API_URL, address=pubkey
            ),
            headers=HEADERS,
        ) as response:
            response.raise_for_status()
            data = await response.json()
            balance = data.get("confirmed", 0)

            return Balance(
                currency=CurrencyBase(chain_id=ChainId.BTC), amount=int(balance)
            )
    except Exception as e:
        logger.error(f"Failed to get token accounts for {pubkey}: {str(e)}")
        return Balance(currency=CurrencyBase(chain_id=ChainId.BTC), amount=0)


async def get_wallet_balances(pubkey: str, chain_id: ChainId) -> List[Balance]:
    """
    fetch both native and token balances for a Solana wallet.
    """
    async with aiohttp.ClientSession() as session:
        balances = []
        match chain_id:
            case ChainId.BTC:
                balance = await get_btc_balance(session, pubkey)
                balances.append(balance)

        return balances
