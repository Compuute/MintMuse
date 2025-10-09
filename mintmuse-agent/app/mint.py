# mint.py – Handles blockchain NFT minting using Web3.py
# ------------------------------------------------------
# This version includes:
# - Proper logging and error handling
# - Input validation
# - Safer environment variable loading
# - Optional structured return for frontend or API use

import json
import logging
import os
from dotenv import load_dotenv
from web3 import Web3
from web3.exceptions import InvalidAddress
from .config import get_env_var  # Custom utility to load env variables securely

# -----------------------------------------------------------------------------
# Logging configuration
# -----------------------------------------------------------------------------
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

# -----------------------------------------------------------------------------
# Load environment variables securely
# -----------------------------------------------------------------------------
RPC_URL = get_env_var("RPC_URL") or exit("❌ Missing RPC_URL in .env")
PRIVATE_KEY = get_env_var("PRIVATE_KEY") or exit("❌ Missing PRIVATE_KEY in .env")
ACCOUNT_ADDRESS = get_env_var("ACCOUNT_ADDRESS") or exit("❌ Missing ACCOUNT_ADDRESS in .env")
CONTRACT_ADDRESS = get_env_var("CONTRACT_ADDRESS") or exit("❌ Missing CONTRACT_ADDRESS in .env")
ABI_PATH = get_env_var("ABI_PATH", default="solidity/contract_abi.json")

# -----------------------------------------------------------------------------
# Establish blockchain connection
# -----------------------------------------------------------------------------

print("🔍 BLOCKCHAIN_RPC_URL:", os.getenv("BLOCKCHAIN_RPC_URL")) # Debug print (remove in production)
try:
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    if not w3.is_connected():
        raise ConnectionError("❌ Unable to connect to blockchain provider.")
    logger.info("✅ Connected to blockchain provider.")
except Exception as e:
    logger.error(f"Failed to connect to RPC provider: {e}")
    raise

# -----------------------------------------------------------------------------
# Load contract ABI (defines smart contract's structure)
# -----------------------------------------------------------------------------
try:
    with open(ABI_PATH) as abi_file:
        contract_abi = json.load(abi_file)
    contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=contract_abi)
    logger.info("✅ Contract loaded successfully.")
except Exception as e:
    logger.error(f"❌ Failed to load contract ABI: {e}")
    raise


# -----------------------------------------------------------------------------
# Helper function: Validate Ethereum address format
# -----------------------------------------------------------------------------
def validate_address(address: str):
    """Ensures the Ethereum address is valid before using it."""
    if not w3.is_address(address):
        raise InvalidAddress(f"Invalid Ethereum address: {address}")


# -----------------------------------------------------------------------------
# Core function: Mint an NFT on-chain
# -----------------------------------------------------------------------------
def mint_nft(recipient_address: str, token_uri: str) -> dict:
    """
    Mints a new NFT to the specified recipient address.

    Args:
        recipient_address (str): Ethereum wallet that will receive the NFT.
        token_uri (str): URL or IPFS URI of the NFT metadata JSON.

    Returns:
        dict: Transaction details (hash + optional explorer link)
    """
    try:
        validate_address(recipient_address)

        # Get the transaction count (nonce) for this account
        nonce = w3.eth.get_transaction_count(ACCOUNT_ADDRESS)

        # Build the transaction for minting
        tx = contract.functions.mintNFT(recipient_address, token_uri).build_transaction({
            'from': ACCOUNT_ADDRESS,
            'nonce': nonce,
            'gas': 300_000,
            'gasPrice': w3.to_wei('10', 'gwei'),
        })

        # Sign transaction using the private key
        signed_tx = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)

        # Broadcast the transaction to the network
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        tx_hex = w3.to_hex(tx_hash)

        logger.info(f"✅ NFT minted successfully! TxHash: {tx_hex}")

        # Return structured response for API or frontend
        return {
            "status": "success",
            "recipient": recipient_address,
            "tx_hash": tx_hex,
            "etherscan_link": f"https://etherscan.io/tx/{tx_hex}"
        }

    except InvalidAddress as e:
        logger.error(f"❌ Address validation failed: {e}")
        return {"status": "error", "error": str(e)}

    except Exception as e:
        logger.error(f"❌ Minting failed: {e}")
        return {"status": "error", "error": str(e)}
