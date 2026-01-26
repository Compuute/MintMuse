# app/routes/mint_route.py

import os
import uuid
from typing import Any, Dict, Optional
from PIL import Image, ImageDraw, ImageFont

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..mint import mint_nft
from app.services.lighthouse_storage_client import (
    upload_metadata_to_lighthouse,
    LighthouseStorageError,
)
from app.config import get_env_var

# Optional: Import logic from agent (can be activated later)
# from agents.root_agent import run_agent_chain
# IMPORTANT:
# Do NOT set prefix="/api" here because main.py already adds prefix="/api"
router = APIRouter()

DEFAULT_RECIPIENT = get_env_var("ACCOUNT_ADDRESS")
if not DEFAULT_RECIPIENT:
    raise ValueError("ACCOUNT_ADDRESS environment variable is not set")

# -----------------------------------------------------------------------------
# 1) Simple AI generation stub  ->  POST /api/generate
# -----------------------------------------------------------------------------

class GenerateRequest(BaseModel):
    """Request body for generating an AI asset + metadata."""
    prompt: str


class GenerateResponse(BaseModel):
    """Response body for the AI generation stub."""
    preview_url: str
    metadata: Dict[str, Any]


@router.post("/generate", response_model=GenerateResponse)
async def generate_asset(request: GenerateRequest):
    """
    Endpoint: POST /api/generate
    Purpose: Temporary stub that returns a fake preview URL + metadata.
             This is only used to verify frontend <-> backend integration.

    Later:
      - Replace this with a real AI call (e.g. Gemini / OpenAI).
      - Upload the generated asset + metadata to IPFS/Arweave.
    """
    try:
        # ---------------------------------------------------------------------
        # NEW: Create a LOCAL preview image (fastest path).
        # Served via main.py static mount: /previews -> app/storage/previews
        # ---------------------------------------------------------------------
        os.makedirs("app/storage/previews", exist_ok=True)

        filename = f"{uuid.uuid4()}.png"
        rel_path = f"app/storage/previews/{filename}"

        # Create a simple preview image with the prompt text (stub preview)
        img = Image.new("RGB", (800, 500), color=(20, 20, 30))
        draw = ImageDraw.Draw(img)

        # Keep the text short so it fits nicely in the preview
        prompt_text = (request.prompt or "").strip()
        if len(prompt_text) > 80:
            prompt_text = prompt_text[:77] + "..."

        text = f"MintMuse\nLocal Preview\n\n{prompt_text}"
        draw.multiline_text(
            (400, 250),
            text,
            fill=(200, 200, 255),
            anchor="mm",
            align="center",
        )

        img.save(rel_path)

        # IMPORTANT: Use 127.0.0.1 to match how you test locally via curl/browser
        preview_url = f"http://127.0.0.1:8000/previews/{filename}"

        return GenerateResponse(
            preview_url=preview_url,
            metadata={
                "name": "Test MintMuse NFT",
                "description": f"AI-generated asset based on prompt: {request.prompt}",
                # NEW: Include standard NFT metadata field "image"
                # (Your UI can prefer metadata.image if it wants.)
                "image": preview_url,
                "attributes": [
                    {"trait_type": "generator", "value": "MintMuse stub"},
                    {"trait_type": "env", "value": "local-dev"},
                ],
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")



# -----------------------------------------------------------------------------
# 2) REAL Mint endpoint used by the React UI  ->  POST /api/mint
# -----------------------------------------------------------------------------

class UIMintRequest(BaseModel):
    """Request body used by the React frontend for /api/mint."""
    prompt: str
    metadata: Dict[str, Any]


class UIMintResponse(BaseModel):
    """Response body returned to the React frontend after REAL mint."""
    status: str
    tx_hash: str
    token_id: Optional[int]  # tokenId may be None if event parsing fails
    metadata_received: Dict[str, Any]
    token_uri: str


@router.post("/mint", response_model=UIMintResponse)
async def ui_mint_endpoint(request: UIMintRequest):
    """
    Endpoint: POST /api/mint

    Purpose:
      - Frontend calls this after the AI asset and metadata are generated.
      - Backend:
            (1) Uploads metadata.json to Lighthouse (gets ipfs://CID)
            (2) Calls the on-chain mint function
            (3) Returns tx hash, metadata, tokenId and tokenURI back to UI

    Notes:
      - Later we will also upload the IMAGE to IPFS.
      - tokenId is now fetched from the Transfer event in mint.py (best-effort).
    """
    try:
        # ---------------------------------------------------------------------
        # 1) Upload metadata to Lighthouse and obtain a real IPFS CID
        # ---------------------------------------------------------------------
        try:
            token_uri = upload_metadata_to_lighthouse(request.metadata)
        except LighthouseStorageError as e:
            raise HTTPException(status_code=500, detail=f"Metadata upload failed: {e}")

        # ---------------------------------------------------------------------
        # 2) Determine who receives the NFT
        # ---------------------------------------------------------------------
        recipient = os.getenv(
            "MINTMUSE_TEST_RECIPIENT",
            "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
        )

        # ---------------------------------------------------------------------
        # 3) Perform the REAL on-chain mint via mint_nft()
        #    mint.py returns: { status, recipient, tx_hash, token_id, etherscan_link }
        # ---------------------------------------------------------------------
        result = mint_nft(recipient, token_uri)

        if result.get("status") != "success":
            error_msg = result.get("error", "Unknown error while minting")
            raise HTTPException(status_code=500, detail=f"Minting failed: {error_msg}")

        tx_hash = result.get("tx_hash")
        token_id = result.get("token_id")  # NEW: real tokenId (or None)

        if not tx_hash:
            raise HTTPException(status_code=500, detail="Minting succeeded but tx_hash is missing.")

        # ---------------------------------------------------------------------
        # 4) Build final response payload
        # ---------------------------------------------------------------------
        return UIMintResponse(
            status="ok",
            tx_hash=tx_hash,
            token_id=token_id,
            metadata_received=request.metadata,
            token_uri=token_uri,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Minting (UI) failed: {str(e)}")


# -----------------------------------------------------------------------------
# 3) Real on-chain mint endpoint  ->  POST /api/mint-nft
# -----------------------------------------------------------------------------

class MintRequest(BaseModel):
    """Real mint endpoint request (on-chain)."""
    recipient_address: str  # Wallet address that will receive the NFT
    token_uri: str          # Metadata URL (e.g., IPFS or HTTPS)


class MintResponse(BaseModel):
    """Real mint endpoint response (on-chain)."""
    status: str
    recipient: Optional[str] = None
    tx_hash: Optional[str] = None        # align with mint.py return
    token_id: Optional[int] = None       # align with mint.py return
    etherscan_link: Optional[str] = None
    error: Optional[str] = None


@router.post("/mint-nft", response_model=MintResponse)
async def mint_nft_endpoint(request: MintRequest):
    """
    Endpoint: POST /api/mint-nft
    Purpose: Mints an NFT to a specified wallet with given metadata.

    Input:
      - recipient_address: Target wallet address (must be valid).
      - token_uri: Link to metadata (e.g., JSON on IPFS).
    """
    try:
        result = mint_nft(request.recipient_address, request.token_uri)
        return MintResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Minting failed: {str(e)}")


# -----------------------------------------------------------------------------
# 4) Agent interaction endpoint  ->  POST /api/interact
# -----------------------------------------------------------------------------

class InteractRequest(BaseModel):
    """User input for the agent."""
    user_input: str


class InteractResponse(BaseModel):
    """Response from the (future) AI agent."""
    agent_reply: str


@router.post("/interact", response_model=InteractResponse)
async def interact_endpoint(request: InteractRequest):
    """
    Endpoint: POST /api/interact
    Purpose: Simulates an AI agent that responds to user input.

    Development note:
      - Replace placeholder logic with `run_agent_chain()` for live agent.
    """
    try:
        user_message = request.user_input
        response = f"🤖 Agent echoes: '{user_message}'"

        # Later:
        # response = run_agent_chain(user_message)

        return InteractResponse(agent_reply=response)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Interaction failed: {str(e)}")
