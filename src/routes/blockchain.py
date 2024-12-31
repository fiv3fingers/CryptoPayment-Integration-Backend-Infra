from fastapi import APIRouter, HTTPException
from typing import List
from services.blockchain import BlockchainService, BlockchainServiceError

from models.schemas.blockchain import TokenBalance
from models.networks import ChainId, get_by_chain_id


router = APIRouter(prefix="/blockchain", tags=["blockchain"])

# User cannot guess the chain_name, especially since it's capitalized and not formatted to lower/upper case. We better use something else.
# Ideally we can get tokens by ChainType (EVM, SOL, etc)
@router.get("/{chain_id}/{address}/tokens")
async def get_wallet_tokens_by_chain(chain_id: ChainId, address: str) -> List[TokenBalance]:
    """
    Fetch tokens for a wallet address on a specific blockchain chain.
    """
    
    # you're already calling this function in the get_wallet_tokens
     
    # chain = get_by_chain_id(chain_id)
    # if chain is None:
    #     raise HTTPException(status_code=400, detail="Chain not found")

    blockchain_service = BlockchainService.get_instance()

    try:
        tokens = await blockchain_service.get_wallet_tokens(address, chain_id)
        return tokens
    except BlockchainServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

