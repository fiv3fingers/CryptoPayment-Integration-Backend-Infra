from typing import List, NamedTuple, Union
from src.utils.currencies.types import CurrencyBase


class Balance(NamedTuple):
    currency: CurrencyBase
    amount: int

class TransferInfo(NamedTuple):
    currency: CurrencyBase
    amount: int
    source_address: str
    destination_address: str
    confirmed: bool

class UTXOOutput(NamedTuple):
    destination_address: str
    amount: int

class UTXOTransferInfo(NamedTuple):
    currency: CurrencyBase
    source_address: str
    confirmed: bool
    outputs: List[UTXOOutput]
    
TransferInfoType = Union[UTXOTransferInfo, TransferInfo]
