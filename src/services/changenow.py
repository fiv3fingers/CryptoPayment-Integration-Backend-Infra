from typing import Optional, List, Dict, Tuple
from pydantic import BaseModel, Field, ConfigDict
import json
import os
import requests
from datetime import datetime, timedelta
from models.schemas.changenow import (
    TransactionType,
    FlowType,
    ExchangeEstimate,
    ExchangeTransaction,
    CreateExchangeRequest,
    EstimateRequest,
    ExchangeStatusResponse,
    Currency
)

from models.schemas.currency import Currency as CurrencyModel
from utils.logging import get_logger

logger = get_logger("changenow")

class ChangeNowAPIError(Exception):
    """Custom exception for ChangeNow API errors"""
    def __init__(self, message: str, response: Optional[requests.Response] = None):
        self.message = message
        self.response = response
        super().__init__(self.message)

class ChangeNowClient:
    _instance = None
    _initialized = False

    def __new__(cls, api_key: Optional[str] = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, api_key: Optional[str] = None):
        """Initialize ChangeNow client with API key (only runs once)"""
        if not ChangeNowClient._initialized:
            self.api_key = api_key or os.getenv('CHANGENOW_API_KEY')
            if not self.api_key:
                raise ValueError("API key must be provided or set in CHANGENOW_API_KEY environment variable")
            
            self.base_url = "https://api.changenow.io/v2"
            self.headers = {
                'Content-Type': 'application/json',
                'x-changenow-api-key': self.api_key
            }
            self.session = requests.Session()
            # Initialize cache attributes
            self._currency_cache: Dict[str, Tuple[List[Currency], datetime]] = {}
            self._cache_duration = timedelta(minutes=15)  # Cache for 15 minutes by default
            logger.debug("ChangeNow client initialized")
            ChangeNowClient._initialized = True

    def _handle_response(self, response: requests.Response, operation: str) -> dict:
        """Handle API response and log appropriately"""
        try:
            response_data = response.json()
            logger.debug(f"{operation} Response: {json.dumps(response_data, indent=2)}")
            
            if response.status_code != 200:
                logger.error(f"{operation} failed with status {response.status_code}")
                logger.error(f"Error response: {response.text}")
                response.raise_for_status()
                
            return response_data
        except requests.exceptions.JSONDecodeError:
            logger.error(f"Failed to decode JSON response for {operation}")
            logger.error(f"Raw response: {response.text}")
            raise ChangeNowAPIError(f"Invalid JSON response for {operation}")
        except requests.exceptions.RequestException as e:
            logger.error(f"{operation} request failed: {str(e)}")
            raise ChangeNowAPIError(f"{operation} request failed", response=response)

    def set_cache_duration(self, minutes: int) -> None:
        """
        Set the duration for which currency data should be cached
        
        Args:
            minutes: int - Number of minutes to cache the data
        """
        self._cache_duration = timedelta(minutes=minutes)
        logger.debug(f"Cache duration set to {minutes} minutes")

    def clear_currency_cache(self) -> None:
        """Clear the currency cache"""
        self._currency_cache.clear()
        logger.debug("Currency cache cleared")

    def get_available_currencies(
        self,
        active: Optional[bool] = None,
        flow: Optional[str] = "standard",
        buy: Optional[bool] = None,
        sell: Optional[bool] = None,
        use_cache: bool = True
    ) -> List[Currency]:
        """
        Get list of available currencies with optional filters
        
        Args:
            active: Optional[bool] - If true, return only active currencies
            flow: Optional[str] - Type of exchange flow ("standard" or "fixed-rate")
            buy: Optional[bool] - If true, return only currencies available for buy
            sell: Optional[bool] - If true, return only currencies available for sell
            
        Returns:
            List[Currency]: List of available currencies matching the criteria
        """
        operation = "Get Available Currencies"
        url = f"{self.base_url}/exchange/currencies"

        # Create cache key from parameters
        cache_key = json.dumps({
            'active': active,
            'flow': flow,
            'buy': buy,
            'sell': sell
        }, sort_keys=True)

        # Check cache if enabled
        if use_cache and cache_key in self._currency_cache:
            cached_data, cache_time = self._currency_cache[cache_key]
            if datetime.now() - cache_time < self._cache_duration:
                logger.debug("Returning cached currency data")
                return cached_data
            else:
                logger.debug("Cache expired, fetching fresh data")
                
        # Build query parameters
        params = {}
        if active is not None:
            params['active'] = str(active).lower()
        if flow:
            params['flow'] = flow
        if buy is not None:
            params['buy'] = str(buy).lower()
        if sell is not None:
            params['sell'] = str(sell).lower()
            
        logger.debug(f"Requesting {operation} with params: {json.dumps(params, indent=2)}")
        
        try:
            response = self.session.get(url, headers=self.headers, params=params)
            response_data = self._handle_response(response, operation)
            currencies = [Currency.model_validate(currency) for currency in response_data]
            
            # Update cache if caching is enabled
            if use_cache:
                self._currency_cache[cache_key] = (currencies, datetime.now())
                logger.debug("Updated currency cache")
                
            return currencies
        except Exception as e:
            logger.exception(f"Failed to get available currencies: {str(e)}")
            raise

    def get_estimated_exchange_amount(self, request: EstimateRequest) -> ExchangeEstimate:
        """Get estimated exchange amount for given parameters"""
        operation = "Exchange Estimation"
        url = f"{self.base_url}/exchange/estimated-amount"
        
        params = request.model_dump(by_alias=True)
        logger.debug(f"Requesting {operation} with params: {json.dumps(params, indent=2)}")
        
        try:
            response = self.session.get(url, headers=self.headers, params=params)
            response_data = self._handle_response(response, operation)
            return ExchangeEstimate.model_validate(response_data)
        except Exception as e:
            logger.exception(f"Failed to get exchange estimate: {str(e)}")
            raise

    def create_exchange_transaction(self, request: CreateExchangeRequest) -> ExchangeTransaction:
        """Create a new exchange transaction"""
        operation = "Create Exchange"
        url = f"{self.base_url}/exchange"
        
        # Format data for the API
        data = {
            "fromCurrency": request.from_currency,
            "toCurrency": request.to_currency,
            "fromNetwork": request.from_network,
            "toNetwork": request.to_network,
            "fromAmount": f"{float(request.from_amount):.5}",
            "toAmount": "",
            "address": request.address,
            "extraId": request.extra_id,
            "refundAddress": request.refund_address,
            "refundExtraId": request.refund_extra_id,
            "userId": request.user_id,
            "payload": request.payload,
            "contactEmail": request.contact_email,
            "source": request.source,
            "flow": request.flow.value,
            "type": request.type.value,
            "rateId": request.rate_id
        }
        
        logger.debug(f"Creating exchange transaction with data: {json.dumps(data, indent=2)}")
        
        try:
            response = self.session.post(url, headers=self.headers, data=json.dumps(data))
            response_data = self._handle_response(response, operation)
            return ExchangeTransaction.model_validate(response_data)
        except Exception as e:
            logger.exception(f"Failed to create exchange transaction: {str(e)}")
            raise

    def get_exchange_status(self, id: str) -> ExchangeStatusResponse:
        """Get status of an exchange transaction"""
        operation = "Exchange Status"
        url = f"{self.base_url}/exchange/by-id"
        
        params = {"id": id}
        logger.debug(f"Getting exchange status for transaction ID: {id}")
        
        try:
            response = self.session.get(url, headers=self.headers, params=params)
            response_data = self._handle_response(response, operation)
            return ExchangeStatusResponse.model_validate(response_data)
        except Exception as e:
            logger.exception(f"Failed to get exchange status: {str(e)}")
            raise

    @classmethod
    def get_instance(cls, api_key: Optional[str] = None) -> 'ChangeNowClient':
        """Get or create the singleton instance"""
        if cls._instance is None:
            cls._instance = cls(api_key)
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton instance (useful for testing)"""
        cls._instance = None
        cls._initialized = False
        logger.debug("ChangeNow client instance reset")
