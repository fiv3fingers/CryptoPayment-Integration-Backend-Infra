import os
import asyncio
from typing import List, Optional
import aiohttp

from web3 import AsyncWeb3, Web3
from eth_utils.address import to_checksum_address
from typing import Dict, Optional

from web3.types import TxData

from src.utils.types import ChainId
from src.utils.currencies.types import Currency, CurrencyBase
from src.utils.logging import get_logger
from src.utils.chains.types import ServiceType
from src.utils.chains.queries import get_chain_by_id, get_rpc_by_chain_id
from .types import Balance, TransferInfo

logger = get_logger(__name__)

HEADERS = {"accept": "application/json", "content-type": "application/json"}

async def _get_web3_client(chain_id: ChainId) -> AsyncWeb3:
    """Helper function to create Web3 client."""
    rpc_url = get_rpc_by_chain_id(chain_id)
    return AsyncWeb3(Web3.AsyncHTTPProvider(rpc_url))



async def get_token_balances(
    session: aiohttp.ClientSession, address: str, chain_id: ChainId
) -> List[Balance]:
    """
    Fetch token balances for a given address using

    Args:
        session: aiohttp client session
        address: The wallet address to query
        chain_id: The chain ID to query
    """
    url = get_rpc_by_chain_id(chain_id)

    payload = {
        "id": 1,
        "jsonrpc": "2.0",
        "method": "alchemy_getTokenBalances",
        "params": [address],
    }

    try:
        async with session.post(url, json=payload, headers=HEADERS) as response:
            response.raise_for_status()
            data = await response.json()
            balances = data["result"]["tokenBalances"]
            return [
                Balance(
                    currency=CurrencyBase(
                        address=balance["contractAddress"], chain_id=chain_id
                    ),
                    amount=int(balance["tokenBalance"], 16),
                )
                for balance in balances
            ]
    except Exception as e:
        logger.error(
            f"Failed to get token balances for {address} on chain {chain_id}: {str(e)}"
        )
        return []


async def get_metadata(
    session: aiohttp.ClientSession, currency: CurrencyBase
) -> Optional[Currency]:
    """
    Fetch token metadata for a given token address

    Args:
        session: aiohttp client session
        currency: The currency to fetch metadata for
    """
    if currency.is_native:
        raise ValueError("Native currency does not have metadata")

    url = get_rpc_by_chain_id(currency.chain_id)

    payload = {
        "id": 1,
        "jsonrpc": "2.0",
        "method": "alchemy_getTokenMetadata",
        "params": [currency.address],
    }

    try:
        async with session.post(url, json=payload, headers=HEADERS) as response:
            response.raise_for_status()
            result = (await response.json())["result"]
            return Currency(
                address=currency.address,
                chain_id=currency.chain_id,
                decimals=result["decimals"],
                image_uri=result["logo"],
                name=result["name"],
                ticker=result["symbol"],
            )
    except Exception as e:
        logger.error(f"Failed to get token metadata for {currency.address}: {str(e)}")
        return None


async def get_native_balance(
    session: aiohttp.ClientSession, address: str, chain_id: ChainId
) -> Balance:
    """
    Fetch native token balance

    Args:
        session: aiohttp client session
        address: The wallet address to query
        chain_id: The chain ID to query
    """

    chain = get_chain_by_id(chain_id)
    url = get_rpc_by_chain_id(chain.id)

    payload = {
        "id": 1,
        "jsonrpc": "2.0",
        "method": "eth_getBalance",
        "params": [address],
    }

    try:
        async with session.post(url, json=payload, headers=HEADERS) as response:
            response.raise_for_status()
            result = await response.json()
            return Balance(
                currency=CurrencyBase.from_chain(chain),
                amount=int(result["result"], 16),
            )
    except Exception as e:
        logger.error(
            f"Failed to get native balance for {address} on chain {chain_id}: {str(e)}"
        )
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
            get_token_balances(session, address, chain_id),
        )
        return [native_balance] + token_balances


