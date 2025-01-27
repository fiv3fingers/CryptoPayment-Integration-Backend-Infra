import asyncio
from typing import List, Optional

from src.utils.blockchain import utxo
from src.utils.chains.queries import get_chain_by_id, get_chains_by_type
from .types import Balance, TransferInfo
from src.utils.types import ChainId, ChainType
from src.utils.currencies.types import CurrencyBase
from . import evm, sol, sui


async def get_wallet_balances(
    wallet_address: str,
    chain_type: ChainType,
    chain_ids: Optional[List[ChainId]] = None,
    filter_zero: bool = True,
) -> List[Balance]:
    """
    fetch wallet balances for a given address

    Args:
        wallet_address: The address to check balances for
        chain_type: The type of blockchain (EVM, SOL, SUI)
        chain_ids: Optional specific chains to query
        filter_zero: Whether to exclude zero balances from results

    Returns:
        A list of Balance objects representing the wallet's holdings
    """

    match chain_type:
        case ChainType.UTXO:
            if chain_ids is None:
                chain_ids = [c.id for c in get_chains_by_type(ChainType.UTXO)]

            balances = await asyncio.gather(
                *[
                    utxo.get_wallet_balances(wallet_address, chain_id=chain_id)
                    for chain_id in chain_ids
                ]
            )
            balances = [b for sublist in balances for b in sublist]
        case ChainType.EVM:
            if chain_ids is None:
                chain_ids = [c.id for c in get_chains_by_type(ChainType.EVM)]

            balances = await asyncio.gather(
                *[
                    evm.get_wallet_balances(wallet_address, chain_id=chain_id)
                    for chain_id in chain_ids
                ]
            )
            balances = [b for sublist in balances for b in sublist]
        case ChainType.SOL:
            balances = await sol.get_wallet_balances(wallet_address)
        case ChainType.SUI:
            balances = await sui.get_wallet_balances(wallet_address)
        case _:
            raise NotImplementedError(f"Chain type {chain_type} not supported")

    # Filter out zero balances if requested
    if filter_zero:
        balances = [b for b in balances if b.amount > 0]

    return balances


async def get_wallet_currencies(
    wallet_address: str,
    chain_type: ChainType,
    chain_ids: Optional[List[ChainId]] = None,
    filter_zero: bool = True,
) -> List[CurrencyBase]:
    """
    fetch all currencies (tokens) present in a wallet.

    Args:
        wallet_address: The address to check currencies for
        chain_type: The type of blockchain (EVM, SOL, SUI)
        chain_ids: Optional specific chains to query (for EVM chains)
        filter_zero: Whether to exclude currencies with zero balance

    Returns:
        A list of CurrencyBase objects representing the currencies in the wallet
    """
    balances = await get_wallet_balances(
        wallet_address=wallet_address,
        chain_type=chain_type,
        chain_ids=chain_ids,
        filter_zero=filter_zero,
    )
    return [b.currency for b in balances]


async def get_transfer_details(
    tx_hash: str,
    chain_id: Optional[ChainId] = None,
    chain_type: Optional[ChainType] = None,
) -> TransferInfo:
    """
    fetch transaction information for a given transaction hash

    Args:
        tx_hash: The transaction hash to query
        chain_type: The type of blockchain (EVM, SOL, SUI)
        chain_id: The chain ID of the blockchain (required for EVM chains)

    Returns:
        A TransferInfo object representing the transaction
    """

    if chain_id is not None:
        chain_type = get_chain_by_id(chain_id).chain_type
    if not chain_type:
        raise ValueError("Either chain_id or chain_type must be provided")

    match chain_type:
        case ChainType.EVM:
            if chain_id is None:
                raise ValueError("Chain ID must be provided for EVM chains")
            tx_info = await evm.get_transfer_details(tx_hash, chain_id)
        case ChainType.SOL:
            tx_info = await sol.get_transfer_details(tx_hash)
        case ChainType.SUI:
            # TODO!
            # tx_info = await sui.get_transfer_details(tx_hash)
            raise NotImplementedError("SUI chain not supported")
        case _:
            raise NotImplementedError(f"Chain type {chain_type} not supported")

    return tx_info
