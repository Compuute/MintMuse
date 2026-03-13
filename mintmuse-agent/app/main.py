# app/main.py

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.routes import mint_route

# Debug (optional)
print("TEST_VAR is:", os.getenv("TEST_VAR"))

app = FastAPI(
    title="MintMuse Agent API",
    description="API for minting NFTs and interacting with the MintMuse AI agent.",
    version="0.1.0",
)

# ---- CORS: allow Vite + localhost variants ----
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:5175",
        "http://127.0.0.1:5175",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- Serve local NFT artifacts (fallback when IPFS is down) ----
# metadata JSON:  http://localhost:8000/metadata/<tokenId>.json
# preview images: http://localhost:8000/previews/<filename>.png
app.mount(
    "/metadata",
    StaticFiles(directory="app/storage/metadata"),
    name="metadata",
)
app.mount(
    "/previews",
    StaticFiles(directory="app/storage/previews"),
    name="previews",
)

# ---- API routes ----
app.include_router(mint_route.router, prefix="/api")

@app.get("/")
def read_root():
    return {
        "message": "✅ MintMuse API is running!",
        "docs": "http://localhost:8000/docs",
    }
