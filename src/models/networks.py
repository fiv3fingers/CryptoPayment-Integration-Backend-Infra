from typing import Optional, List
from pydantic import BaseModel
from enum import Enum

# we have chainTypes, chainIds and chain data.

class ChainType(str, Enum):
    EVM = "EVM",
    SOL = "SOL",
    SUI = "SUI",
    TRON = "TRON",
    # Unspent transaction output (e.g. Bitcoin, Litecoin, Dogecoin)
    UTXO = "UTXO",

# Can we add
class ChainId(int, Enum):
    ETH = 1
    OPTIMISM = 10
    BSC = 56
    POLYGON = 137
    FANTOM = 250
    ZKSYNC = 324
    BASE = 8453
    ARBITRUM = 42161
    AVALANCHE = 43114
    BLAST = 81457

    SEPOLIA = 11155111
    SEPBASE = 84532
    SEPARB = 421614
    SEPOPT = 11155420

    BTC = 20000000000001
    BCH = 20000000000002
    LTC = 20000000000003
    DOGE = 20000000000004

    SOL = 30000000000001
    SUI = 30000000000002
    TRON = 30000000000003
    XRPL = 30000000000004

class NativeCurrency(BaseModel):
    name: str
    symbol: str
    decimals: int

class ChainClass(BaseModel):
    id: str
    name: str
    shortName: str
    type: ChainType
    chainId: Optional[int]
    nativeCurrency: NativeCurrency
    logo: str

# SUPPORTED CHAINS

# I feel this should be a mapping not an enum
CHAIN_DATA_MAP = {
    ChainId.ETH: ChainClass(
        id="ETHEREUM",
        name="Ethereum",
        shortName="eth",
        type=ChainType.EVM,
        chainId=ChainId.ETH,
        nativeCurrency=NativeCurrency(
            name="Ether",
            symbol="ETH",
            decimals=18
        ),
        logo="https://cryptologos.cc/logos/ethereum-eth-logo.png"
    ),
    ChainId.BASE: ChainClass(
        id="BASE",
        name="Base",
        shortName="base",
        type=ChainType.EVM,
        chainId=ChainId.BASE,
        nativeCurrency=NativeCurrency(
            name="Ether",
            symbol="ETH",
            decimals=18
        ),
        logo="https://basescan.org/assets/base/images/svg/logos/chain-light.svg"
    ),
    ChainId.SOL: ChainClass(
        id="SOLANA",
        name="Solana",
        shortName="sol",
        type=ChainType.SOL,
        chainId=ChainId.SOL,
        nativeCurrency=NativeCurrency(
            name="SOL",
            symbol="SOL",
            decimals=9
        ),
        logo="https://cryptologos.cc/logos/solana-sol-logo.png"
    ),
    ChainId.SUI: ChainClass(
        id="SUI",
        name="Sui",
        shortName="sui",
        type=ChainType.SUI,
        chainId=ChainId.SUI,
        nativeCurrency=NativeCurrency(
            name="SUI",
            symbol="SUI",
            decimals=9
        ),
        logo="https://cryptologos.cc/logos/sui-sui-logo.png"
    )
}

# We want to use enum / typed values, also works better with the docs.

# @classmethod
# def get_by_name(cls, name: str) -> Optional[ChainClass]:
#     """Get chain by name or short name"""
#     return next(
#         (chain.value for chain in cls 
#             if chain.value.name.lower() == name.lower() 
#             or chain.value.shortName.lower() == name.lower()),
#         None
#     )

def get_by_chain_id(chain_id: ChainId) -> Optional[ChainClass]:
    """
    Get chain information by chain ID.

    :param chain_id: ChainId enum value
    :return: ChainClass object or None if not found
    """
    if not isinstance(chain_id, ChainId):
        raise ValueError(f"Invalid ChainId: {chain_id}")
    return CHAIN_DATA_MAP.get(chain_id)


def get_by_type(chain_type: ChainType) -> List[ChainClass]:
    """
    Get all chains matching the specified ChainType.

    :param chain_type: ChainType enum value
    :return: List of ChainClass objects
    """
    if not isinstance(chain_type, ChainType):
        raise ValueError(f"Invalid ChainType: {chain_type}")
    return [chain for chain in CHAIN_DATA_MAP.values() if chain.type == chain_type]

def list_all() -> List[ChainClass]:
    """
    List all chains.

    :return: List of all ChainClass objects
    """
    return list(CHAIN_DATA_MAP.values())
