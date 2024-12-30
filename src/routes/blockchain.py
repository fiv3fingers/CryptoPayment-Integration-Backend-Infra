from fastapi import APIRouter, HTTPException
from typing import List, Optional
from services.blockchain import BlockchainService, BlockchainServiceError

from models.schemas.blockchain import TokenBalance, Token
from models.networks import Chain


router = APIRouter(prefix="/blockchain", tags=["blockchain"])


@router.get("/{chain_name}/{address}/tokens")
async def get_wallet_tokens(chain_name: str, address: str):

    chain = Chain.get_by_name(chain_name)
    if chain is None:
        raise HTTPException(status_code=400, detail="Chain not found")

    blockchain_service = BlockchainService.get_instance()

    try:
        tokens = await blockchain_service.get_wallet_tokens(address, chain.id)
        return tokens
    except BlockchainServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