async def get_native_transfer(tx_hash: str, chain_id: ChainId) -> TransferInfo:
    """Get native transfer details from a transaction hash."""
    w3 = await _get_web3_client(chain_id)

    try:
        tx = await w3.eth.get_transaction(tx_hash)
        if tx and tx["value"] > 0:
            return TransferInfo(
                source_address=to_checksum_address(tx["from"]),
                destination_address=to_checksum_address(tx["to"]),
                amount=tx["value"],
                currency=CurrencyBase(address=None, chain_id=chain_id),
            )
    except Exception as e:
        logger.error(f"Failed to get native transfer details for {tx_hash}: {str(e)}")
    raise ValueError("No native transfer found in transaction")


async def get_erc20_transfer(tx_hash: str, chain_id: ChainId) -> TransferInfo:
    """Get ERC20 token transfer details from a transaction hash."""
    w3 = await _get_web3_client(chain_id)

    try:
        transfer_event_signature = w3.keccak(
            text="Transfer(address,address,uint256)"
        ).hex()
        tx_info = await w3.eth.get_transaction_receipt(tx_hash)

        for log in tx_info["logs"]:
            if (
                len(log["topics"]) == 3
                and log["topics"][0].hex() == transfer_event_signature
            ):
                return TransferInfo(
                    source_address=to_checksum_address(
                        "0x" + log["topics"][1].hex()[-40:]
                    ),
                    destination_address=to_checksum_address(
                        "0x" + log["topics"][2].hex()[-40:]
                    ),
                    amount=int(log["data"].hex(), 16),
                    currency=CurrencyBase(
                        address=to_checksum_address(log["address"]), chain_id=chain_id
                    ),
                )
    except Exception as e:
        logger.error(f"Failed to get ERC20 transfer details for {tx_hash}: {str(e)}")
    raise ValueError("No ERC20 transfer found in transaction")


async def get_transfer_details(tx_hash: str, chain_id: ChainId) -> TransferInfo:
    """
    Get transfer details from a transaction hash.

    Args:
        tx_hash (str): The transaction hash to analyze
        chain_id (ChainId): The chain ID to query

    Raises:
        ValueError: If no transfer is found in the transaction
    """
    w3 = await _get_web3_client(chain_id)

    try:
        tx = await w3.eth.get_transaction(tx_hash)

        # has value and no input data => native transfer
        if tx["value"] > 0 and (not tx.get("input") or tx["input"] == "0x"):
            return TransferInfo(
                source_address=to_checksum_address(tx["from"]),
                destination_address=to_checksum_address(tx["to"]),
                amount=tx["value"],
                currency=CurrencyBase(address=None, chain_id=chain_id),
            )

        # If input data => check for ERC20 transfer
        if tx.get("input") and tx["input"].hex().startswith(
            "0xa9059cbb"
        ):  # https://www.4byte.directory/signatures/?bytes4_signature=0xa9059cbb
            receipt = await w3.eth.get_transaction_receipt(tx_hash)
            transfer_event_signature = w3.keccak(
                text="Transfer(address,address,uint256)"
            ).hex()

            for log in receipt["logs"]:
                if (
                    len(log["topics"]) == 3
                    and log["topics"][0].hex() == transfer_event_signature
                ):
                    return TransferInfo(
                        source_address=to_checksum_address(
                            "0x" + log["topics"][1].hex()[-40:]
                        ),
                        destination_address=to_checksum_address(
                            "0x" + log["topics"][2].hex()[-40:]
                        ),
                        amount=int(log["data"].hex(), 16),
                        currency=CurrencyBase(
                            address=to_checksum_address(log["address"]),
                            chain_id=chain_id,
                        ),
                    )

    except Exception as e:
        logger.error(f"Failed to get transfer details for {tx_hash}: {str(e)}")
        raise ValueError(f"Error processing transaction: {str(e)}")

    raise ValueError("No valid transfer found in transaction")
