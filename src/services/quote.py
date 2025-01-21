from typing import List, Union

from src.utils.currencies.types import Currency, CurrencyBase
from src.utils.logging import get_logger

from .changenow import ChangeNowService, ExchangeType
from .coingecko import CoinGeckoService

from src.models.schemas.quote import CurrencyQuote


logger = get_logger(__name__)


class QuoteService():
    async def _get_quote_value_usd(
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
                        try:
                            amount_out = value_usd / to_currency.price_usd
                            est_currency_in_amount = await cn.estimate(
                                currency_in=from_currency, 
                                currency_out=to_currency,
                                amount=amount_out,
                                exchange_type=ExchangeType.REVERSE)


                            est_currency_in_value_usd = est_currency_in_amount * from_currency.price_usd
                            _quotes.append({
                                "from_currency": from_currency,
                                "to_currency": to_currency,
                                "amount_in": est_currency_in_amount,
                                "amount_out": amount_out,
                                "value_usd_in": est_currency_in_value_usd,
                            })

                        except Exception as e:
                            logger.error(f"Error estimating {from_currency.id} to {to_currency.id}: {str(e)}")
                            continue

                    if _quotes:
                        best_quote = min(_quotes, key=lambda x: x["value_usd_in"])
                        in_currency: Currency = best_quote["from_currency"]
                        in_currency.ui_amount = best_quote["amount_in"]
                        in_currency.amount = in_currency.ui_amount_to_amount(in_currency.ui_amount)

                        out_currency: Currency = best_quote["to_currency"]
                        out_currency.ui_amount = best_quote["amount_out"]
                        out_currency.amount = out_currency.ui_amount_to_amount(out_currency.ui_amount)


                        best_quote = CurrencyQuote(
                            value_usd=best_quote["value_usd_in"],
                            in_currency=in_currency,
                            out_currency=out_currency,
                        )
                        quotes.append(best_quote)

        return quotes

    async def _get_quote_currency_out(
        self,
        from_currencies: Union[List[str], List[CurrencyBase]],
        to_currency: Union[str, CurrencyBase],
        amount_out: float
    ) -> List[CurrencyQuote]:

        quotes = []
        if type(from_currencies[0]) == str:
            from_currencies = [CurrencyBase.from_id(id_) for id_ in from_currencies]
        if type(to_currency) == str:
            to_currency = CurrencyBase.from_id(to_currency)

        async with CoinGeckoService() as cg:
            from_currencies = await cg.price(currencies=from_currencies)
            to_currency = await cg.price(currencies=[to_currency])

            print(f"\t\tAMOUNT_OUT: {amount_out}")
            print("~~~ FROM CURRENCIES ~~~")
            for c in from_currencies:
                for k, v in c.model_dump().items():
                    print(f"{k}: {v}")

            print("~~~ TO CURRENCY ~~~")
            for c in to_currency:
                for k, v in c.model_dump().items():
                    print(f"{k}: {v}")

            async with ChangeNowService() as cn:
                for from_currency in from_currencies:
                    try:
                        est_currency_in_amount = await cn.estimate(
                            currency_in=from_currency, 
                            currency_out=to_currency[0],
                            amount=amount_out,
                            exchange_type=ExchangeType.REVERSE)

                        print(f"Estimate: {est_currency_in_amount}")

                        est_currency_in_value_usd = est_currency_in_amount * from_currency.price_usd
                        print(f"Estimate USD: {est_currency_in_value_usd}")

                        from_currency.ui_amount = est_currency_in_amount
                        from_currency.amount = from_currency.ui_amount_to_amount(from_currency.ui_amount)

                        out_currency: Currency = to_currency[0]
                        out_currency.ui_amount = amount_out
                        out_currency.amount = out_currency.ui_amount_to_amount(out_currency.ui_amount)


                        quotes.append(CurrencyQuote(
                            value_usd=est_currency_in_value_usd,
                            in_currency=from_currency,
                            out_currency=out_currency,
                        ))
                        print("~~~ QUOTE ~~~")
                        for q in quotes:
                            for k, v in q.model_dump().items():
                                print(f"{k}: {v}")
                    except Exception as e:
                        logger.error(f"Error estimating {from_currency.id} to {to_currency[0].id}: {str(e)}")
                        continue



        return quotes
