from enum import Enum
from typing import Dict


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


class ChainType(str, Enum):
    EVM = "EVM"
    SOL = "SOL"
    SUI = "SUI"
    TRON = "TRON"
    UTXO = "UTXO"


class ServiceType(str, Enum):
    ALCHEMY = "ALCHEMY"
    COINGECKO = "COINGECKO"
    CHANGENOW = "CHANGENOW"
    JUPITER = "JUPITER"


class AuthHeaderType(Dict):
    APIKey: str
    signature: str
    timestamp: str


