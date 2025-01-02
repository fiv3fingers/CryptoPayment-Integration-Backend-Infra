from pydantic import BaseModel
from typing import Optional
from .changenow import Currency as ChangeNowCurrency

class Currency(BaseModel):
    id: str
    ticker: str
    name: str
    image: str
    network: str
    network_name: str
    is_stable: bool
    is_native: bool = False
    token_contract: Optional[str] = None

    @classmethod
    def from_changenow(cls, changenow_currency: ChangeNowCurrency) -> "Currency":
        # the network name is either the name of the token (native token) or its inside the parentheis: USDC (Ethereum), USDC (Algorand)
        if "(" in changenow_currency.name:
            network_name = changenow_currency.name.split("(")[1].replace(")", "")
        else:
            network_name = changenow_currency.name

        if changenow_currency.token_contract is None:
            is_native = True
            _id = f"{changenow_currency.ticker}-{changenow_currency.network}"
        else:
            is_native = False
            _id = f"{changenow_currency.ticker}-{changenow_currency.network}-{changenow_currency.token_contract}"


        return cls(
            ticker=changenow_currency.ticker,
            name=changenow_currency.name,
            image=changenow_currency.image,
            is_stable=changenow_currency.is_stable,
            is_native=is_native,
            network=changenow_currency.network,
            token_contract=changenow_currency.token_contract,
            id=_id,
            network_name=network_name
        )

class Balance(BaseModel):
    currency: Currency
    amount: float
