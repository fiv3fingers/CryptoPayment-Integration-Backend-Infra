import os
from dataclasses import dataclass
import requests
from typing import List

from src.utils.logging import get_logger

from src.utils.currencies.types import CurrencyBase 
from src.utils.chains.types import ChainId
from .types import Balance

logger = get_logger(__name__)


SUI_RPC_URL = os.getenv("SUI_RPC_URL")
if SUI_RPC_URL is None:
    raise ValueError("SUI_RPC_URL is not set")

@dataclass
class TokenBalance:
    coin_type: str  # Address/type of the coin
    balance: int    # Raw balance
    balance_ui: float  # UI balance (considering decimals)
    decimals: int   # Number of decimals
    symbol: str     # Token symbol
    description: str  # Token description
    iconUrl: str    # Token icon URL

def get_token_balances(address: str) -> List[Balance]:
    """Get SUI token balances for an address"""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "suix_getAllBalances",
        "params": [address]
    }
    
    headers = {
        "Content-Type": "application/json",
    }
    
    try:
        response = requests.post(SUI_RPC_URL, json=payload, headers=headers)
        response.raise_for_status()
        
        result = response.json().get("result", [])
        token_balances = []

        for balance in result:
            coin_type = balance.get("coinType")
            total_balance = int(balance.get("totalBalance", "0"))

            token_balances.append(
                Balance(
                    currency=CurrencyBase(address=coin_type, chain_id=ChainId.SUI),
                    amount=total_balance
                )
            )
                
        return token_balances

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to get token balances for {address}: {str(e)}")
        return []

def get_wallet_balances(address: str) -> List[Balance]:
    token_balances = get_token_balances(address)
    return token_balances

