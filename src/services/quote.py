from typing import List, Union

from src.utils.currencies.types import CurrencyBase
from src.utils.logging import get_logger

from .changenow import ChangeNowService, ExchangeType
from .coingecko import CoinGeckoService

from src.models.schemas.quote import CurrencyQuote


logger = get_logger(__name__)


class QuoteService():
    async def _get_quote(
        self,
        from_currencies: Union[List[str], List[CurrencyBase]],
        to_currencies: Union[List[str], List[CurrencyBase]],
        value_usd: float,
    ) -> List[CurrencyQuote]:
        quotes = []
        if type(from_currencies[0]) == str:
            from_currencies = [CurrencyBase.from_id(id_) for id_ in from_currencies]
        if type(to_currencies[0]) == str:
            to_currencies = [CurrencyBase.from_id(id_) for id_ in to_currencies]

        async with CoinGeckoService() as cg:
            from_currencies = await cg.price(currencies=from_currencies)
            to_currencies = await cg.price(currencies=to_currencies)

            async with ChangeNowService() as cn:
                for from_currency in from_currencies:
                    _quotes = []
                    for to_currency in to_currencies:
                        est_currency_in_amount = await cn.estimate(
                            currency_in=from_currency, 
                            currency_out=to_currency,
                            amount=value_usd / to_currency.price_usd,
                            type=ExchangeType.REVERSE)

                        est_currency_in_value_usd = est_currency_in_amount * from_currency.price_usd
                        _quotes.append({
                            "from_currency": from_currency,
                            "to_currency": to_currency,
                            "amount_in": est_currency_in_amount,
                            "value_usd_in": est_currency_in_value_usd,
                        })

                    best_quote = min(_quotes, key=lambda x: x["value_usd_in"])
                    best_quote = CurrencyQuote(
                        currency=best_quote["from_currency"],
                        amount=best_quote["amount_in"],
                        value_usd=best_quote["value_usd_in"],
                        currency_out=best_quote["to_currency"]
                    )
                    quotes.append(best_quote)

        return quotes

