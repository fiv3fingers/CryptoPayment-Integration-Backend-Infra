from typing import Optional, List, Dict
from models.schemas.blockchain import TokenBalance, Token
from models.networks import ChainId, ChainType, ChainClass, get_by_chain_id
from utils import evm, solana
from utils.logging import get_logger
import requests

logger = get_logger(__name__)

class BlockchainServiceError(Exception):
    """Custom exception for Blockchain service errors"""
    def __init__(self, message: str, chain: Optional[str] = None):
        self.message = message
        self.chain = chain
        super().__init__(self.message)

class BlockchainService:
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize Blockchain service (only runs once)"""
        if not BlockchainService._initialized:
            # Does this cache have an expiration time + clean up? Else we blow up the memory.
            self._token_cache: Dict[str, Dict[str, List[TokenBalance]]] = {}  # wallet -> chain -> tokens
            logger.debug("Blockchain service initialized")
            BlockchainService._initialized = True



    async def get_wallet_tokens(
        self,
        address: str,
        chain_id: ChainId,
        use_cache: bool = True
    ) -> List[TokenBalance]:
        """
        Get token balances for a wallet address on a specific chain
        
        Args:
            address: Wallet address
            chain: Chain to query
            use_cache: Whether to use cached results
        
        Returns:
            List of TokenBalance objects
        """
        try:
            chain = get_by_chain_id(chain_id)
            if chain is None:
                raise BlockchainServiceError(f"Chain not found: {chain_id}")

            # Check cache first if enabled
            if use_cache and address in self._token_cache:
                chain_cache = self._token_cache[address]
                if chain.id in chain_cache:
                    logger.debug(f"Using cached tokens for {address} on {chain.name}")
                    return chain_cache[chain.id]

            # Get tokens based on chain type
            #tokens: List[TokenBalance] = []
            tokens = []
            
            if chain.type == ChainType.EVM:
                _tokens = evm.get_token_balances(address, chain.shortName)
                # TODO: filter empty balances 
                # TODO: filter tokens with no value (spam tokens etc).

                # This is way to slow, we either need a service that allow searching in bulk, or parallelize this.
                for token in _tokens:
                    metadata = evm.get_token_metadata(token.contractAddress, chain.shortName)

                    if metadata:
                        tokens.append(TokenBalance(
                            token=Token(
                                address=token.contractAddress,
                                decimals=metadata.decimals,
                                chain_id=chain.id,
                                name=metadata.name,
                                symbol=metadata.symbol,
                                logo=metadata.logo,
                                description=None,
                                price_usd=None,
                                is_stablecoin=None
                            ),
                            balance=token.tokenBalance
                        ))

                
            elif chain.type == ChainType.SOL:
                _tokens = solana.get_token_balances(address)
                print(_tokens)
                for token in _tokens:
                    print(token)
                    metadata = solana.get_token_metadata(token.mint)
                    print(metadata)

                    # download json file at the metadata.uri and parse it
                    try:
                        metadata_json = requests.get(metadata.uri).json()
                    except:
                        metadata_json = {}

                    print(metadata_json)
                    

                    if metadata:
                        tokens.append(TokenBalance(
                            token=Token(
                                address=token.mint,
                                decimals=token.decimals,
                                chain_id=chain.id,
                                name=metadata.name,
                                symbol=metadata.symbol,
                                logo= metadata_json.get('logo', None),
                                description=metadata_json.get('description', None),
                                price_usd=None,
                                is_stablecoin=None
                            ),
                            balance=token.balance
                        ))

                
            else:
                raise BlockchainServiceError(
                    f"Unsupported chain type: {chain.type}",
                    chain=chain.id
                )

            # Add native token balance if available
            native_balance = await self._get_native_balance(address, chain)
            if native_balance is not None:
                native_token = Token(
                    address="NATIVE",  # Special case for native token
                    decimals=chain.nativeCurrency.decimals,
                    chain_id=chain.id,
                    name=chain.nativeCurrency.name,
                    symbol=chain.nativeCurrency.symbol,
                    logo=chain.logo,
                    description=None,
                    price_usd=None,
                    is_stablecoin=False
                )
                tokens.append(TokenBalance(
                    token=native_token,
                    balance=native_balance
                ))

            # Update cache
            if use_cache:
                if address not in self._token_cache:
                    self._token_cache[address] = {}
                self._token_cache[address][chain.id] = tokens

            return tokens

        except Exception as e:
            logger.error(f"Error getting tokens for {address} on {chain.name}: {str(e)}")
            raise BlockchainServiceError(
                f"Failed to get tokens: {str(e)}",
                chain=chain.id
            )

    async def _get_native_balance(
        self,
        address: str,
        chain: ChainClass
    ) -> Optional[int]:
        """Get native token balance for a wallet"""
        try:
            if chain.type == ChainType.EVM:
                return evm.get_native_balance(address, chain.shortName)
            elif chain.type == ChainType.SOL:
                return solana.get_native_balance(address)
            return None
        except Exception as e:
            logger.warning(f"Failed to get native balance for {address} on {chain.name}: {str(e)}")
            return None

    @classmethod
    def get_instance(cls):
        """Get singleton instance of Blockchain service"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls):
        """Reset singleton instance (for testing)"""
        cls._instance = None
        cls._initialized = False
        return cls._instance

   
