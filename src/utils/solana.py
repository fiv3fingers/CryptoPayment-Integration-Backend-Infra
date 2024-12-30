import base64
import os
from dataclasses import dataclass
from typing import List, Optional
import requests
from solders.pubkey import Pubkey
import struct

from .logging import get_logger
import base58



logger = get_logger(__name__)

SOLANA_RPC_URL = os.getenv("SOLANA_RPC_URL")
if SOLANA_RPC_URL is None:
    raise ValueError("SOLANA_RPC_URL is not set")

@dataclass
class TokenAccount:
    pubkey: str
    mint: str
    balance: int
    balance_ui: str
    decimals: int

@dataclass
class Metadata:
    mint: str
    name: str
    symbol: str
    uri: str

def get_token_balances(pubkey: str) -> List[TokenAccount]:
    filters = [
        {
            "dataSize": 165  # Size of token account (bytes)
        },
        {
            "memcmp": {
                "offset": 32,  # Location of owner field
                "bytes": pubkey  # Wallet to search for
            }
        }
    ]
    
    # Construct the RPC request
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getProgramAccounts",
        "params": [
            "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA",  # TOKEN_PROGRAM_ID
            {
                "encoding": "jsonParsed",
                "filters": filters
            }
        ]
    }
    
    headers = {
        "Content-Type": "application/json",
    }
    
    try:
        response = requests.post(SOLANA_RPC_URL, json=payload, headers=headers)
        response.raise_for_status()
        
        result = response.json().get("result", [])
        
        token_accounts = []
        for account in result:
            try:
                account_data = account["account"]["data"]["parsed"]["info"]
                token_accounts.append(
                    TokenAccount(
                        pubkey=account["pubkey"],
                        mint=account_data["mint"],
                        balance=int(account_data["tokenAmount"]["amount"]),
                        balance_ui=account_data["tokenAmount"]["uiAmount"],
                        decimals=account_data["tokenAmount"]["decimals"]
                    )
                )
            except (KeyError, TypeError) as e:
                logger.warning(f"Failed to parse account data: {str(e)}")
                continue
                
        return token_accounts

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to get token accounts for {pubkey}: {str(e)}")
        return []


def get_metadata_account(mint_address: str) -> Pubkey:
    """Find the metadata account for a given mint address"""
    metadata_program_id = Pubkey.from_string('metaqbxxUerdq28cj1RbAWkYQm3ybzjb6a8bt518x1s')
    mint_pubkey = Pubkey.from_string(mint_address)
    
    # Find PDA for metadata
    seeds = [
        bytes("metadata", 'utf-8'),
        bytes(metadata_program_id),
        bytes(mint_pubkey)
    ]
    metadata_address, _ = Pubkey.find_program_address(
        seeds,
        metadata_program_id
    )
    return metadata_address


def unpack_metadata_account(data):
    # COPY PASTA FROM https://github.com/metaplex-foundation/python-api/blob/441c2ba9be76962d234d7700405358c72ee1b35b/metaplex/metadata.py#L180
    assert(data[0] == 4)
    i = 1
    source_account = base58.b58encode(bytes(struct.unpack('<' + "B"*32, data[i:i+32])))
    i += 32
    mint_account = base58.b58encode(bytes(struct.unpack('<' + "B"*32, data[i:i+32])))
    i += 32
    name_len = struct.unpack('<I', data[i:i+4])[0]
    i += 4
    name = struct.unpack('<' + "B"*name_len, data[i:i+name_len])
    i += name_len
    symbol_len = struct.unpack('<I', data[i:i+4])[0]
    i += 4 
    symbol = struct.unpack('<' + "B"*symbol_len, data[i:i+symbol_len])
    i += symbol_len
    uri_len = struct.unpack('<I', data[i:i+4])[0]
    i += 4 
    uri = struct.unpack('<' + "B"*uri_len, data[i:i+uri_len])
    i += uri_len
    fee = struct.unpack('<h', data[i:i+2])[0]
    i += 2
    has_creator = data[i] 
    i += 1
    creators = []
    verified = []
    share = []
    if has_creator:
        creator_len = struct.unpack('<I', data[i:i+4])[0]
        i += 4
        for _ in range(creator_len):
            creator = base58.b58encode(bytes(struct.unpack('<' + "B"*32, data[i:i+32])))
            creators.append(creator)
            i += 32
            verified.append(data[i])
            i += 1
            share.append(data[i])
            i += 1
    primary_sale_happened = bool(data[i])
    i += 1
    is_mutable = bool(data[i])
    metadata = {
        "update_authority": source_account,
        "mint": mint_account,
        "data": {
            "name": bytes(name).decode("utf-8").strip("\x00"),
            "symbol": bytes(symbol).decode("utf-8").strip("\x00"),
            "uri": bytes(uri).decode("utf-8").strip("\x00"),
            "seller_fee_basis_points": fee,
            "creators": creators,
            "verified": verified,
            "share": share,
        },
        "primary_sale_happened": primary_sale_happened,
        "is_mutable": is_mutable,
    }
    return metadata


def get_token_metadata(mint_address: str) -> Metadata:
    metadata_address = get_metadata_account(mint_address)

    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getAccountInfo",
        "params": [
            f"{metadata_address}",
            { "encoding": "base64" }
        ],
    }
    
    headers = {
        "Content-Type": "application/json",
    }
    
    response = requests.post(SOLANA_RPC_URL, json=payload, headers=headers)
    response.raise_for_status()

    
    result = response.json().get("result", {})
    data = result.get("value", {}).get("data", "")
    
    if data:
        metadata = unpack_metadata_account(base64.b64decode(data[0]))
        return Metadata(
            mint=metadata["mint"],
            name=metadata["data"]["name"],
            symbol=metadata["data"]["symbol"],
            uri=metadata["data"]["uri"]
        )
    else:
        logger.warning(f"Failed to fetch metadata for mint {mint_address}")
        return None

def get_native_balance(pubkey: str) -> int:
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getBalance",
        "params": [pubkey]
    }
    
    headers = {
        "Content-Type": "application/json",
    }
    
    try:
        response = requests.post(SOLANA_RPC_URL, json=payload, headers=headers)
        response.raise_for_status()
        
        return response.json().get("result", 0).get("value", 0)
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to get balance for {pubkey}: {str(e)}")
        return 0

