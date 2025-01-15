# utils/chains/types.py
from typing import Optional, Dict
from pydantic import BaseModel

from src.utils.types import ChainType, ServiceType, ChainId


class AliasModel(BaseModel):
    aliases: Optional[Dict[ServiceType, str]] = None

    def get_alias(self, service: ServiceType) -> Optional[str]:
        if self.aliases:
            return self.aliases.get(service)

class NativeCurrency(AliasModel):
    address: Optional[str] = None
    name: str
    ticker: str
    decimals: int
    image: str
    #aliases: Optional[Dict[ServiceType, str]] = None


class Chain(AliasModel):
    id: ChainId
    name: str
    type: ChainType
    image: str
    nativeCurrency: NativeCurrency
    #aliases: Optional[Dict[ServiceType, str]] = None


