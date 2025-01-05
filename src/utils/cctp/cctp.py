from dataclasses import dataclass
from enum import Enum
import json
import time
from typing import Dict, Optional, Tuple
import requests
import logging

from web3 import Web3
from web3.contract.contract import Contract
from eth_account import Account
from eth_account.signers.local import LocalAccount
from eth_utils.address import to_checksum_address
from eth_utils.crypto import keccak

from abis import TOKEN_MESSENGER_ABI, USDC_ABI, MESSAGE_TRANSMITTER_ABI

import asyncio

ATTESTATION_BASE_URL = 'https://iris-api-sandbox.circle.com/attestations/'


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CCTPError(Exception):
    """Base exception for CCTP-related errors"""
    pass

class ChainConnectionError(CCTPError):
    """Raised when there's an issue connecting to a chain"""
    pass

class TransactionError(CCTPError):
    """Raised when a transaction fails"""
    pass

class AttestationError(CCTPError):
    """Raised when there's an issue getting the attestation"""
    pass

class Chain(Enum):
    ETH_SEPOLIA = "eth-sepolia"
    BASE_SEPOLIA = "base-sepolia"
    AVALANCHE_FUJI = "avalanche-fuji"
    OP_SEPOLIA = "op-sepolia"
    ARBITRUM_SEPOLIA = "arbitrum-sepolia"
    POLYGON_POS_AMOY = "polygon-pos-amoy"

@dataclass
class ChainConfig:
    rpc_url: str
    token_messenger_address: str
    message_transmitter_address: str
    usdc_address: str
    domain_identifier: int

