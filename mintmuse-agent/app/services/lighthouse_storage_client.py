# app/services/lighthouse_storage_client.py
# -----------------------------------------
# Uploads NFT metadata JSON to Lighthouse (IPFS) and returns an ipfs:// URI.
# Fallback: saves metadata locally and returns an HTTP URL served by FastAPI.

import json
import logging
import os
import tempfile
import uuid
from typing import Any, Dict, Optional

import requests

from app.config import get_env_var  # reuse your existing config helper

logger = logging.getLogger(__name__)

# Load API key from environment (optional if you want local fallback)
LIGHTHOUSE_API_KEY = get_env_var("LIGHTHOUSE_API_KEY")

# Used for local fallback tokenURI. Set PUBLIC_BASE_URL in .env for non-local usage.
PUBLIC_BASE_URL = get_env_var("PUBLIC_BASE_URL", default="http://127.0.0.1:8000")

# Where we store fallback metadata files
LOCAL_METADATA_DIR = "app/storage/metadata"


class LighthouseStorageError(Exception):
    """Custom exception for Lighthouse related errors."""
    pass


def _save_metadata_locally(metadata: Dict[str, Any]) -> str:
    """Save metadata to local disk and return the generated file id (without extension)."""
    os.makedirs(LOCAL_METADATA_DIR, exist_ok=True)

    file_id = str(uuid.uuid4())
    file_path = os.path.join(LOCAL_METADATA_DIR, f"{file_id}.json")

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    logger.info(f"💾 Saved metadata locally: {file_path}")
    return file_id


def _local_token_uri(file_id: str) -> str:
    """Build an HTTP tokenURI for the locally saved metadata file."""
    base = (PUBLIC_BASE_URL or "http://127.0.0.1:8000").rstrip("/")
    return f"{base}/metadata/{file_id}.json"


# -----------------------------------------------------------------------------
# NEW: Upload a binary asset (e.g., PNG) to Lighthouse and return ipfs://<cid>
# -----------------------------------------------------------------------------
def upload_file_to_lighthouse(file_path: str) -> str:
    """
    Upload a binary file (e.g. PNG) to Lighthouse and return ipfs://<cid>.
    Raises LighthouseStorageError on failure (caller can decide fallback behavior).
    """
    url = "https://node.lighthouse.storage/api/v0/add"

    if not LIGHTHOUSE_API_KEY:
        raise LighthouseStorageError("LIGHTHOUSE_API_KEY missing.")

    if not os.path.exists(file_path):
        raise LighthouseStorageError(f"File not found: {file_path}")

    headers = {"Authorization": f"Bearer {LIGHTHOUSE_API_KEY}"}

    try:
        with open(file_path, "rb") as f:
            files = {"file": f}
            response = requests.post(url, headers=headers, files=files, timeout=(5,60))
            response.raise_for_status()

        try:
            body = response.json()
        except ValueError as e:
            logger.error(f"❌ Could not decode Lighthouse response as JSON: {e}")
            raise LighthouseStorageError("Could not decode Lighthouse response as JSON.") from e

        cid = body.get("Hash") or (body.get("data") or {}).get("Hash")
        if not cid:
            logger.error(f"❌ Lighthouse response missing CID/Hash: {body}")
            raise LighthouseStorageError(f"Lighthouse response missing CID/Hash: {body}")

        ipfs_uri = f"ipfs://{cid}"
        logger.info(f"✅ File uploaded to Lighthouse. CID={cid}")
        return ipfs_uri

    except requests.RequestException as e:
        raise LighthouseStorageError(f"Upload failed: {e}") from e


def upload_metadata_to_lighthouse(metadata: Dict[str, Any]) -> str:
    """
    Uploads NFT metadata JSON to Lighthouse and returns an ipfs://<cid> URI.
    If Lighthouse fails (timeout, network, etc), falls back to local storage and returns
    an HTTP URL that points to FastAPI static route (/metadata/<id>.json).

    Returns:
        str: tokenURI (ipfs://CID OR http(s)://.../metadata/<id>.json)
    """

    # Lighthouse upload endpoint (JSON file upload as multipart/form-data)
    url = "https://node.lighthouse.storage/api/v0/add"

    # If no API key is set, go directly to local fallback (no hard failure)
    if not LIGHTHOUSE_API_KEY:
        logger.warning("⚠️ LIGHTHOUSE_API_KEY missing. Using local fallback tokenURI.")
        file_id = _save_metadata_locally(metadata)
        return _local_token_uri(file_id)

    headers = {"Authorization": f"Bearer {LIGHTHOUSE_API_KEY}"}

    response: Optional[requests.Response] = None

    # Lighthouse expects a file upload. We'll write metadata to a temp JSON file.
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp:
            json.dump(metadata, tmp, ensure_ascii=False)
            tmp_path = tmp.name

        with open(tmp_path, "rb") as f:
            files = {"file": f}
            response = requests.post(url, headers=headers, files=files, timeout=60)
            response.raise_for_status()

        # Parse response JSON
        try:
            body = response.json()
        except ValueError as e:
            logger.error(f"❌ Could not decode Lighthouse response as JSON: {e}")
            raise LighthouseStorageError("Could not decode Lighthouse response as JSON.") from e

        # Lighthouse commonly returns a Hash field (CID). Some responses use data.Hash.
        cid = body.get("Hash") or (body.get("data") or {}).get("Hash")
        if not cid:
            logger.error(f"❌ Lighthouse response missing CID/Hash: {body}")
            raise LighthouseStorageError(f"Lighthouse response missing CID/Hash: {body}")

        ipfs_uri = f"ipfs://{cid}"
        logger.info(f"✅ Metadata uploaded to Lighthouse. CID={cid}")
        logger.info(f"🔗 tokenURI = {ipfs_uri}")
        return ipfs_uri

    except (requests.RequestException, LighthouseStorageError) as e:
        # Fallback to local storage instead of failing mint flow
        logger.error(f"❌ Lighthouse upload failed, using local fallback. Reason: {e}")
        file_id = _save_metadata_locally(metadata)
        fallback_uri = _local_token_uri(file_id)
        logger.info(f"🔁 Fallback tokenURI = {fallback_uri}")
        return fallback_uri

    finally:
        # Clean up temp file
        try:
            if "tmp_path" in locals() and os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception:
            pass
