import os
from dataclasses import dataclass
from typing import List, Optional
import requests

from .logging import get_logger

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

def get_token_metadata(coin_type: str) -> Optional[dict]:
    """Get metadata for a SUI token type"""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "suix_getCoinMetadata",
        "params": [coin_type]
    }
    
    headers = {
        "Content-Type": "application/json",
    }
    
    try:
        response = requests.post(SUI_RPC_URL, json=payload, headers=headers)
        response.raise_for_status()
        return response.json().get("result")
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to get metadata for {coin_type}: {str(e)}")
        return None

def get_token_balances(address: str) -> List[TokenBalance]:
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
            
            # Get metadata for each token
            description = ""
            iconUrl = ""
            metadata = get_token_metadata(coin_type)
            if metadata:
                print(metadata)
                decimals = metadata.get("decimals", 9)
                symbol = metadata.get("symbol", "")
                balance_ui = total_balance / (10 ** decimals)
                description = metadata.get("description", "")
                iconUrl = metadata.get("iconUrl", "")
            else:
                decimals = 9  # Default decimals
                symbol = coin_type.split("::")[-1]  # Use last part of type as symbol
                balance_ui = total_balance / (10 ** decimals)

            token_balances.append(
                TokenBalance(
                    coin_type=coin_type,
                    balance=total_balance,
                    balance_ui=balance_ui,
                    decimals=decimals,
                    symbol=symbol,
                    description=description,
                    iconUrl=iconUrl
                )
            )
                
        return token_balances

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to get token balances for {address}: {str(e)}")
        return []

def get_native_balance(address: str) -> int:
    """Get native SUI balance for an address"""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "suix_getBalance",
        "params": [address, "0x2::sui::SUI"]
    }
    
    headers = {
        "Content-Type": "application/json",
    }
    
    try:
        response = requests.post(SUI_RPC_URL, json=payload, headers=headers)
        response.raise_for_status()
        
        result = response.json().get("result", {})
        return int(result.get("totalBalance", "0"))
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to get balance for {address}: {str(e)}")
        return 0

