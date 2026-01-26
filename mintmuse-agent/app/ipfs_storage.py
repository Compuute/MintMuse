# app/ipfs_storage.py
# --------------------
# Helper module to upload metadata JSON to NFT.Storage (IPFS)
# using their simple HTTPS upload endpoint.

import json
import logging
from typing import Any, Dict

import requests
from .config import get_env_var

logger = logging.getLogger(__name__)

# Load API key from environment
NFT_STORAGE_API_KEY = get_env_var("NFT_STORAGE_API_KEY")

# NFT.Storage upload endpoint
NFT_STORAGE_UPLOAD_URL = "https://api.nft.storage/upload"


def upload_json_to_nft_storage(metadata: Dict[str, Any]) -> str:
    """
    Upload JSON metadata to NFT.Storage, returns ipfs://CID URI.
    """
    if not NFT_STORAGE_API_KEY:
        raise RuntimeError("Missing NFT_STORAGE_API_KEY in environment")

    headers = {
        "Authorization": f"Bearer {NFT_STORAGE_API_KEY}",
    }

    files = {
        "file": ("metadata.json", json.dumps(metadata), "application/json"),
    }

    logger.info("📤 Uploading metadata to NFT.Storage...")

    resp = requests.post(
        NFT_STORAGE_UPLOAD_URL,
        headers=headers,
        files=files,
        timeout=30,
    )
    resp.raise_for_status()

    data = resp.json()

    if not data.get("ok"):
        raise RuntimeError(f"NFT.Storage error response: {data}")

    cid = data["value"]["cid"]
    ipfs_uri = f"ipfs://{cid}"

    logger.info(f"✅ Metadata stored on IPFS. CID = {cid}")
    return ipfs_uri
