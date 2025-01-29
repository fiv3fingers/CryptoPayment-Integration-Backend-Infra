import os
from .types import Chain
from src.utils.types import ChainId, ChainType, ServiceType
from .data import CHAIN_DATA_MAP


def get_chain_by_id(chain_id: ChainId) -> Chain:
    """Get chain data by its ID."""
    chain = CHAIN_DATA_MAP.get(chain_id)
    if chain is None:
        raise ValueError(f"Chain {chain_id} not found")
    return chain


def get_chains_by_type(chain_type: ChainType) -> list[Chain]:
    """Get chains by their type."""
    return [
        chain for chain in CHAIN_DATA_MAP.values() if chain.chain_type == chain_type
    ]


def get_chain_by_name(chain_name: str) -> Chain:
    """Get chain data by its name."""
    for chain in CHAIN_DATA_MAP.values():
        if chain.name.lower() == chain_name.lower():
            return chain
    raise ValueError(f"Chain {chain_name} not found")


def get_all_chains() -> list[Chain]:
    """Get all chains."""
    return list(CHAIN_DATA_MAP.values())


def get_rpc_by_chain_id(chain_id: ChainId) -> str:
    """Get RPC URL by chain ID."""
    chain = get_chain_by_id(chain_id)

    if chain.chain_type == ChainType.EVM:
        alias = chain.get_alias(ServiceType.ALCHEMY)
        ALCHEMY_API_KEY = os.getenv("ALCHEMY_API_KEY")
        if ALCHEMY_API_KEY is None:
            raise ValueError("ALCHEMY_API_KEY not found")
        rpc_url: str = f"https://{alias}.g.alchemy.com/v2/{ALCHEMY_API_KEY}"
        return rpc_url
    elif chain.chain_type == ChainType.SOL:
        SOLANA_RPC_URL = os.getenv("SOLANA_RPC_URL")
        if SOLANA_RPC_URL is None:
            raise ValueError("SOLANA_RPC_URL not found")
        return SOLANA_RPC_URL
    elif chain.chain_type == ChainType.SUI:
        SUI_RPC_URL = os.getenv("SUI_RPC_URL")
        if SUI_RPC_URL is None:
            raise ValueError("SUI_RPC_URL not found")
        return SUI_RPC_URL
    else:
        raise ValueError(f"Chain {chain_id} not found")
