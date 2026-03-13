# app/routes/mint_route.py

import logging
import os
import uuid
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

from PIL import Image, ImageDraw

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# NEW: Gemini SDK (reads GEMINI_API_KEY from environment)
from google import genai

from ..mint import mint_nft
from app.services.lighthouse_storage_client import (
    upload_metadata_to_lighthouse,
    upload_file_to_lighthouse,  # NEW
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
# 0) Gemini toggle + helper (minimal change, safe fallback)
# -----------------------------------------------------------------------------
# If USE_GEMINI=true, /api/generate will first enhance the prompt via Gemini,
# then continue the exact same preview + metadata flow as before.
USE_GEMINI = os.getenv("USE_GEMINI", "false").lower() == "true"
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")  # Fast default model

# Image generation toggle — set USE_IMAGEN=true in .env to enable AI image generation
USE_IMAGEN = os.getenv("USE_IMAGEN", "false").lower() == "true"


def _gemini_prompt_enhance(user_prompt: str) -> str:
    """
    Enhance the user's prompt using Gemini (text-only).
    Returns a single string. If Gemini returns empty text, the original prompt is used.

    IMPORTANT:
    - This function must not break the existing /api/generate flow.
    - Any exception should be handled by the caller and fallback to original prompt.
    """
    client = genai.Client()  # Automatically reads GEMINI_API_KEY from environment

    system_instructions = (
        "You are an expert prompt engineer for image generation.\n"
        "Rewrite the user's idea into a concise, high-quality image prompt.\n"
        "Return ONLY the final prompt as plain text (no markdown, no JSON)."
    )

    resp = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=[system_instructions, f"User idea: {user_prompt.strip()}"],
    )

    enhanced = (getattr(resp, "text", "") or "").strip()
    return enhanced if enhanced else user_prompt


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

        # File name is determined after generation to match the mime-type extension
        file_id = str(uuid.uuid4())

        # ---------------------------------------------------------------------
        # Optionally enhance the prompt via Gemini
        # - If Gemini fails, fallback to the original request.prompt
        # ---------------------------------------------------------------------
        raw_prompt = (request.prompt or "").strip()
        final_prompt = raw_prompt
        gemini_used = False

        if USE_GEMINI and raw_prompt:
            try:
                final_prompt = _gemini_prompt_enhance(raw_prompt)
                gemini_used = (final_prompt.strip() != raw_prompt.strip())
            except Exception:
                final_prompt = raw_prompt
                gemini_used = False

        # ---------------------------------------------------------------------
        # IMAGE GENERATION: Try AI generation → fall back to PIL on failure
        # ---------------------------------------------------------------------
        imagen_used = False
        filename = f"{file_id}.png"   # default, updated below based on mime-type
        rel_path = f"app/storage/previews/{filename}"

        if USE_IMAGEN:
            try:
                from ..generate_image import generate_image_bytes
                img_bytes, mime_type = generate_image_bytes(final_prompt)
                # Pick the right file extension based on mime-type
                ext = "jpg" if "jpeg" in mime_type else "png"
                filename = f"{file_id}.{ext}"
                rel_path = f"app/storage/previews/{filename}"
                with open(rel_path, "wb") as f:
                    f.write(img_bytes)
                imagen_used = True
                logger.info(f"AI image saved to {rel_path}")
            except Exception as img_err:
                logger.warning(f"AI image generation failed, falling back to PIL: {img_err}")

        if not imagen_used:
            # PIL fallback: renders a text preview image with the prompt
            import textwrap
            img = Image.new("RGB", (800, 500), color=(245, 245, 250))
            draw = ImageDraw.Draw(img)

            # Header banner
            draw.rectangle([(0, 0), (800, 80)], fill=(79, 70, 229))
            draw.text((400, 40), "✦ MintMuse NFT Preview ✦", fill=(255, 255, 255), anchor="mm")

            # Divider
            draw.rectangle([(40, 95), (760, 97)], fill=(200, 195, 245))

            # Prompt label
            draw.text((400, 125), "Prompt", fill=(99, 102, 241), anchor="mm")

            # Wrap prompt text so it fits on the image
            prompt_text = (final_prompt or "").strip()
            wrapped = textwrap.fill(prompt_text, width=60)
            lines = wrapped.splitlines()
            if len(lines) > 5:
                lines = lines[:4]
                lines[-1] = lines[-1][:57] + "..."
            wrapped = "\n".join(lines)

            draw.multiline_text(
                (400, 260),
                wrapped,
                fill=(30, 27, 75),
                anchor="mm",
                align="center",
                spacing=8,
            )

            # Footer
            draw.rectangle([(0, 460), (800, 500)], fill=(238, 237, 255))
            draw.text((400, 480), "PIL fallback · Local dev preview", fill=(99, 102, 241), anchor="mm")

            img.save(rel_path)

        # Use 127.0.0.1 to match local testing via curl/browser
        preview_url = f"http://127.0.0.1:8000/previews/{filename}"

        # Best-effort upload the image to Lighthouse/IPFS.
        # If Lighthouse fails, keep the local preview URL so nothing breaks.
        image_uri_for_metadata = preview_url
        try:
            image_uri_for_metadata = upload_file_to_lighthouse(rel_path)
        except LighthouseStorageError:
            pass

        # Dynamic NFT name from the prompt (first 5 words, capitalized)
        name_words = (final_prompt or raw_prompt).split()[:5]
        nft_name = " ".join(w.capitalize() for w in name_words) if name_words else "MintMuse NFT"

        # Pick generator label based on what was actually used
        if imagen_used:
            generator_value = "Hugging Face FLUX"
        elif gemini_used:
            generator_value = "Gemini-enhanced PIL"
        else:
            generator_value = "PIL stub"

        return GenerateResponse(
            preview_url=preview_url,
            metadata={
                "name": nft_name,
                "description": f"AI-generated NFT based on prompt: {final_prompt}",
                "image": image_uri_for_metadata,
                "original_prompt": raw_prompt,
                "gemini_used": gemini_used,
                "imagen_used": imagen_used,
                "attributes": [
                    {"trait_type": "generator", "value": generator_value},
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
    token_id: Optional[int]       # tokenId may be None if event parsing fails
    metadata_received: Dict[str, Any]
    token_uri: str
    storage_used: Optional[str] = None
    etherscan_url: Optional[str] = None  # clickable link on Sepolia, None on local


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
            storage_used = "lighthouse"
        except LighthouseStorageError as e:
          # Fallback to local storage
          logger.warning(f"Lighthouse unavailable, using local storage fallback. {e}")
          token_uri = "ipfs://DEMO_FALLBACK_METADATA"
          storage_used = "fallback"

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

        tx_hash       = result.get("tx_hash")
        token_id      = result.get("token_id")       # real tokenId (or None)
        etherscan_url = result.get("etherscan_url")  # Sepolia link (or None on local)

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
            storage_used=storage_used,
            etherscan_url=etherscan_url,
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
