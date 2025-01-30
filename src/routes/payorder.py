from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.database.dependencies import (
    get_db,
    get_current_organization,
    validate_authorization_header,
    authorization_header,
    api_key_header,
)
from src.models.enums import PayOrderMode, PayOrderStatus
from src.models.schemas.payorder import (
    CreatePayOrderRequest,
    PayOrderResponse,
    CreateQuoteRequest,
    PaymentDetailsRequest,
    PaymentDetailsResponse,
    SingleCurrencyQuote,
)
from src.models.database_models import Organization
from src.services.payorder import PayOrderService

router = APIRouter(prefix="/pay-orders", tags=["Pay Orders"])


@router.post("/", response_model=PayOrderResponse)
async def create_payorder(
    req: CreatePayOrderRequest,
    db: Session = Depends(get_db),
    api_key=Depends(api_key_header),
    auth_header=Depends(authorization_header),
):
    if req.mode == PayOrderMode.DEPOSIT:
        org = get_current_organization(api_key, db) # raise 401 if invalid api key
    if req.mode == PayOrderMode.SALE:
        org = validate_authorization_header(auth_header, db) # raise 401 if invalid signature

    try:
        payorder_service = PayOrderService(db)
        return await payorder_service.create_payorder(org.id, req)

    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.post("/{payorder_id}/quote", response_model=List[SingleCurrencyQuote])
async def quote_payorder(
    payorder_id: str,
    req: CreateQuoteRequest,
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """API Route for creating the final quote including deposit details to submit the transaction"""

    try:
        payorder_service = PayOrderService(db)
        return await payorder_service.quote(payorder_id, req, org)

    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)




@router.post("/{payorder_id}/payment-details", response_model=PaymentDetailsResponse)
async def create_payment_details(
    payorder_id: str,
    req: PaymentDetailsRequest,
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    """API Route for creating the final quote including deposit details to submit the transaction"""

    try:
        payorder_service = PayOrderService(db)
        payorder = await payorder_service.get(payorder_id)
        if payorder is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

        # Check if payorder status is pending
        if payorder.status != PayOrderStatus.PENDING:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Deposit status is not pending, cannot update")
        
        return await payorder_service.payment_details(payorder, req, org)
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code)
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)



@router.get("/{payorder_id}/process", response_model=None)
async def process_payorder(
    payorder_id: str,
    tx_hash: str,
    db: Session = Depends(get_db),
    _: Organization = Depends(get_current_organization),
):
    """API Route for processing a payorder"""

    try:
        payorder_service = PayOrderService(db)
        payorder = await payorder_service.get(payorder_id)
        if payorder is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PayOrder not found")

        # Validation
        if payorder.status != PayOrderStatus.AWAITING_PAYMENT:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="PayOrder status is not AWAITING_PAYMENT"
            )

        payorder = await payorder_service.process_payment_txhash(payorder, tx_hash)
        await payorder_service.update(payorder)

        if payorder.status == PayOrderStatus.AWAITING_CONFIRMATION:
            # TODO: build in retry mechanism
            pass
    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)




@router.get("/{payorder_id}", response_model=PayOrderResponse)
async def get_payorder(
    payorder_id: str,
    db: Session = Depends(get_db),
    _: Organization = Depends(get_current_organization),
):
    """API Route for get a payorder by id"""

    try:
        payorder_service = PayOrderService(db)
        payorder = await payorder_service.get(payorder_id)
        if payorder is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
        return payorder
    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)



@router.get("/", response_model=List[PayOrderResponse])
async def get_orders(
    db: Session = Depends(get_db), org: Organization = Depends(get_current_organization)
):
    """API Route for get all payorders of an organization"""

    # TODO: add pagination
    # TODO: only from dashboard server

    try:
        payorder_service = PayOrderService(db)
        payorders = await payorder_service.get_all(org.id)
        return payorders
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
