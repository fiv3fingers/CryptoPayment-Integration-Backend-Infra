import asyncio
from typing import List, Optional

from src.utils.blockchain import utxo
from src.utils.chains.queries import get_chains_by_type
from .types import Balance
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
    evm_chain_ids: Optional[List[ChainId]] = None,
    filter_zero: bool = True,
) -> List[CurrencyBase]:
    """
    fetch all currencies (tokens) present in a wallet.

    Args:
        wallet_address: The address to check currencies for
        chain_type: The type of blockchain (EVM, SOL, SUI)
        evm_chain_ids: Optional specific chains to query (for EVM chains)
        filter_zero: Whether to exclude currencies with zero balance

    Returns:
        A list of CurrencyBase objects representing the currencies in the wallet
    """
    balances = await get_wallet_balances(
        wallet_address=wallet_address,
        chain_type=chain_type,
        evm_chain_ids=evm_chain_ids,
        filter_zero=filter_zero,
    )
    return [b.currency for b in balances]
