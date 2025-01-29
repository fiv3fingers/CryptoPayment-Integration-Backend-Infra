# utils/chains/data.py
from .types import Chain, ServiceType, NativeCurrency
from src.utils.types import ChainId, ChainType

CHAIN_DATA_MAP = {
    ChainId.BTC: Chain(
        id=ChainId.BTC,
        name="Bitcoin",
        chain_type=ChainType.UTXO,
        nativeCurrency=NativeCurrency(
            name="Bitcoin",
            ticker="BTC",
            decimals=8,
            image_uri="https://cryptologos.cc/logos/bitcoin-btc-logo.png",
            aliases={ServiceType.COINGECKO: "bitcoin", ServiceType.CHANGENOW: "btc"},
        ),
        image_uri="https://cryptologos.cc/logos/bitcoin-btc-logo.png",
        aliases={
            ServiceType.COINGECKO: "bitcoin",
            ServiceType.CHANGENOW: "btc",
        },
    ),
    ChainId.ETH: Chain(
        id=ChainId.ETH,
        name="Ethereum",
        chain_type=ChainType.EVM,
        nativeCurrency=NativeCurrency(
            name="Ether",
            ticker="ETH",
            decimals=18,
            image_uri="https://cryptologos.cc/logos/ethereum-eth-logo.png",
            aliases={ServiceType.COINGECKO: "ethereum", ServiceType.CHANGENOW: "eth"},
        ),
        image_uri="https://cryptologos.cc/logos/ethereum-eth-logo.png",
        aliases={
            ServiceType.COINGECKO: "ethereum",
            ServiceType.CHANGENOW: "eth",
            ServiceType.ALCHEMY: "eth-mainnet",
        },
    ),
    ChainId.BASE: Chain(
        id=ChainId.BASE,
        name="Base",
        chain_type=ChainType.EVM,
        nativeCurrency=NativeCurrency(
            name="Ether",
            ticker="ETH",
            decimals=18,
            image_uri="https://cryptologos.cc/logos/ethereum-eth-logo.png",
            aliases={ServiceType.COINGECKO: "ethereum", ServiceType.CHANGENOW: "eth"},
        ),
        image_uri="https://basescan.org/assets/base/image_uris/svg/logos/chain-light.svg",
        aliases={
            ServiceType.COINGECKO: "base",
            ServiceType.CHANGENOW: "base",
            ServiceType.ALCHEMY: "base-mainnet",
        },
    ),
    ChainId.SOL: Chain(
        id=ChainId.SOL,
        name="Solana",
        chain_type=ChainType.SOL,
        nativeCurrency=NativeCurrency(
            name="SOL",
            ticker="SOL",
            decimals=9,
            image_uri="https://cryptologos.cc/logos/solana-sol-logo.png",
            aliases={ServiceType.COINGECKO: "solana", ServiceType.CHANGENOW: "sol"},
        ),
        image_uri="https://cryptologos.cc/logos/solana-sol-logo.png",
        aliases={ServiceType.COINGECKO: "solana", ServiceType.CHANGENOW: "sol"},
    ),
    ChainId.SUI: Chain(
        id=ChainId.SUI,
        name="Sui",
        chain_type=ChainType.SUI,
        nativeCurrency=NativeCurrency(
            address="0x2::sui::sui",
            name="SUI",
            ticker="SUI",
            decimals=9,
            image_uri="https://cryptologos.cc/logos/sui-sui-logo.png",
            aliases={ServiceType.CHANGENOW: "sui", ServiceType.COINGECKO: "sui"},
        ),
        image_uri="https://cryptologos.cc/logos/sui-sui-logo.png",
        aliases={
            ServiceType.ALCHEMY: "sui-mainnet",
            ServiceType.CHANGENOW: "sui",
            ServiceType.COINGECKO: "sui",
        },
    ),
}
