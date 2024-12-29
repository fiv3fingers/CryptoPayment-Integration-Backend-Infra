from typing import Optional, List
from pydantic import BaseModel
from enum import Enum

class ChainType(str, Enum):
    EVM = "EVM"
    SOL = "SOL"
    SUI = "SUI"
    UTXO = "UTXO"


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
class Chain(Enum):
    ETHEREUM = ChainClass(
        id="ETHEREUM",
        name="Ethereum",
        shortName="eth",
        type=ChainType.EVM,
        chainId=1,
        nativeCurrency=NativeCurrency(
            name="Ether",
            symbol="ETH",
            decimals=18
        ),
        logo="https://cryptologos.cc/logos/ethereum-eth-logo.png"
    )
    BASE = ChainClass(
        id="BASE",
        name="Base",
        shortName="base",
        type=ChainType.EVM,
        chainId=8453,
        nativeCurrency=NativeCurrency(
            name="Ether",
            symbol="ETH",
            decimals=18
        ),
        logo="https://basescan.org/assets/base/images/svg/logos/chain-light.svg"
    )
    SOLANA = ChainClass(
        id="SOLANA",
        name="Solana",
        shortName="sol",
        type=ChainType.SOL,
        chainId=None,
        nativeCurrency=NativeCurrency(
            name="SOL",
            symbol="SOL",
            decimals=9
        ),
        logo="https://cryptologos.cc/logos/solana-sol-logo.png"
    )

    @classmethod
    def get_by_name(cls, name: str) -> Optional[ChainClass]:
        """Get chain by name or short name"""
        return next(
            (chain.value for chain in cls 
             if chain.value.name.lower() == name.lower() 
             or chain.value.shortName.lower() == name.lower()),
            None
        )

    @classmethod
    def get_by_chain_id(cls, chain_id: int) -> Optional[ChainClass]:
        """Get chain by chain ID"""
        return next(
            (chain.value for chain in cls if chain.value.chainId == chain_id),
            None
        )

    @classmethod
    def get_by_id(cls, chain_id: str) -> Optional[ChainClass]:
        """Get chain by ID"""
        return next(
            (chain.value for chain in cls if chain.value.id == chain_id),
            None
        )

    @classmethod
    def get_evm_chains(cls) -> List[ChainClass]:
        """Get all EVM chains"""
        return [chain.value for chain in cls if chain.value.type == ChainType.EVM]

    @classmethod
    def list_all(cls) -> List[ChainClass]:
        """Get all chains"""
        return [chain.value for chain in cls]
