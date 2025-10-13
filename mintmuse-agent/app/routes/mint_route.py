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
    Endpoint: POST /mint-nft
    Purpose: Mints an NFT to a specified wallet with given metadata.
    Input:
        - recipient_address: Target wallet address (must be valid).
        - token_uri: Link to metadata (e.g., JSON on IPFS).
    Output:
        - transaction_hash: Returned if minting is successful.

    Troubleshooting:
        - Ensure RPC URL is active and connected (localhost or Goerli).
        - Check private key and contract address in `.env`.
        - Watch for exceptions from web3 or contract ABI issues.
    """
    try:
        tx_hash = mint_nft(request.recipient_address, request.token_uri)
        return {"transaction_hash": tx_hash}
    except Exception as e:
        # Return 500 if any unexpected error occurs during minting
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
    Endpoint: POST /interact
    Purpose: Simulates an AI agent that responds to user input.
    Input:
        - user_input: A prompt or question from the user.
    Output:
        - agent_reply: Response from the agent (currently placeholder).

    Development Note:
        - Replace placeholder logic with `run_agent_chain()` for live agent.
        - Good for testing backend integration before full AI pipeline.

    Troubleshooting:
        - Watch for missing dependencies or import errors.
        - If using real agent, ensure memory, API key, and model configs are set.
    """

    try:
        # Placeholder agent logic – just echoing back the input
        user_message = request.user_input
        response = f"🤖 Agent echoes: '{user_message}'"

        # 🔄 When agent is ready, replace with:
        # response = run_agent_chain(user_message)

        return {"agent_reply": response}

    except Exception as e:
        # Catch all backend errors and return to frontend
        raise HTTPException(status_code=500, detail=f"Interaction failed: {str(e)}")
