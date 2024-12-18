from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
import json
import os
import requests
from models.schemas.changenow import (
    TransactionType,
    FlowType,
    ExchangeEstimate,
    ExchangeTransaction,
    CreateExchangeRequest,
    EstimateRequest,
    ExchangeStatusResponse
)

from utils.logging import get_logger
logger = get_logger("changenow")

class ChangeNowAPIError(Exception):
    """Custom exception for ChangeNow API errors"""
    def __init__(self, message: str, response: Optional[requests.Response] = None):
        self.message = message
        self.response = response
        super().__init__(self.message)

class ChangeNowClient:
    def __init__(self, api_key: Optional[str] = None):
        """Initialize ChangeNow client with API key"""
        self.api_key = api_key or os.getenv('CHANGENOW_API_KEY')
        if not self.api_key:
            raise ValueError("API key must be provided or set in CHANGENOW_API_KEY environment variable")
        
        self.base_url = "https://api.changenow.io/v2"
        self.headers = {
            'Content-Type': 'application/json',
            'x-changenow-api-key': self.api_key
        }
        self.session = requests.Session()
        logger.debug("ChangeNow client initialized")

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
