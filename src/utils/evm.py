import os
from dataclasses import dataclass
from typing import List, Optional
import requests
from .logging import get_logger

logger = get_logger(__name__)
ALCHEMY_API_KEY = os.getenv("ALCHEMY_API_KEY")

@dataclass
class Metadata:
    decimals: int
    logo: str
    name: str
    symbol: str

@dataclass
class Balance:
    contractAddress: str
    tokenBalance: int



def get_token_balances(address: str, chain_name: str = "eth") -> List[Balance]:
    """
    Fetch token balances for a given address using Alchemy API
    """
    url = f"https://{chain_name}-mainnet.g.alchemy.com/v2/{ALCHEMY_API_KEY}"
    
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
                contractAddress=balance["contractAddress"],
                tokenBalance=int(balance["tokenBalance"], 16)
            )
            for balance in balances
        ]
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to get token balances for {address}: {str(e)}")
        return []

def get_token_metadata(token_address: str, chain_name: str = "eth") -> Optional[Metadata]:
    """
    Fetch token metadata for a given token address using Alchemy API
    """
    url = f"https://{chain_name}-mainnet.g.alchemy.com/v2/{ALCHEMY_API_KEY}"
    
    payload = {
        "id": 1,
        "jsonrpc": "2.0",
        "method": "alchemy_getTokenMetadata",
        "params": [token_address]
    }
    
    headers = {
        "accept": "application/json",
        "content-type": "application/json"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        result = response.json()["result"]
        return Metadata(
            decimals=result["decimals"],
            logo=result["logo"],
            name=result["name"],
            symbol=result["symbol"]
        )
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to get token metadata for {token_address}: {str(e)}")
        return None


def get_native_balance(address: str, chain_name: str = "eth") -> int:
    """
    Fetch native token balance for a given address using Alchemy API
    """
    url = f"https://{chain_name}-mainnet.g.alchemy.com/v2/{ALCHEMY_API_KEY}"
    
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
        return int(response.json()["result"], 16)
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to get native balance for {address}: {str(e)}")
        return 0
