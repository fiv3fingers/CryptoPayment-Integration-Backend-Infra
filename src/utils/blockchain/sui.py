import os
from dataclasses import dataclass
import aiohttp
import asyncio
from typing import List
from src.utils.logging import get_logger
from src.utils.currencies.types import CurrencyBase 
from src.utils.chains.types import ChainId
from .types import Balance

logger = get_logger(__name__)
SUI_RPC_URL = os.getenv("SUI_RPC_URL")
if SUI_RPC_URL is None:
    raise ValueError("SUI_RPC_URL is not set")

HEADERS = {
    "Content-Type": "application/json",
}

@dataclass
class TokenBalance:
    coin_type: str    # Address of the coin
    balance: int      # Raw balance
    balance_ui: float # UI balance (considering decimals)
    decimals: int
    symbol: str
    description: str
    iconUrl: str

async def get_token_balances(session: aiohttp.ClientSession, address: str) -> List[Balance]:
    """
    fetch all token balances for a Sui wallet address.
    """
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "suix_getAllBalances",
        "params": [address]
    }
    
    try:
        async with session.post(SUI_RPC_URL, json=payload, headers=HEADERS) as response:
            response.raise_for_status()
            data = await response.json()
            result = data.get("result", [])
            
            token_balances = []
            for balance in result:
                coin_type = balance.get("coinType")
                total_balance = int(balance.get("totalBalance", "0"))
                
                token_balances.append(
                    Balance(
                        currency=CurrencyBase(
                            address=coin_type,
                            chain_id=ChainId.SUI
                        ),
                        amount=total_balance
                    )
                )
            
            return token_balances
            
    except aiohttp.ClientError as e:
        logger.error(f"Failed to get token balances for {address}: {str(e)}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error while getting token balances for {address}: {str(e)}")
        return []

async def get_wallet_balances(address: str) -> List[Balance]:
    """
    Fetch all token balances for a given wallet address.
    """
    async with aiohttp.ClientSession() as session:
        token_balances = await get_token_balances(session, address)
        return token_balances




# Example usage
if __name__ == "__main__":
    async def main():
        test_address = "0xc3af1f2ca3dc69a70616fa3707f67a9367f8d01d4b75a40520b931d42241695e"
        balances = await get_wallet_balances(test_address)
        print(f"Found {len(balances)} token balances for {test_address}")
        for balance in balances:
            print(f"\t{balance}")

    # Run the async main function
    asyncio.run(main())
