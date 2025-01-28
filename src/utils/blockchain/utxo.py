from dataclasses import dataclass
from typing import List
import aiohttp

from .types import Balance, UTXOOutput, UTXOTransferInfo
from src.utils.types import ChainId
from src.utils.currencies.types import CurrencyBase
from src.utils.logging import get_logger

logger = get_logger(__name__)

BTC_API_URL = "https://api.blockchain.info/haskoin-store/btc/address"
BTC_API_TX_URL = "https://blockchain.info/rawtx"

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


async def get_transfer_details(tx_hash: str, chain_id: ChainId) -> UTXOTransferInfo | None:
    """
    Get transfer details from a UTXO transaction hash.

    Args:
        tx_hash (str): The transaction signature to analyze
        chain_id (ChainId): The chain ID of the blockchain

    Raises:
        ValueError: If no transfer is found or transaction failed
    """
    async with aiohttp.ClientSession() as session:
            match chain_id:
                case ChainId.BTC:
                    return await get_btc_transfer_details(session, tx_hash)
                case _:
                    raise NotImplementedError(f"[UTXO]: Chain ID {chain_id} not supported")


async def get_btc_transfer_details(session: aiohttp.ClientSession, tx_hash: str) -> UTXOTransferInfo | None:
    """
    fetch transaction information for a given transaction hash
    """

    async with session.get(
        "{BTC_API_TX_URL}/{tx_hash}".format(BTC_API_TX_URL=BTC_API_TX_URL, tx_hash=tx_hash),
        headers=HEADERS,
    ) as response:
        # Do not throw on error, might be that the transaction has not reached the the mempool yet
        if response.status >= 400:
            return None
        
        data = await response.json()
        if data.get("error"):
            raise ValueError(data.get("error"))
        
        if data.double_spend:
            raise ValueError("Transaction is a double spend")

        return UTXOTransferInfo(
            currency=CurrencyBase(chain_id=ChainId.BTC),
            source_address=data.get("inputs", [])[0].get("prev_out", {}).get("addr", ""),
            confirmed=data.get("block_height", 0) > 0,
            outputs=[
                UTXOOutput(
                    destination_address=out.get("addr", ""),
                    amount=out.get("value", 0),
                )
                for out in data.get("out", [])
            ],
        )