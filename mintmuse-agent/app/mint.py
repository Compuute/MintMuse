# mint.py – Handles blockchain NFT minting using Web3.py
# ------------------------------------------------------
# This version includes:
# - Proper logging and error handling
# - Input validation
# - Safer environment variable loading
# - Optional structured return for frontend or API use
# - NEW: Extract token_id from ERC-721 Transfer event (real tokenId)
# - NEW: Checksummed addresses to avoid Web3 address issues

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

# Detect network from RPC URL so we can build the correct Etherscan link
_IS_SEPOLIA = "sepolia" in RPC_URL.lower()
ETHERSCAN_BASE = "https://sepolia.etherscan.io/tx" if _IS_SEPOLIA else None
PRIVATE_KEY = get_env_var("PRIVATE_KEY") or exit("❌ Missing PRIVATE_KEY in .env")
ACCOUNT_ADDRESS = get_env_var("ACCOUNT_ADDRESS") or exit("❌ Missing ACCOUNT_ADDRESS in .env")
CONTRACT_ADDRESS = get_env_var("CONTRACT_ADDRESS") or exit("❌ Missing CONTRACT_ADDRESS in .env")
ABI_PATH = get_env_var("ABI_PATH", default="solidity/contract_abi.json")

# -----------------------------------------------------------------------------
# Establish blockchain connection
# -----------------------------------------------------------------------------
load_dotenv()  # Ensure .env is loaded when running locally

# Optional debug prints (safe to remove in production)
print("🔍 RPC_URL:", RPC_URL)

try:
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    if not w3.is_connected():
        raise ConnectionError("❌ Unable to connect to blockchain provider.")
    logger.info("✅ Connected to blockchain provider.")
except Exception as e:
    logger.error(f"Failed to connect to RPC provider: {e}")
    raise

# -----------------------------------------------------------------------------
# Normalize / checksum addresses (avoid common Web3.py address issues)
# -----------------------------------------------------------------------------
try:
    ACCOUNT_ADDRESS = w3.to_checksum_address(ACCOUNT_ADDRESS)
    CONTRACT_ADDRESS = w3.to_checksum_address(CONTRACT_ADDRESS)
except Exception as e:
    logger.error(f"❌ Failed to checksum addresses: {e}")
    raise

# -----------------------------------------------------------------------------
# Load contract ABI (defines smart contract's structure)
# -----------------------------------------------------------------------------
try:
    with open(ABI_PATH) as abi_file:
        raw_json = json.load(abi_file)

        # --- support both Hardhat artifact and raw ABI list ---
        # Case 1: Hardhat-style artifact: {"abi": [...], ...}
        if isinstance(raw_json, dict) and "abi" in raw_json:
            contract_abi = raw_json["abi"]
            logger.info("✅ Loaded ABI from Hardhat artifact JSON.")
        # Case 2: Already a pure ABI list
        else:
            contract_abi = raw_json
            logger.info("✅ Loaded ABI from raw ABI JSON.")

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
# Helper function: Extract tokenId from ERC-721 Transfer event
# -----------------------------------------------------------------------------
def _extract_token_id_from_receipt(receipt) -> int | None:
    """
    Attempts to parse ERC-721 Transfer events from the tx receipt
    and returns the minted tokenId.
    """
    try:
        # Transfer(from, to, tokenId)
        events = contract.events.Transfer().process_receipt(receipt)
        if not events:
            return None
        # Take the last Transfer event (usually the mint event)
        token_id = int(events[-1]["args"]["tokenId"])
        return token_id
    except Exception:
        # If event decoding fails (ABI mismatch / no event), return None safely
        return None


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
        dict: Transaction details (hash + token_id if found + optional explorer link)
    """
    try:
        validate_address(recipient_address)

        # Normalize recipient to checksum to prevent downstream issues
        recipient_address = w3.to_checksum_address(recipient_address)

        # Get the transaction count (nonce) for this account
        nonce = w3.eth.get_transaction_count(ACCOUNT_ADDRESS)

        # Build the transaction for minting
        # Use dynamic gas price so it works on both local Hardhat and Sepolia
        tx = contract.functions.mintNFT(recipient_address, token_uri).build_transaction({
            "from": ACCOUNT_ADDRESS,
            "nonce": nonce,
            "gas": 500_000,       # a bit higher to avoid out-of-gas surprises
            "gasPrice": w3.eth.gas_price,  # auto: ~1 gwei local, current rate on Sepolia
        })

        # Sign transaction using the private key
        signed_tx = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)

        # Broadcast the transaction to the network
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        tx_hex = w3.to_hex(tx_hash)

        logger.info(f"✅ Mint tx submitted. TxHash: {tx_hex}")

        # Wait for receipt so we can extract tokenId
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)

        token_id = _extract_token_id_from_receipt(receipt)

        if token_id is not None:
            logger.info(f"🎯 Mint confirmed. token_id={token_id}")
        else:
            logger.warning("⚠️ Mint confirmed but could not extract token_id from Transfer event.")

        # Build Etherscan link — only valid on Sepolia, None on local Hardhat
        etherscan_url = f"{ETHERSCAN_BASE}/{tx_hex}" if ETHERSCAN_BASE else None

        # Return structured response for API or frontend
        return {
            "status": "success",
            "recipient": recipient_address,
            "tx_hash": tx_hex,
            "token_id": token_id,
            "etherscan_url": etherscan_url,  # clickable link (None on local)
        }

    except InvalidAddress as e:
        logger.error(f"❌ Address validation failed: {e}")
        return {"status": "error", "error": str(e)}

    except Exception as e:
        logger.error(f"❌ Minting failed: {e}")
        return {"status": "error", "error": str(e)}
