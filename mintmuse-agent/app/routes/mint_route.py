# app/routes/mint_route.py

from typing import Optional, Any, Dict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..mint import mint_nft

# Optional: Import logic from agent (can be activated later)
# from agents.root_agent import run_agent_chain

# IMPORTANT:
# Do NOT set prefix="/api" here because main.py already adds prefix="/api"
router = APIRouter()

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
    return GenerateResponse(
      preview_url="https://placehold.co/800x500/png?text=AI+Preview",
      metadata={
        "name": "Test MintMuse NFT",
        "description": f"AI-generated asset based on prompt: {request.prompt}",
        "attributes": [
          {"trait_type": "generator", "value": "MintMuse stub"},
          {"trait_type": "env", "value": "local-dev"},
        ],
      },
    )
  except Exception as e:
    raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")



# -----------------------------------------------------------------------------
# 2) Simple “fake mint” used by the React UI  ->  POST /api/mint
# -----------------------------------------------------------------------------


class UIMintRequest(BaseModel):
  """Request body used by the React frontend for /api/mint."""
  prompt: str
  metadata: Dict[str, Any]


class UIMintResponse(BaseModel):
  """Response body returned to the React frontend after fake mint."""
  status: str
  tx_hash: str
  token_id: int
  metadata_received: Dict[str, Any]


@router.post("/mint", response_model=UIMintResponse)
async def ui_mint_endpoint(request: UIMintRequest):
  """
  Endpoint: POST /api/mint
  Purpose: Simulates a blockchain mint for local testing.
           The React app calls this after generation.

  Later:
    - Replace this stub with a real call to the ERC-721 contract
      using web3.py or ethers via a dedicated service.
  """
  try:
    fake_tx_hash = "0x" + "abcd" * 16
    fake_token_id = 1

    return UIMintResponse(
      status="ok",
      tx_hash=fake_tx_hash,
      token_id=fake_token_id,
      metadata_received=request.metadata,
    )
  except Exception as e:
    raise HTTPException(status_code=500, detail=f"Minting (UI stub) failed: {str(e)}")


# -----------------------------------------------------------------------------
# 3) Real on-chain mint endpoint  ->  POST /api/mint-nft
# -----------------------------------------------------------------------------


class MintRequest(BaseModel):
  """Real mint endpoint request (on-chain)."""
  recipient_address: str  # Wallet address that will receive the NFT
  token_uri: str          # Metadata URL (e.g., IPFS or HTTPS)


class MintResponse(BaseModel):
  """Real mint endpoint response (on-chain)."""
  status: str                          # Success or error message
  recipient: Optional[str] = None      # Wallet address that received the NFT
  transaction_hash: Optional[str] = None   # Blockchain transaction hash
  etherscan_link: Optional[str] = None     # Etherscan link for transaction
  error: Optional[str] = None              # Error message if minting fails


@router.post("/mint-nft", response_model=MintResponse)
async def mint_nft_endpoint(request: MintRequest):
  """
  Endpoint: POST /api/mint-nft
  Purpose: Mints an NFT to a specified wallet with given metadata.

  Input:
    - recipient_address: Target wallet address (must be valid).
    - token_uri: Link to metadata (e.g., JSON on IPFS).

  Output:
    - transaction_hash: Returned if minting is successful.

  Troubleshooting:
    - Ensure RPC URL is active and connected (localhost or testnet).
    - Check private key and contract address in `.env`.
    - Watch for exceptions from web3 or contract ABI issues.
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
