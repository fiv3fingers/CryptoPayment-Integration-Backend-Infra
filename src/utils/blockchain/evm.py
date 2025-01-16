import os
from typing import List
import requests

from src.utils.types import ChainId

from src.utils.currencies.types import Currency, CurrencyBase
from src.utils.logging import get_logger
from src.utils.chains.types import ServiceType
from src.utils.chains.queries import get_chain_by_id

from .types import Balance

logger = get_logger(__name__)
ALCHEMY_API_KEY = os.getenv("ALCHEMY_API_KEY")


def get_token_balances(address: str, chain_id: ChainId) -> List[Balance]:
    """
    Fetch token balances for a given address using Alchemy API
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

    headers = {
        "accept": "application/json",
        "content-type": "application/json"
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()

        balances = response.json()["result"]["tokenBalances"]
        return [
            Balance(
                currency=CurrencyBase(address=balance["contractAddress"], chain_id=chain_id),
                amount=int(balance["tokenBalance"], 16)
            )
            for balance in balances
        ]
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to get token balances for {address}: {str(e)}")
        return []

def get_metadata(currency: CurrencyBase) -> Currency:
    """
    Fetch token metadata for a given token address using Alchemy API
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

    headers = {
        "accept": "application/json",
        "content-type": "application/json"
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        result = response.json()["result"]
        return Currency(
            address=currency.address,
            chain_id=currency.chain_id,
            decimals=result["decimals"],
            image=result["logo"],
            name=result["name"],
            ticker=result["symbol"]
        )

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to get token metadata for {currency.address}: {str(e)}")
        return None


def get_native_balance(address: str, chain_id: ChainId) -> Balance:
    """
    Fetch native token balance for a given address using Alchemy API
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

    headers = {
        "accept": "application/json",
        "content-type": "application/json"
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return Balance(
            currency=CurrencyBase.from_chain(chain),
            amount=int(response.json()["result"], 16)
        )
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to get native balance for {address}: {str(e)}")
        return Balance(currency=CurrencyBase.from_chain(chain), amount=0)


def get_wallet_balances(address: str, chain_id: ChainId) -> List[Balance]:
    """
    Fetch all token balances for a given address using Alchemy API
    """
    native_balance = get_native_balance(address, chain_id)
    token_balances = get_token_balances(address, chain_id)
    return [native_balance] + token_balances
