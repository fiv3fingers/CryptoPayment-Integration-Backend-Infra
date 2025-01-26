# utils/coingecko.py
from typing import Dict, Optional, List, Union
import requests

from src.utils.types import ServiceType
from src.utils.currencies.types import Currency, CurrencyBase
from .types import Price, VSCurrency, PriceParams, TokenInfo


class CoinGeckoAPI:
    """Strongly typed wrapper around CoinGecko API."""

    BASE_URL = "https://api.coingecko.com/api/v3"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.session = requests.Session()
        if api_key:
            self.session.headers.update({"x-cg-api-key": api_key})
        self.session.headers.update({"accept": "application/json"})

    def _get_token_info(self, currency: CurrencyBase) -> Optional[TokenInfo]:
        """
        Get detailed information about a token by its contract address.

        Args:
            platform_id: Platform identifier (e.g., "ethereum")
            contract_address: Token contract address

        Returns:
            TokenInfo if found, None otherwise
        """
        try:
            if currency.is_native:
                token_id = currency.chain.nativeCurrency.get_alias(
                    ServiceType.COINGECKO
                )
                url = f"{self.BASE_URL}/coins/{token_id}"
            else:
                contract_address = currency.address
                platform_id = currency.chain.get_alias(ServiceType.COINGECKO)
                url = f"{self.BASE_URL}/coins/{platform_id}/contract/{contract_address}"

            response = self.session.get(url)

            if response.status_code == 429:
                raise Exception("Rate limit reached")

            response.raise_for_status()
            data = response.json()

            return TokenInfo(**data)
        except Exception as e:
            print(f"Error fetching token info for {currency}: {e}")
            return None

    def _get_coingecko_id(
        self, currency: Union[CurrencyBase, Currency]
    ) -> Union[str, None]:
        # TODO: Add cashing mechanism
        """Get CoinGecko ID for a currency."""

        token_info = self._get_token_info(currency)
        if token_info:
            return token_info.id

        return None

    def _get_prices(
        self,
        ids: List[str],
        vs_currency: VSCurrency = VSCurrency.USD,
        precision: Optional[int] = 8,
    ) -> Dict[str, Price]:

        params = PriceParams(
            ids=ids,
            include_market_cap=False,
            include_24hr_vol=False,
            include_24hr_change=False,
            include_last_updated_at=True,
            precision=precision,
            vs_currencies=[vs_currency],
        )

        try:
            response = self.session.get(f"{self.BASE_URL}/simple/price", params=params)

            if response.status_code == 429:
                raise Exception("Rate limit reached")

            response.raise_for_status()
            data = response.json()

            result = {}
            for id in ids:
                coin_data = data.get(id)
                price = coin_data.get(vs_currency)
                last_updated_at = coin_data.get("last_updated_at")

                result[id] = Price(
                    currency_id=id,
                    price=price,
                    vs_currency=vs_currency,
                    last_updated_at=last_updated_at,
                )
            return result

        except Exception as e:
            print(f"Error fetching prices: {e}")
            return {}

    def get_prices(
        self,
        currencies: List[Union[Currency, CurrencyBase]],
        vs_currency: VSCurrency = VSCurrency.USD,
        precision: Optional[int] = 8,
    ) -> List[Price]:
        """Get current price of currency in USD."""

        # Get CoinGecko IDs for each currency
        id_currencies = list(
            {
                (id, currency)
                for currency in currencies
                if (id := self._get_coingecko_id(currency))
            }
        )

        for id, currency in id_currencies:
            print(f"CoinGecko ID for {currency}: {id}")

        params = PriceParams(
            ids=[id for id, _ in id_currencies],
            include_market_cap=False,
            include_24hr_vol=False,
            include_24hr_change=False,
            include_last_updated_at=True,
            precision=precision,
            vs_currencies=[vs_currency],
        )

        try:
            response = self.session.get(
                f"{self.BASE_URL}/simple/price", params=params.to_query_params()
            )

            if response.status_code == 429:
                raise Exception("Rate limit reached")

            response.raise_for_status()
            data = response.json()

            result = []
            for id, currency in id_currencies:
                coin_data = data.get(id)
                price = coin_data.get(vs_currency)
                last_updated_at = coin_data.get("last_updated_at")

                result.append(
                    Price(
                        currency_id=currency.id,
                        price=price,
                        vs_currency=vs_currency,
                        last_updated_at=last_updated_at,
                    )
                )

            return result

        except Exception as e:
            print(f"Error fetching price for {currency}: {e}")
            return []

    def get_token_info(
        self, currency: Union[Currency, CurrencyBase]
    ) -> Optional[Currency]:
        """Get detailed information about a token."""

        token_info = self._get_token_info(currency)

        if token_info:
            platform_id = token_info.asset_platform_id

            return Currency(
                chain_id=currency.chain_id,
                address=currency.address,
                name=token_info.name,
                ticker=token_info.symbol,
                decimals=token_info.detail_platforms.get(platform_id).decimal_place,
                image=token_info.image.small,
            )

        return None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()
