from typing import NamedTuple
from ..currencies.types import CurrencyBase

class Balance(NamedTuple):
    currency: CurrencyBase
    amount: int



