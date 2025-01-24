from .types import Chain
from src.utils.types import ChainId, ChainType
from .data import CHAIN_DATA_MAP


def get_chain_by_id(chain_id: ChainId) -> Chain:
    """Get chain data by its ID."""
    chain = CHAIN_DATA_MAP.get(chain_id)
    if chain is None:
        raise ValueError(f"Chain {chain_id} not found")
    return chain

def get_chains_by_type(chain_type: ChainType) -> list[Chain]:
    """Get chains by their type."""
    return [chain for chain in CHAIN_DATA_MAP.values() if chain.chain_type == chain_type]

def get_chain_by_name(chain_name: str) -> Chain:
    """Get chain data by its name."""
    for chain in CHAIN_DATA_MAP.values():
        if chain.name.lower() == chain_name.lower():
            return chain
    raise ValueError(f"Chain {chain_name} not found")

def get_all_chains() -> list[Chain]:
    """Get all chains."""
    return list(CHAIN_DATA_MAP.values())
