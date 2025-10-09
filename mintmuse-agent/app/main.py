# mintmuse-agent/app/main.py

import os
from fastapi import FastAPI
from app.routes import mint_route

# Print env var for debug (optional)
print("TEST_VAR is:", os.getenv("TEST_VAR"))

# Initialize FastAPI app
app = FastAPI(
    title="MintMuse Agent API",
    description="API for minting NFTs and interacting with the MintMuse AI agent.",
    version="0.1.0"
)

# Include the API routes (both /mint-nft and /interact are defined inside mint_route)
app.include_router(mint_route.router)

# Root endpoint for health check
@app.get("/")
def read_root():
    """
    Health check endpoint.
    """
    return {"message": "✅ MintMuse API is running!"}
