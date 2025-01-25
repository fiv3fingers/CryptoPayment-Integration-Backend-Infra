from .types import Currency, CurrencyBase


def to_currency_base(c):
    if type(c) == Currency or type(c) == CurrencyBase:
        return c
    elif type(c) == str:
        return CurrencyBase.from_id(c)
    else:
        raise TypeError(f"Invalid currency type: {type(c)} {c}")
