from enum import Enum
from typing import Dict, Tuple


class NetworkId(int, Enum):
    MAINNET = 20
    SEPOLIA = 21
    ARBITRUM = 22
    AVALANCHE = 23
    BNBCHAIN = 24
    BASE = 25
    OPTIMISM = 26
    POLYGON = 27
    BLAST = 28
    ZORA = 29
    WORLDCHAIN = 30

class FactoryAddress(str, Enum):
    MAINNET = "0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f"
    SEPOLIA = "0xF62c03E08ada871A0bEb309762E260a7a6a880E6"
    ARBITRUM = "0xf1D7CC64Fb4452F05c498126312eBE29f30Fbcf9"
    AVALANCHE = "0x9e5A52f57b3038F1B8EeE45F28b3C1967e22799C"
    BNBCHAIN = "0x8909Dc15e40173Ff4699343b6eB8132c65e18eC6"
    BASE = "0x8909Dc15e40173Ff4699343b6eB8132c65e18eC6"
    OPTIMISM = "0x0c3c1c532F1e39EdF36BE9Fe0bE1410313E074Bf"
    POLYGON = "0x9e5A52f57b3038F1B8EeE45F28b3C1967e22799C"
    BLAST = "0x5C346464d33F90bABaf70dB6388507CC889C1070"
    ZORA = "0x0F797dC7efaEA995bB916f268D919d0a1950eE3C"
    WORLDCHAIN = "0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f"

class V2RouterAddress(str, Enum):
    MAINNET = "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"
    SEPOLIA = "0xeE567Fe1712Faf6149d80dA1E6934E354124CfE3"
    ARBITRUM = "0x4752ba5dbc23f44d87826276bf6fd6b1c372ad24"
    AVALANCHE = "0x4752ba5dbc23f44d87826276bf6fd6b1c372ad24"
    BNBCHAIN = "0x4752ba5dbc23f44d87826276bf6fd6b1c372ad24"
    BASE = "0x4752ba5dbc23f44d87826276bf6fd6b1c372ad24"
    OPTIMISM = "0x4A7b5Da61326A6379179b40d00F57E5bbDC962c2"
    POLYGON = "0xedf6066a2b290C185783862C7F4776A2C8077AD1"
    BLAST = "0xBB66Eb1c5e875933D44DAe661dbD80e5D9B03035"
    ZORA = "0xa00F34A632630EFd15223B1968358bA4845bEEC7"
    WORLDCHAIN = "0x541aB7c31A119441eF3575F6973277DE0eF460bd"
#
# NETWORK_ADDRESS: Dict[NetworkId, FactoryAddress] = {
#     NetworkId.MAINNET: {FactoryAddress.MAINNET},
#     NetworkId.SEPOLIA: FactoryAddress.SEPOLIA,
#     NetworkId.ARBITRUM: FactoryAddress.ARBITRUM,
#     NetworkId.AVALANCHE: FactoryAddress.AVALANCHE,
#     NetworkId.BNBCHAIN: FactoryAddress.BNBCHAIN,
#     NetworkId.BASE: FactoryAddress.BASE,
#     NetworkId.OPTIMISM: FactoryAddress.OPTIMISM,
#     NetworkId.POLYGON: FactoryAddress.POLYGON,
#     NetworkId.BLAST: FactoryAddress.BLAST,
#     NetworkId.ZORA: FactoryAddress.ZORA,
#     NetworkId.WORLDCHAIN: FactoryAddress.WORLDCHAIN,
# }

NETWORK_ADDRESS: Dict[NetworkId, Tuple[FactoryAddress, V2RouterAddress]] = {
    NetworkId.MAINNET:   (FactoryAddress.MAINNET,   V2RouterAddress.MAINNET),
    NetworkId.SEPOLIA:   (FactoryAddress.SEPOLIA,   V2RouterAddress.SEPOLIA),
    NetworkId.ARBITRUM:  (FactoryAddress.ARBITRUM,  V2RouterAddress.ARBITRUM),
    NetworkId.AVALANCHE: (FactoryAddress.AVALANCHE, V2RouterAddress.AVALANCHE),
    NetworkId.BNBCHAIN:  (FactoryAddress.BNBCHAIN,  V2RouterAddress.BNBCHAIN),
    NetworkId.BASE:      (FactoryAddress.BASE,      V2RouterAddress.BASE),
    NetworkId.OPTIMISM:  (FactoryAddress.OPTIMISM,  V2RouterAddress.OPTIMISM),
    NetworkId.POLYGON:   (FactoryAddress.POLYGON,   V2RouterAddress.POLYGON),
    NetworkId.BLAST:     (FactoryAddress.BLAST,     V2RouterAddress.BLAST),
    NetworkId.ZORA:      (FactoryAddress.ZORA,      V2RouterAddress.ZORA),
    NetworkId.WORLDCHAIN:(FactoryAddress.WORLDCHAIN,V2RouterAddress.WORLDCHAIN),
}