from typing import NamedTuple
from src.utils.currencies.types import CurrencyBase


class Balance(NamedTuple):
    currency: CurrencyBase
    amount: int
