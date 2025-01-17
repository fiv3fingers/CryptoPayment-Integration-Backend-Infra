# routes/payorder.py
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.database.dependencies import get_db, get_current_organization
from src.models.schemas.payorder import (
    CreatePaymentRequest,
    PayOrderDepositCreate,
    PayOrderResponse,
    PayOrderSaleCreate,
    UpdatePayOrderRequest,
)
from src.models.database_models import Organization
from src.services.payorder import PayOrderService
from src.utils.signature import validate_signature

router = APIRouter(prefix="/pay-orders", tags=["pay-order"])


@router.post("/deposit", response_model=PayOrderResponse)
async def create_deposit_pay_order(
    req: PayOrderDepositCreate,
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    """ API Route for create a new pay-order of type DEPOSIT """
    pay_order_service = PayOrderService(db)

    return await pay_order_service.create_deposit(org.id, req)


@router.post("/sale", response_model=PayOrderResponse)
async def create_sale_pay_order(
    req: PayOrderSaleCreate,
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    """ API Route for create a new pay-order of type SALE """

    #  api_key + secret + timestamp -> signature hash
    
    # validate Authorization Header
    authHeader = req.headers.get("Authorization")

    # TODO: get secret from database
    if validate_signature(authHeader, "secret_key") is False:
        raise HTTPException(
                status_code=401,
                detail="UnAuthorized"
            )
    
    pay_order_service = PayOrderService(db)
    return await pay_order_service.create_sale(org.id, req)


@router.put("/sale", response_model=PayOrderResponse)
async def update_sale_pay_order(
    id: str,
    req: UpdatePayOrderRequest,
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    """ API Route for update a payorder """

    # validate Authorization Header
    authHeader = req.headers.get("Authorization")

    # TODO: get secret from database
    if validate_signature(authHeader, "secret_key") is False:
        raise HTTPException(
                status_code=401,
                detail="UnAuthorized"
            )

    pay_order_service = PayOrderService(db)
    return await pay_order_service.update_sale(id, req)


@router.put("/deposit", response_model=PayOrderResponse)
async def update_deposit_pay_order(
    id: str,
    req: UpdatePayOrderRequest,
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    """ API Route for update a payorder """
    pay_order_service = PayOrderService(db)
    return await pay_order_service.update_deposit(id, req)


@router.post("/pay", response_model=PayOrderResponse)
async def pay_sale_order(
    req: CreatePaymentRequest,
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    """ API Route for pay a payorder """

    pay_order_service = PayOrderService(db)
    pay_order = await pay_order_service.pay(
        payorder_id=req.id,
        in_token_address=req.token_address,
        in_chain_id=req.token_chain_id,
        refund_address=req.refund_address,
    )

    # TODO: return partial PayOrderResponse omitting destination values

    return pay_order

@router.get("/{order_id}", response_model=PayOrderResponse)
async def get_order(
    order_id: str,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization)
):
    """ API Route for get a payorder by id """
    pay_order_service = PayOrderService(db)
    pay_order = await pay_order_service.get(org.id, order_id)
    return pay_order


#  Admin Routes

@router.get("/", response_model=List[PayOrderResponse])
async def get_orders(
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization)
):
    """ API Route for get all payorders of an organization """

    # TODO: add pagination
    # TODO: only from dashboard server

    pay_order_service = PayOrderService(db)
    pay_orders = await pay_order_service.get_all(org.id)
    return pay_orders


