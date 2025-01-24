import os
import asyncio
from typing import List, Optional
import aiohttp 

from src.utils.types import ChainId
from src.utils.currencies.types import Currency, CurrencyBase
from src.utils.logging import get_logger
from src.utils.chains.types import ServiceType
from src.utils.chains.queries import get_chain_by_id
from .types import Balance

logger = get_logger(__name__)
ALCHEMY_API_KEY = os.getenv("ALCHEMY_API_KEY")

HEADERS = {
    "accept": "application/json",
    "content-type": "application/json"
}

async def get_token_balances(session: aiohttp.ClientSession, address: str, chain_id: ChainId) -> List[Balance]:
    """
    Fetch token balances for a given address using

    Args:
        session: aiohttp client session
        address: The wallet address to query
        chain_id: The chain ID to query
    """
    chain = get_chain_by_id(chain_id)
    chain_name = chain.get_alias(ServiceType.ALCHEMY)
    url = f"https://{chain_name}.g.alchemy.com/v2/{ALCHEMY_API_KEY}"

    payload = {
        "id": 1,
        "jsonrpc": "2.0",
        "method": "alchemy_getTokenBalances",
        "params": [address]
    }

    try:
        async with session.post(url, json=payload, headers=HEADERS) as response:
            response.raise_for_status()
            data = await response.json()
            balances = data["result"]["tokenBalances"]
            return [
                Balance(
                    currency=CurrencyBase(address=balance["contractAddress"], chain_id=chain_id),
                    amount=int(balance["tokenBalance"], 16)
                )
                for balance in balances
            ]
    except Exception as e:
        logger.error(f"Failed to get token balances for {address} on chain {chain_id}: {str(e)}")
        return []

async def get_metadata(session: aiohttp.ClientSession, currency: CurrencyBase) -> Optional[Currency]:
    """
    Fetch token metadata for a given token address
    
    Args:
        session: aiohttp client session 
        currency: The currency to fetch metadata for
    """
    if currency.is_native:
        raise ValueError("Native currency does not have metadata")

    chain = currency.chain
    chain_name = chain.get_alias(ServiceType.ALCHEMY)
    url = f"https://{chain_name}.g.alchemy.com/v2/{ALCHEMY_API_KEY}"

    payload = {
        "id": 1,
        "jsonrpc": "2.0",
        "method": "alchemy_getTokenMetadata",
        "params": [currency.address]
    }

    try:
        async with session.post(url, json=payload, headers=HEADERS) as response:
            response.raise_for_status()
            result = (await response.json())["result"]
            return Currency(
                address=currency.address,
                chain_id=currency.chain_id,
                decimals=result["decimals"],
                image=result["logo"],
                name=result["name"],
                ticker=result["symbol"]
            )
    except Exception as e:
        logger.error(f"Failed to get token metadata for {currency.address}: {str(e)}")
        return None

async def get_native_balance(session: aiohttp.ClientSession, address: str, chain_id: ChainId) -> Balance:
    """
    Fetch native token balance
    
    Args:
        session: aiohttp client session
        address: The wallet address to query
        chain_id: The chain ID to query
    """
    chain = get_chain_by_id(chain_id)
    chain_name = chain.get_alias(ServiceType.ALCHEMY)
    url = f"https://{chain_name}.g.alchemy.com/v2/{ALCHEMY_API_KEY}"

    payload = {
        "id": 1,
        "jsonrpc": "2.0",
        "method": "eth_getBalance",
        "params": [address]
    }

    try:
        async with session.post(url, json=payload, headers=HEADERS) as response:
            response.raise_for_status()
            result = await response.json()
            return Balance(
                currency=CurrencyBase.from_chain(chain),
                amount=int(result["result"], 16)
            )
    except Exception as e:
        logger.error(f"Failed to get native balance for {address} on chain {chain_id}: {str(e)}")
        return Balance(currency=CurrencyBase.from_chain(chain), amount=0)

async def get_wallet_balances(address: str, chain_id: ChainId) -> List[Balance]:
    """
    Fetch all token balances for a given address and chain_id
    
    Args:
        address: The wallet address to query
        chain_id: The chain ID to query
    """
    async with aiohttp.ClientSession() as session:
        native_balance, token_balances = await asyncio.gather(
            get_native_balance(session, address, chain_id),
            get_token_balances(session, address, chain_id)
        )
        return [native_balance] + token_balances

