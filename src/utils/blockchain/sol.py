import os
from dataclasses import dataclass
from typing import List
import requests

from src.utils.types import ChainId

from src.utils.currencies.types import CurrencyBase
from src.utils.logging import get_logger
from .types import Balance



logger = get_logger(__name__)

SOLANA_RPC_URL = os.getenv("SOLANA_RPC_URL")
if SOLANA_RPC_URL is None:
    raise ValueError("SOLANA_RPC_URL is not set")

@dataclass
class Metadata:
    mint: str
    name: str
    symbol: str
    uri: str


def get_token_balances(pubkey: str) -> List[Balance]:
    filters = [
        {
            "dataSize": 165  # Size of token account (bytes)
        },
        {
            "memcmp": {
                "offset": 32,  # Location of owner field
                "bytes": pubkey  # Wallet to search for
            }
        }
    ]

    # Construct the RPC request
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getProgramAccounts",
        "params": [
            "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA",  # TOKEN_PROGRAM_ID
            {
                "encoding": "jsonParsed",
                "filters": filters
            }
        ]
    }
    
    headers = {
        "Content-Type": "application/json",
    }
    
    try:
        response = requests.post(SOLANA_RPC_URL, json=payload, headers=headers)
        response.raise_for_status()
        
        result = response.json().get("result", [])
        
        token_accounts = []
        for account in result:
            try:
                account_data = account["account"]["data"]["parsed"]["info"]
                token_accounts.append(
                    Balance(
                        currency=CurrencyBase(address=account_data["mint"], chain_id=ChainId.SOL),
                        amount=int(account_data["tokenAmount"]["amount"]),
                    )
                )
            except (KeyError, TypeError) as e:
                logger.warning(f"Failed to parse account data: {str(e)}")
                continue
                
        return token_accounts

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to get token accounts for {pubkey}: {str(e)}")
        return []


def get_native_balance(pubkey: str) -> Balance:
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getBalance",
        "params": [pubkey]
    }
    
    headers = {
        "Content-Type": "application/json",
    }
    
    try:
        response = requests.post(SOLANA_RPC_URL, json=payload, headers=headers)
        response.raise_for_status()
        
        return Balance(
            currency=CurrencyBase.from_chain(ChainId.SOL),
            amount=response.json().get("result", 0).get("value", 0)
        )
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to get balance for {pubkey}: {str(e)}")
        return Balance(currency=CurrencyBase.from_chain(ChainId.SOL), amount=0)

def get_wallet_balances(pubkey: str) -> List[Balance]:
    native_balance = get_native_balance(pubkey)
    token_balances = get_token_balances(pubkey)

    return [native_balance] + token_balances

