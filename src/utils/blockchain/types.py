from typing import NamedTuple
from src.utils.currencies.types import CurrencyBase


class Balance(NamedTuple):
    currency: CurrencyBase
    amount: int


class TransferInfo(NamedTuple):
    currency: CurrencyBase
    source_address: str
    destination_address: str
    amount: int
