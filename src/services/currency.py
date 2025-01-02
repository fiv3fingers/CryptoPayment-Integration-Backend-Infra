from typing import List, Optional, Dict, Tuple
from datetime import datetime, timedelta
from models.schemas.currency import Currency
from services.changenow import ChangeNowClient
from utils.logging import get_logger

from utils import evm

logger = get_logger(__name__)

class CurrencyService:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize Currency service (only runs once)"""
        if not CurrencyService._initialized:
            self._currency_cache: Dict[str, Tuple[List[Currency], datetime]] = {}
            self._cache_duration = timedelta(minutes=15)  # Cache for 15 minutes by default
            self._changenow = ChangeNowClient.get_instance()
            logger.debug("Currency service initialized")
            CurrencyService._initialized = True

    def set_cache_duration(self, minutes: int) -> None:
        """
        Set the duration for which currency data should be cached
        
        Args:
            minutes: int - Number of minutes to cache the data
        """
        self._cache_duration = timedelta(minutes=minutes)
        logger.debug(f"Cache duration set to {minutes} minutes")

    def clear_cache(self) -> None:
        """Clear the currency cache"""
        self._currency_cache.clear()
        logger.debug("Currency cache cleared")

    def _get_cache_key(self, networks: Optional[List[str]] = None, 
                      is_native: Optional[bool] = None, 
                      is_stable: Optional[bool] = None) -> str:
        """Generate a cache key based on filter parameters"""
        key_parts = []
        if networks:
            key_parts.append(f"networks={'_'.join(sorted(net.upper() for net in networks))}")
        if is_native is not None:
            key_parts.append(f"native={is_native}")
        if is_stable is not None:
            key_parts.append(f"stable={is_stable}")
        return "|".join(key_parts) if key_parts else "all"

    def get_currencies(self, 
                      networks: Optional[List[str]] = None,
                      is_native: Optional[bool] = None,
                      is_stable: Optional[bool] = None,
                      use_cache: bool = True) -> List[Currency]:
        """
        Get filtered currencies with caching
        
        Args:
            networks: Optional list of network tickers to filter by
            is_native: Optional boolean to filter native tokens
            is_stable: Optional boolean to filter stablecoins
            use_cache: Whether to use cached data
            
        Returns:
            List[Currency]: Filtered list of currencies
        """
        cache_key = self._get_cache_key(networks, is_native, is_stable)

        # Check cache if enabled
        if use_cache and cache_key in self._currency_cache:
            cached_data, cache_time = self._currency_cache[cache_key]
            if datetime.now() - cache_time < self._cache_duration:
                logger.debug(f"Returning cached currency data for key: {cache_key}")
                return cached_data
            else:
                logger.debug("Cache expired, fetching fresh data")

        # Get currencies from ChangeNow
        cn_currencies = self._changenow.get_available_currencies()
        currencies = [Currency.from_changenow(c) for c in cn_currencies]

        # Apply filters
        if networks:
            networks = [net.upper() for net in networks]  # Normalize to uppercase
            currencies = [c for c in currencies if c.network.upper() in networks]
            
        if is_native is not None:
            currencies = [c for c in currencies if c.is_native == is_native]
            
        if is_stable is not None:
            currencies = [c for c in currencies if c.is_stable == is_stable]

        # Update cache if enabled
        if use_cache:
            self._currency_cache[cache_key] = (currencies, datetime.now())
            logger.debug(f"Updated currency cache for key: {cache_key}")

        return currencies

    async def get_by_id(self, currency_id: str) -> Optional[Currency]:
        """
        Get currency by ID
        
        Args:
            currency_id: str - Currency ID to look up
            
        Returns:
            Optional[Currency]: Currency object if found, None otherwise
        """
        currencies = self.get_currencies(use_cache=True)
        return next((c for c in currencies if c.id == currency_id), None)

    @classmethod
    def get_instance(cls) -> 'CurrencyService':
        """Get or create the singleton instance"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton instance (useful for testing)"""
        cls._instance = None
        cls._initialized = False
        logger.debug("Currency service instance reset")




    def get_user_currencies(self, wallet_address: str, chain_name: str) -> List[Currency]:
        """
        Get list of currencies available to a user based on their wallet address
        
        Args:
            wallet_address: str - User's wallet address
            chain_id: str - Chain ID to query
            
        Returns:
            List[Currency]: List of currencies available to the user
        """
        # Get all available currencies
        supported_currencies = self.get_currencies(use_cache=True, networks=[chain_name], is_native=False)

        print("Supported currencies: ", supported_currencies)
        
        # Get user's tokens on the specified chain
        user_token_balances = evm.get_token_balances(wallet_address, chain_name)
        user_native_balance = evm.get_native_balance(wallet_address, chain_name)

        contract_addresses = [t.contractAddress.lower() for t in user_token_balances if t.tokenBalance > 0]
        relevant_currencies = [c for c in supported_currencies if c.token_contract.lower() in contract_addresses]

        return relevant_currencies

