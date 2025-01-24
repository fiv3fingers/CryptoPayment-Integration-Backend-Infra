from typing import List

from src.utils.types import ChainId, ChainType

from src.utils.currencies.types import CurrencyBase
from src.utils.chains.queries import get_chain_by_id

from .types import Balance


from . import evm, sol, sui

def get_wallet_balances(address: str, chain_id: ChainId, filter_zero=True) -> List[Balance]:
    chain = get_chain_by_id(chain_id)
    chain_type = chain.type

    try:
        if chain_type == ChainType.EVM:
            r = evm.get_wallet_balances(address, chain_id)
        elif chain_type == ChainType.SOL:
            r = sol.get_wallet_balances(address)
        elif chain_type == ChainType.SUI:
            r =  sui.get_wallet_balances(address)
        else:
            raise NotImplementedError(f"Chain type {chain_type} not supported")

        if filter_zero:
            r = [b for b in r if b.amount > 0]

        return r
    except Exception as e:
        print(f"An error occurred in fetching balance: {e}")
        return []

def get_wallet_currencies(address: str, chain_id: ChainId, filter_zero=True) -> List[CurrencyBase]:
    balances = get_wallet_balances(address, chain_id, filter_zero)
    return [b.currency for b in balances]
