# mintmuse-agent/app/routes/mint_route.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..mint import mint_nft

# Initialize a new API router
router = APIRouter()

# Define the request body model for NFT minting
class MintRequest(BaseModel):
    recipient_address: str
    token_uri: str

# Define the response model
class MintResponse(BaseModel):
    transaction_hash: str

@router.post("/mint-nft", response_model=MintResponse)
async def mint_nft_endpoint(request: MintRequest):
    """
    Endpoint to mint an NFT on the blockchain.
    - recipient_address: The wallet address to receive the NFT.
    - token_uri: A URL or IPFS link pointing to the NFT metadata.

    Returns:
        The transaction hash of the minting transaction.
    """
    try:
        # Call the minting function from app/mint.py
        tx_hash = mint_nft(request.recipient_address, request.token_uri)
        return {"transaction_hash": tx_hash}
    except Exception as e:
        # Handle any errors and return a 500 response
        raise HTTPException(status_code=500, detail=f"Minting failed: {str(e)}")
