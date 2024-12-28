from fastapi import APIRouter, Query, Response
from typing import List, Optional
from services.currency import CurrencyService
from models.schemas.currency import Currency
from models.schemas.pagination import PaginatedResponse
from math import ceil

router = APIRouter(prefix="/currencies", tags=["currencies"])

@router.get("/all", response_model=List[Currency])
async def get_all_currencies(response: Response):
    """Get all available currencies."""
    currency_service = CurrencyService.get_instance()
    currencies = currency_service.get_currencies()
    
    # Convert response to JSON and compress
    return currencies

@router.get("", response_model=PaginatedResponse[Currency])
async def get_filtered_currencies(
    response: Response,
    q: Optional[str] = Query(None, description="Search query for currency name or ticker"),
    networks: Optional[List[str]] = Query(None, description="Filter by network (e.g., ETH, BTC)"),
    is_native: Optional[bool] = Query(None, description="Filter by native token status"),
    is_stable: Optional[bool] = Query(None, description="Filter by stablecoin status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page")
):

    currency_service = CurrencyService.get_instance()
    
    # Get filtered currencies
    currencies = currency_service.get_currencies(
        networks=networks,
        is_native=is_native,
        is_stable=is_stable
    )
    
    # Apply search filter if query is provided
    if q:
        q = q.lower()
        currencies = [
            currency for currency in currencies
            if q in currency.name.lower() or q in currency.ticker.lower()
        ]
    
    # Calculate pagination
    total_items = len(currencies)
    total_pages = ceil(total_items / page_size)
    
    # Adjust page if it exceeds total pages
    if page > total_pages and total_pages > 0:
        page = total_pages
    
    # Calculate slice indices
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    
    # Get paginated results
    paginated_currencies = currencies[start_idx:end_idx]
    
    
    return {
        "items": paginated_currencies,
        "total": total_items,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages
    }