class CCTPBridge:
    CHAIN_CONFIGS = {
        Chain.ETH_SEPOLIA: ChainConfig(
            rpc_url="https://eth-sepolia.public.blastapi.io",
            token_messenger_address="0x9f3B8679c73C2Fef8b59B4f3444d4e156fb70AA5",
            message_transmitter_address="0x7865fAfC2db2093669d92c0F33AeEF291086BEFD",
            usdc_address="0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238",
            domain_identifier=0
        ),
        Chain.AVALANCHE_FUJI: ChainConfig(
            rpc_url="https://ava-testnet.public.blastapi.io/ext/bc/C/rpc",
            token_messenger_address="0xeb08f243e5d3fcff26a9e38ae5520a669f4019d0",
            message_transmitter_address="0xa9fb1b3009dcb79e2fe346c16a604b8fa8ae0a79",
            usdc_address="0x5425890298aed601595a70ab815c96711a31bc65",
            domain_identifier=1
        ),
        Chain.OP_SEPOLIA: ChainConfig(
            rpc_url="https://sepolia.optimism.io",
            token_messenger_address="0x9f3B8679c73C2Fef8b59B4f3444d4e156fb70AA5",
            message_transmitter_address="0x7865fAfC2db2093669d92c0F33AeEF291086BEFD",
            usdc_address="0x5fd84259d66Cd46123540766Be93DFE6D43130D7",
            domain_identifier=2
        ),
        Chain.ARBITRUM_SEPOLIA: ChainConfig(
            rpc_url="https://arbitrum-sepolia-rpc.publicnode.com",
            token_messenger_address="0x9f3B8679c73C2Fef8b59B4f3444d4e156fb70AA5",
            message_transmitter_address="0xaCF1ceeF35caAc005e15888dDb8A3515C41B4872",
            usdc_address="0x75faf114eafb1BDbe2F0316DF893fd58CE46AA4d",
            domain_identifier=3
        ),
        Chain.BASE_SEPOLIA: ChainConfig(
            rpc_url="https://base-sepolia-rpc.publicnode.com",
            token_messenger_address="0x9f3B8679c73C2Fef8b59B4f3444d4e156fb70AA5",
            message_transmitter_address="0x7865fAfC2db2093669d92c0F33AeEF291086BEFD",
            usdc_address="0x036CbD53842c5426634e7929541eC2318f3dCF7e",
            domain_identifier=6
        ),
        Chain.POLYGON_POS_AMOY: ChainConfig(
            rpc_url="https://rpc-amoy.polygon.technology/",
            token_messenger_address="0x9f3B8679c73C2Fef8b59B4f3444d4e156fb70AA5",
            message_transmitter_address="0x7865fAfC2db2093669d92c0F33AeEF291086BEFD",
            usdc_address="0x41e94eb019c0762f9bfcf9fb1e58725bfb0e7582",
            domain_identifier=7
        ),
    }

    def __init__(self, max_retries: int = 3, retry_delay: int = 1):
        self.web3_connections: Dict[Chain, Web3] = {}
        self.contracts: Dict[Chain, Dict[str, Contract]] = {}
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        self._initialize_connections()

    def _initialize_connections(self) -> None:
        """Initialize Web3 connections and contracts for all chains"""
        for chain in Chain:
            try:
                config = self.CHAIN_CONFIGS[chain]
                w3 = Web3(Web3.HTTPProvider(config.rpc_url))
                
                if not w3.is_connected():
                    raise ChainConnectionError(f"Failed to connect to {chain.value}")
                
                self.web3_connections[chain] = w3
                self.contracts[chain] = {
                    'token_messenger': self._load_contract(w3, config.token_messenger_address, TOKEN_MESSENGER_ABI),
                    'usdc': self._load_contract(w3, config.usdc_address, USDC_ABI),
                    'message_transmitter': self._load_contract(w3, config.message_transmitter_address, MESSAGE_TRANSMITTER_ABI)
                }
            except Exception as e:
                logger.error(f"Failed to initialize {chain.value}: {str(e)}")
                raise ChainConnectionError(f"Failed to initialize {chain.value}") from e

    @staticmethod
    def _load_contract(w3: Web3, address: str, abi: str) -> Contract:
        return w3.eth.contract(address=to_checksum_address(address), abi=json.loads(abi))

    @staticmethod
    def _address_to_bytes32(addr: str) -> str:
        addr_int = int(addr[2:], 16)
        return '0x' + hex(addr_int)[2:].zfill(64)

    def get_balances(self, chain: Chain, address: str) -> Tuple[float, float]:
        """Get ETH and USDC balances"""
        w3 = self.web3_connections[chain]
        usdc_contract = self.contracts[chain]['usdc']
        
        try:
            eth_balance = w3.eth.get_balance(address) / 1e18
            usdc_balance = usdc_contract.functions.balanceOf(address).call() / 1e6
            return eth_balance, usdc_balance
        except Exception as e:
            logger.error(f"Failed to get balances on {chain.value}: {str(e)}")
            raise

    def get_usdc_allowence(self, chain: Chain, account: LocalAccount) -> int:
        """Get USDC allowance for the token messenger contract"""
        usdc_contract = self.contracts[chain]['usdc']
        config = self.CHAIN_CONFIGS[chain]

        try:
            return usdc_contract.functions.allowance(
                account.address,
                config.token_messenger_address
            ).call()
        except Exception as e:
            logger.error(f"Failed to get USDC allowance on {chain.value}: {str(e)}")
            raise

    def approve_usdc(self, chain: Chain, account: LocalAccount, amount: int) -> str:
        """Approve USDC spending and return transaction hash"""
        w3 = self.web3_connections[chain]
        usdc_contract = self.contracts[chain]['usdc']
        config = self.CHAIN_CONFIGS[chain]

        try:
            nonce = w3.eth.get_transaction_count(account.address)
            approve_tx = usdc_contract.functions.approve(
                config.token_messenger_address,
                amount
            ).build_transaction({
                'from': account.address,
                'nonce': nonce,
                'gas': usdc_contract.functions.approve(
                    config.token_messenger_address,
                    amount
                ).estimate_gas({'from': account.address})
            })

            signed_tx = w3.eth.account.sign_transaction(approve_tx, account.key)
            tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
            
            if receipt['status'] != 1:
                raise TransactionError('USDC approval failed')
                
            return tx_hash.hex()
        except Exception as e:
            logger.error(f"Failed to approve USDC on {chain.value}: {str(e)}")
            raise

    def initiate_transfer(
        self,
        source_chain: Chain,
        destination_chain: Chain,
        source_account: LocalAccount,
        destination_address: str,
        amount: int
    ) -> Tuple[bytes, bytes, str]:
        """Initiate transfer and return message bytes, hash, and transaction hash"""
        try:
            destination_address_bytes32 = self._address_to_bytes32(destination_address)
            w3 = self.web3_connections[source_chain]
            token_messenger = self.contracts[source_chain]['token_messenger']
            config = self.CHAIN_CONFIGS[source_chain]
            
            # Approve USDC spending if necessary
            if self.get_usdc_allowence(source_chain, source_account) < amount:
                self.approve_usdc(source_chain, source_account, amount)

            
            # Initiate transfer
            nonce = w3.eth.get_transaction_count(source_account.address)
            burn_tx = token_messenger.functions.depositForBurn(
                amount,
                self.CHAIN_CONFIGS[destination_chain].domain_identifier,
                destination_address_bytes32,
                config.usdc_address
            ).build_transaction({
                'from': source_account.address,
                'nonce': nonce,
                'gas': token_messenger.functions.depositForBurn(
                    amount,
                    self.CHAIN_CONFIGS[destination_chain].domain_identifier,
                    destination_address_bytes32,
                    config.usdc_address
                ).estimate_gas({'from': source_account.address})
            })

            signed_tx = w3.eth.account.sign_transaction(burn_tx, source_account.key)
            tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

            if receipt['status'] != 1:
                raise TransactionError('Transfer initiation failed')

            event_topic = keccak(text='MessageSent(bytes)')
            log = next(log for log in receipt['logs'] 
                      if log['topics'][0].hex() == event_topic.hex())
            message_bytes = w3.eth.codec.decode(['bytes'], log['data'])[0]
            message_hash = keccak(hexstr=message_bytes.hex())

            return message_bytes, message_hash, tx_hash.hex()
        except Exception as e:
            logger.error(f"Failed to initiate transfer: {str(e)}")
            raise

    def get_attestation(self, message_hash: bytes, max_attempts: int = 60) -> Optional[str]:
        """Get attestation with timeout"""
        attempts = 0
        while attempts < max_attempts:
            try:
                response = requests.get(
                    f'{ATTESTATION_BASE_URL}0x{message_hash.hex()}',
                    timeout=10
                )
                response.raise_for_status()
                attestation_response = response.json()
                
                if attestation_response.get('status') == 'complete':
                    return attestation_response['attestation']
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"Attestation request failed: {str(e)}")
            
            attempts += 1
            time.sleep(self.retry_delay)
        
        raise AttestationError("Failed to get attestation after maximum attempts")

    def complete_transfer(
        self,
        destination_chain: Chain,
        destination_account: LocalAccount,
        message_bytes: bytes,
        signature: str
    ) -> str:
        """Complete transfer and return transaction hash"""
        try:
            w3 = self.web3_connections[destination_chain]
            transmitter = self.contracts[destination_chain]['message_transmitter']

            nonce = w3.eth.get_transaction_count(destination_account.address)
            receive_tx = transmitter.functions.receiveMessage(
                message_bytes,
                signature
            ).build_transaction({
                'from': destination_account.address,
                'nonce': nonce,
                'gas': transmitter.functions.receiveMessage(
                    message_bytes,
                    signature
                ).estimate_gas({'from': destination_account.address})
            })
            
            signed_tx = w3.eth.account.sign_transaction(receive_tx, destination_account.key)
            tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

            if receipt['status'] != 1:
                raise TransactionError('Transfer completion failed')
                
            return tx_hash.hex()
        except Exception as e:
            logger.error(f"Failed to complete transfer: {str(e)}")
            raise

