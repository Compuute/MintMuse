from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..mint import mint_nft

# Optional: Import logic from agent (can be activated later)
# from agents.root_agent import run_agent_chain

# Initialize a new API router
router = APIRouter()

# --------------------------
# Mint NFT Endpoint
# --------------------------

class MintRequest(BaseModel):
    recipient_address: str  # Wallet address that will receive the NFT
    token_uri: str          # Metadata URL (e.g., IPFS or HTTPS)

class MintResponse(BaseModel):
    transaction_hash: str   # Blockchain transaction hash

@router.post("/mint-nft", response_model=MintResponse)
async def mint_nft_endpoint(request: MintRequest):
    """
    Endpoint to mint an NFT on the blockchain.
    Request body:
        - recipient_address: Ethereum-compatible wallet address.
        - token_uri: Metadata describing the NFT (image, name, etc).
    Response:
        - transaction_hash: ID of the blockchain transaction.
    """
    try:
        tx_hash = mint_nft(request.recipient_address, request.token_uri)
        return {"transaction_hash": tx_hash}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Minting failed: {str(e)}")

# --------------------------
# Interact with Agent Endpoint
# --------------------------

class InteractRequest(BaseModel):
    user_input: str  # The user's input to the agent

class InteractResponse(BaseModel):
    agent_reply: str  # The agent's generated reply

@router.post("/interact", response_model=InteractResponse)
async def interact_endpoint(request: InteractRequest):
    """
    Endpoint to interact with the AI agent.
    Request body:
        - user_input: A message or instruction to the agent.
    Response:
        - agent_reply: The agent's generated response.
    """

    try:
        # Placeholder agent logic – just echoing back the input
        user_message = request.user_input
        response = f"🤖 Agent echoes: '{user_message}'"

        # 🔄 When agent is ready, replace with:
        # response = run_agent_chain(user_message)

        return {"agent_reply": response}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Interaction failed: {str(e)}")
