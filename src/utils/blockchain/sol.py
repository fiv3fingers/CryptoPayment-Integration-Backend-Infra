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

SOLANA_RPC_URL = os.getenv("SOLANA_RPC_URL")
if SOLANA_RPC_URL is None:
    raise ValueError("SOLANA_RPC_URL is not set")

HEADERS = {
    "Content-Type": "application/json",
}


@dataclass
class Metadata:
    mint: str
    name: str
    symbol: str
    uri: str


async def get_token_balances(
    session: aiohttp.ClientSession, pubkey: str
) -> List[Balance]:
    """
    fetch all token balances for a Solana wallet address.
    """
    filters = [
        {"dataSize": 165},  # Size of token account (bytes)
        {
            "memcmp": {
                "offset": 32,  # Location of owner field
                "bytes": pubkey,  # Wallet to search for
            }
        },
    ]

    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getProgramAccounts",
        "params": [
            "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA",  # TOKEN_PROGRAM_ID
            {"encoding": "jsonParsed", "filters": filters},
        ],
    }

    try:
        async with session.post(
            SOLANA_RPC_URL, json=payload, headers=HEADERS
        ) as response:
            response.raise_for_status()
            data = await response.json()
            result = data.get("result", [])

            token_accounts = []
            for account in result:
                try:
                    account_data = account["account"]["data"]["parsed"]["info"]
                    token_accounts.append(
                        Balance(
                            currency=CurrencyBase(
                                address=account_data["mint"], chain_id=ChainId.SOL
                            ),
                            amount=int(account_data["tokenAmount"]["amount"]),
                        )
                    )
                except (KeyError, TypeError) as e:
                    logger.warning(f"Failed to parse account data: {str(e)}")
                    continue

            return token_accounts

    except Exception as e:
        logger.error(f"Failed to get token accounts for {pubkey}: {str(e)}")
        return []


async def get_native_balance(session: aiohttp.ClientSession, pubkey: str) -> Balance:
    """
    fetch the native SOL balance for a wallet address.
    """
    payload = {"jsonrpc": "2.0", "id": 1, "method": "getBalance", "params": [pubkey]}

    try:
        async with session.post(
            SOLANA_RPC_URL, json=payload, headers=HEADERS
        ) as response:
            response.raise_for_status()
            data = await response.json()
            return Balance(
                currency=CurrencyBase.from_chain(ChainId.SOL),
                amount=data.get("result", {}).get("value", 0),
            )

    except Exception as e:
        logger.error(f"Failed to get balance for {pubkey}: {str(e)}")
        return Balance(currency=CurrencyBase.from_chain(ChainId.SOL), amount=0)


async def get_wallet_balances(pubkey: str) -> List[Balance]:
    """
    fetch both native and token balances for a Solana wallet.
    """
    async with aiohttp.ClientSession() as session:
        native_balance, token_balances = await asyncio.gather(
            get_native_balance(session, pubkey), get_token_balances(session, pubkey)
        )

        return [native_balance] + token_balances
