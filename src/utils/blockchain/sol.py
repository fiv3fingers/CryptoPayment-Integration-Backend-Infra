import os
import asyncio
from dataclasses import dataclass
from typing import List
import aiohttp

from .types import Balance, TransferInfo
from src.utils.types import ChainId
from src.utils.currencies.types import CurrencyBase
from src.utils.logging import get_logger


logger = get_logger(__name__)


SYSTEM_PROGRAM_ID = "11111111111111111111111111111111"

SOLANA_RPC_URL = os.getenv("SOLANA_RPC_URL")
if SOLANA_RPC_URL is None:
    raise ValueError("SOLANA_RPC_URL is not set")
SOLANA_RPC_HEADERS = {
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
            SOLANA_RPC_URL, json=payload, headers=SOLANA_RPC_HEADERS
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
            SOLANA_RPC_URL, json=payload, headers=SOLANA_RPC_HEADERS
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


async def get_transfer_details(tx_hash: str) -> TransferInfo:
    """
    Get transfer details from a Solana transaction hash.
    Handles both native SOL and SPL token transfers.

    Args:
        tx_hash (str): The transaction signature to analyze

    Raises:
        ValueError: If no transfer is found or transaction failed
    """
    async with aiohttp.ClientSession() as session:
        try:
            # Get transaction data with parsed details
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getTransaction",
                "params": [
                    tx_hash,
                    {"encoding": "jsonParsed", "maxSupportedTransactionVersion": 0},
                ],
            }

            async with session.post(
                SOLANA_RPC_URL, json=payload, headers=SOLANA_RPC_HEADERS
            ) as response:
                response.raise_for_status()
                data = await response.json()

                mint = None
                source_ata = None
                destination_ata = None
                amount = None

                result = data.get("result")
                if not result:
                    raise ValueError("Transaction not found")

                # Check if transaction was successful
                if result.get("meta", {}).get("err") is not None:
                    raise ValueError("Transaction failed")

                # First check main instructions for transfers
                instructions = result["transaction"]["message"]["instructions"]
                for ix in instructions:
                    # Check for native SOL transfer
                    if (
                        ix.get("programId") == SYSTEM_PROGRAM_ID
                        or ix.get("program") == "system"
                    ) and ix.get("parsed", {}).get("type") == "transfer":
                        parsed = ix["parsed"]["info"]
                        return TransferInfo(
                            source_address=parsed["source"],
                            destination_address=parsed["destination"],
                            amount=parsed["lamports"],
                            currency=CurrencyBase(address=None, chain_id=ChainId.SOL),
                        )

                    # Check for SPL token transfers in main instructions
                    if ix.get("program") == "spl-token":
                        parsed = ix.get("parsed", {})
                        if parsed.get("type") in ["transfer", "transferChecked"]:
                            info = parsed["info"]
                            source_ata = info["source"]
                            destination_ata = info["destination"]
                            amount = int(
                                info["tokenAmount"]["amount"]
                                if "tokenAmount" in info
                                else info["amount"]
                            )
                            mint = info.get("mint")

                # Check for SPL token transfers in innerInstructions
                for inner in result["meta"]["innerInstructions"]:
                    for ix in inner.get("instructions", []):
                        if ix.get("program") == "spl-token":
                            parsed = ix.get("parsed", {})
                            if parsed.get("type") in ["transfer", "transferChecked"]:
                                info = parsed["info"]
                                source_ata = info["source"]
                                destination_ata = info["destination"]
                                amount = int(
                                    info["tokenAmount"]["amount"]
                                    if "tokenAmount" in info
                                    else info["amount"]
                                )
                                mint = info.get("mint")

                if not source_ata or not destination_ata or not amount or not mint:
                    raise ValueError("No transfer found in transaction")

                # find the balance deltas
                pre_token_balances = result["meta"]["preTokenBalances"]
                post_token_balances = result["meta"]["postTokenBalances"]

                deltas = []  # [address, delta]
                for balance in pre_token_balances:
                    if balance["mint"] == mint:
                        deltas.append(
                            [balance["owner"], -int(balance["uiTokenAmount"]["amount"])]
                        )
                for balance in post_token_balances:
                    if balance["mint"] == mint:
                        found = False
                        for delta in deltas:
                            if delta[0] == balance["owner"]:
                                delta[1] += int(balance["uiTokenAmount"]["amount"])
                                found = True
                                break
                        if not found:
                            deltas.append(
                                [
                                    balance["owner"],
                                    int(balance["uiTokenAmount"]["amount"]),
                                ]
                            )

                # deduce the source and destination addresses from the deltas

                source_address = None
                destination_address = None
                for delta in deltas:
                    if delta[1] == -amount:  # tokens were transferred out
                        source_address = delta[0]
                    elif delta[1] == amount:  # tokens were transferred in
                        destination_address = delta[0]

                return TransferInfo(
                    currency=CurrencyBase(address=mint, chain_id=ChainId.SOL),
                    source_address=source_address,
                    destination_address=destination_address,
                    amount=amount,
                )

        except Exception as e:
            logger.error(f"Failed to get transfer details for {tx_hash}: {str(e)}")
            raise ValueError(f"Error processing transaction: {str(e)}")