async def transfer_usdc(
    source_chain: Chain,
    destination_chain: Chain, 
    source_account: LocalAccount,
    destination_account: LocalAccount,
    amount_usdc: float
) -> Dict[str, str]:
    """
    Async function to perform complete USDC transfer between chains and accounts.
    Returns transaction hashes for tracking.
    """
    bridge = CCTPBridge()
    amount = int(amount_usdc * 1_000_000)
    
    try:
        # Verify sufficient balance
        _, usdc_balance = bridge.get_balances(source_chain, source_account.address)
        if usdc_balance < amount_usdc:
            raise ValueError(f"Insufficient USDC balance: {usdc_balance:.6f}")
        
        # Execute transfer
        message_bytes, message_hash, init_tx = bridge.initiate_transfer(
            source_chain=source_chain,
            destination_chain=destination_chain,
            source_account=source_account,
            destination_address=destination_account.address,
            amount=amount
        )
        
        signature = bridge.get_attestation(message_hash)
        
        complete_tx = bridge.complete_transfer(
            destination_chain=destination_chain,
            destination_account=destination_account,
            message_bytes=message_bytes,
            signature=signature
        )
        
        return {
            'initiation_tx': init_tx,
            'completion_tx': complete_tx,
            'message_hash': '0x' + message_hash.hex(),
            'source_chain': source_chain.value,
            'destination_chain': destination_chain.value,
            'amount': amount_usdc,
            'source_address': source_account.address,
            'destination_address': destination_account.address
        }
        
    except Exception as e:
        logger.error(f"Transfer failed: {str(e)}")
        raise

def get_transaction_status(chain: Chain, tx_hash: str) -> Dict[str, any]:
    try:
        bridge = CCTPBridge()
        w3 = bridge.web3_connections[chain]
        receipt = w3.eth.get_transaction_receipt(tx_hash)
        
        return {
            'status': 'success' if receipt['status'] == 1 else 'failed',
            'block_number': receipt['blockNumber'],
            'gas_used': receipt['gasUsed'],
            'transaction_hash': tx_hash,
            'chain': chain.value
        }
    except Exception as e:
        logger.error(f"Failed to get transaction status: {str(e)}")
        raise

def verify_attestation(message_hash: str) -> Dict[str, any]:
    """
    Verify the attestation status for a given message hash.
    Returns the attestation details.
    """
    try:
        response = requests.get(
            f'{ATTESTATION_BASE_URL}{message_hash}',
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Failed to verify attestation: {str(e)}")
        raise


