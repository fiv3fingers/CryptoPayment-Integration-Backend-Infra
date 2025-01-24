# routes/quote.py

"""
    Gives a quote for a wallet, amount and output token
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.database.dependencies import get_db, get_current_organization

from src.models.database_models import Organization

from src.services.organization import OrganizationService
from src.services.quote import QuoteService
from src.services.changenow import ChangeNowService
from src.utils.blockchain.blockchain import get_wallet_currencies
from src.models.schemas.quote import (
    QuoteResponse, QuoteRequest,
)
from src.utils.types import ChainId


from datetime import datetime

router = APIRouter(prefix="/quotes", tags=["Quotes"])

@router.post("/usd", response_model=QuoteResponse)
async def get_quote_usd(
    chain_id: ChainId,
    user_address: str,
    value_usd: float,
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    """Get a quote for a specific order"""
    org_service = OrganizationService(db)
    # cn_service = ChangeNowService()

    settlement_currency_ids = [sc.currency_id for sc in await org_service.get_settlement_currencies(org.id)]

    all_user_currencies = get_wallet_currencies(user_address, chain_id)
    print(f"all_user_currencies: len={len(all_user_currencies)}")
    # user_currencies = [c for c in all_user_currencies if await cn_service.is_supported(c)]
    # print(f"user_currencies (cn_supported): len={len(user_currencies)}")


    quote_service = QuoteService()
    quotes = await quote_service._get_quote_value_usd(
        from_currencies=all_user_currencies,
        to_currencies=settlement_currency_ids,
        value_usd=value_usd
    )

    return QuoteResponse(
        timestamp=datetime.now(),
        quotes=quotes
    )

@router.post("/currency", response_model=QuoteResponse)
async def get_quote_currency(
        chain_id: ChainId,
        user_address: str,
        out_currency_id: str,
        amount_out: float,
        _: Organization = Depends(get_current_organization),
        # db: Session = Depends(get_db)
):
    """Get a quote for a specific order"""


    all_user_currencies = get_wallet_currencies(user_address, chain_id)
    print(f"all_user_currencies: len={len(all_user_currencies)}")

    quote_service = QuoteService()

    quotes = await quote_service._get_quote_currency_out(
        from_currencies=all_user_currencies,
        to_currency=out_currency_id,
        amount_out=amount_out
    )

    return QuoteResponse(
        timestamp=datetime.now(),
        quotes=quotes
    )

