import os
from dataclasses import dataclass
import aiohttp
from typing import List
from src.utils.logging import get_logger
from src.utils.currencies.types import CurrencyBase
from src.utils.chains.types import ChainId
from .types import Balance, TransferInfo

from typing import Any, Dict, Optional

logger = get_logger(__name__)
SUI_RPC_URL = os.getenv("SUI_RPC_URL")
if SUI_RPC_URL is None:
    raise ValueError("SUI_RPC_URL is not set")

HEADERS = {
    "Content-Type": "application/json",
}


@dataclass
class TokenBalance:
    coin_type: str  # Address of the coin
    balance: int  # Raw balance
    balance_ui: float  # UI balance (considering decimals)
    decimals: int
    symbol: str
    description: str
    iconUrl: str


async def get_token_balances(
    session: aiohttp.ClientSession, address: str
) -> List[Balance]:
    """
    fetch all token balances for a Sui wallet address.
    """
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "suix_getAllBalances",
        "params": [address],
    }

    try:
        async with session.post(SUI_RPC_URL, json=payload, headers=HEADERS) as response:
            response.raise_for_status()
            data = await response.json()
            result = data.get("result", [])

            token_balances = []
            for balance in result:
                coin_type = balance.get("coinType")
                total_balance = int(balance.get("totalBalance", "0"))

                token_balances.append(
                    Balance(
                        currency=CurrencyBase(address=coin_type, chain_id=ChainId.SUI),
                        amount=total_balance,
                    )
                )

            return token_balances

    except aiohttp.ClientError as e:
        logger.error(f"Failed to get token balances for {address}: {str(e)}")
        return []
    except Exception as e:
        logger.error(
            f"Unexpected error while getting token balances for {address}: {str(e)}"
        )
        return []


async def get_wallet_balances(address: str) -> List[Balance]:
    """
    Fetch all token balances for a given wallet address.
    """
    async with aiohttp.ClientSession() as session:
        token_balances = await get_token_balances(session, address)
        return token_balances


def parse_coin_transfer(
    transaction: Dict[str, Any], effects: Dict[str, Any]
) -> Optional[TransferInfo]:
    """parse a tx from data and effects"""
    try:
        tx_data = transaction.get("data", {})
        sender = tx_data.get("sender")

        prog_tx = tx_data.get("transaction", {})
        if prog_tx.get("kind") != "ProgrammableTransaction":
            return None

        inputs = prog_tx.get("inputs", [])
        transactions = prog_tx.get("transactions", [])

        recipient = None
        amount = None
        is_native_sui = False

        for tx_input in inputs:
            if tx_input.get("type") == "pure":
                if tx_input.get("valueType") == "u64":
                    amount = int(tx_input.get("value", "0"))
                elif tx_input.get("valueType") == "address":
                    recipient = tx_input.get("value")

        for tx in transactions:
            if "SplitCoins" in tx:
                split_coins = tx["SplitCoins"]
                if split_coins[0] == "GasCoin":
                    is_native_sui = True
                    break

        if not (sender and recipient and amount):
            return None

        if is_native_sui:
            currency = CurrencyBase(address=None, chain_id=ChainId.SUI)
        else:
            for tx_input in inputs:
                if (
                    tx_input.get("type") == "object"
                    and tx_input.get("objectType") == "immOrOwnedObject"
                ):
                    currency = CurrencyBase(
                        address=tx_input.get("objectId"), chain_id=ChainId.SUI
                    )
                    break
            else:
                return None

        status = effects.get("status", {}).get("status")

        return TransferInfo(
            source_address=sender,
            destination_address=recipient,
            amount=amount,
            confirmed=status == "success",
            currency=currency,
        )

    except Exception as e:
        logger.error(f"Error parsing coin transfer: {str(e)}")
        return None


async def get_transfer_details(tx_hash: str) -> TransferInfo:
    """fetch transaction information for a given transaction hash"""

    async with aiohttp.ClientSession() as session:
        try:
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "sui_getTransactionBlock",
                "params": [
                    tx_hash,
                    {
                        "showInput": True,
                        "showEffects": True,
                        "showEvents": True,
                    },
                ],
            }

            async with session.post(
                SUI_RPC_URL, json=payload, headers=HEADERS
            ) as response:
                response.raise_for_status()
                data = await response.json()

                if "error" in data:
                    raise ValueError(f"RPC error: {data['error']}")

                result = data.get("result")
                if not result:
                    raise ValueError("Transaction not found")

                transfer = parse_coin_transfer(
                    result.get("transaction", {}), result.get("effects", {})
                )

                if transfer:
                    return transfer

                raise ValueError("No transfer found in transaction")

        except aiohttp.ClientError as e:
            logger.error(
                f"Network error while getting transfer details for {tx_hash}: {str(e)}"
            )
            raise ValueError(f"Network error: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to get transfer details for {tx_hash}: {str(e)}")
            raise ValueError(f"Error processing transaction: {str(e)}")
