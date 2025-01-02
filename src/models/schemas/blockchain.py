from typing import Optional 
from pydantic import BaseModel, Field

class Token(BaseModel):
    address: str = Field(examples=["0x1234...1324"])
    decimals: int = Field(examples=[18])
    chain_id: str = Field(examples=[1])

    name: str = Field(examples=["Ethereum"])
    symbol: str = Field(examples=["ETH"])
    logo: Optional[str] = Field(examples=["https://cryptologos.cc/logos/ethereum-eth-logo.png"])
    description: Optional[str] = Field(examples=["Ethereum is a decentralized platform that runs smart contracts: applications that run exactly as programmed without any possibility of downtime, fraud or third-party interference."])

    price_usd: Optional[float] = Field(examples=[2000.00])
    is_stablecoin: Optional[bool] = Field(examples=[False])


class TokenBalance(BaseModel):
    token: Token
    balance: int = Field(examples=[1000000000000000000])  # 1 ETH = 10^18 wei

