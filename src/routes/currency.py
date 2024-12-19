"""
API routes for currency operations
"""
from fastapi import APIRouter, Query
from typing import List, Optional
from services.currency import CurrencyService
from models.schemas.currency import Currency

router = APIRouter(prefix="/currencies", tags=["currencies"])

@router.get("/all", response_model=List[Currency])
async def get_all_currencies():
    """Get all available currencies."""
    currency_service = CurrencyService.get_instance()
    return currency_service.get_currencies()

@router.get("", response_model=List[Currency])
async def get_filtered_currencies(
    networks: Optional[List[str]] = Query(None, description="Filter by network (e.g., ETH, BTC)"),
    is_native: Optional[bool] = Query(None, description="Filter by native token status"),
    is_stable: Optional[bool] = Query(None, description="Filter by stablecoin status")
):
    """
    Get currencies with optional filters.
    
    - **networks**: Optional list of network tickers to filter by
    - **is_native**: Optional boolean to filter native tokens
    - **is_stable**: Optional boolean to filter stablecoins
    """
    currency_service = CurrencyService.get_instance()
    return currency_service.get_currencies(
        networks=networks,
        is_native=is_native,
        is_stable=is_stable
    )

@router.post("/filter", response_model=List[Currency])
async def filter_currencies(filters: dict):
    """
    Filter currencies using JSON body parameters.
    
    Example body:
    ```json
    {
        "networks": ["ETH", "BSC"],
        "is_native": true,
        "is_stable": false
    }
    ```
    """
    currency_service = CurrencyService.get_instance()
    return currency_service.get_currencies(
        networks=filters.get("networks"),
        is_native=filters.get("is_native"),
        is_stable=filters.get("is_stable")
    )
