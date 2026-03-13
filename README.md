# MintMuse — AI NFT Generator

MintMuse is an MVP that lets a user describe an artwork in plain text, generates the image with AI, and mints it as an NFT on the Ethereum blockchain (Sepolia testnet).

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        User Browser                         │
│                    React + Vite (frontend/)                  │
│   Step 1: Describe  →  Step 2: Generate  →  Step 3: Mint    │
└──────────────────────────────┬──────────────────────────────┘
                               │ HTTP (REST)
┌──────────────────────────────▼──────────────────────────────┐
│               FastAPI Backend (mintmuse-agent/)              │
│                                                             │
│  POST /api/generate                POST /api/mint           │
│  ┌──────────────────┐       ┌──────────────────────────┐   │
│  │ generate_image.py│       │     mint_route.py         │   │
│  │  HuggingFace API │       │  lighthouse_storage_client│   │
│  │  FLUX.1-schnell  │       │  → IPFS (Lighthouse)      │   │
│  │  (AI model)      │       │  → local fallback         │   │
│  └──────────────────┘       │  mint.py → Web3.py        │   │
│                             └──────────────┬─────────────┘  │
└─────────────────────────────────────────────────────────────┘
                                             │ JSON-RPC
┌────────────────────────────────────────────▼────────────────┐
│          Ethereum Blockchain (Sepolia Testnet)               │
│              MintMuseNFT.sol  (ERC-721)                      │
│              Deployed via Hardhat (contracts/)               │
└─────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React, Vite |
| Backend | Python, FastAPI, Uvicorn |
| AI Image Generation | Hugging Face Inference API — FLUX.1-schnell |
| Blockchain | Solidity, Hardhat, Web3.py |
| Storage | IPFS via Lighthouse (local fallback) |
| Network | Ethereum Sepolia testnet |
| Foundation | GCP Agent Starter Pack (project scaffold) |

---

## Project Structure

```
MintMuse/
├── frontend/               # React UI (Vite)
│   └── src/
│       ├── App.jsx         # Main 3-step app (Describe → Generate → Mint)
│       └── index.css       # Styling
│
├── mintmuse-agent/         # FastAPI backend
│   └── app/
│       ├── main.py         # FastAPI app + CORS + static file serving
│       ├── generate_image.py  # HuggingFace image generation
│       ├── mint.py         # Web3.py blockchain minting
│       ├── routes/
│       │   └── mint_route.py  # /api/generate and /api/mint endpoints
│       └── services/
│           └── lighthouse_storage_client.py  # IPFS upload + local fallback
│
├── contracts/              # Solidity smart contract
│   └── contracts/
│       └── MintMuseNFT.sol # ERC-721 NFT contract
│
└── solidity/               # Compiled ABI (used by backend)
    └── contract_abi.json
```

---

## User Flow

1. **Describe** — User types a text prompt describing the artwork
2. **Generate** — Backend calls HuggingFace API (FLUX.1-schnell) to generate an image; metadata is built and a preview is returned to the frontend
3. **Mint** — Backend uploads the image and metadata to IPFS (Lighthouse), then calls `mintNFT()` on the deployed ERC-721 contract via Web3.py; the transaction hash and token ID are returned to the user with a link to Etherscan

---

## Running Locally

### Prerequisites

- Python 3.10+
- Node.js 18+
- A [HuggingFace](https://huggingface.co) account with an API token
- A funded Sepolia wallet + Alchemy/Infura RPC URL
- A deployed `MintMuseNFT` contract (see `contracts/`)

### Backend

```bash
cd mintmuse-agent
cp .env.example .env   # fill in HF_TOKEN, RPC_URL, PRIVATE_KEY, CONTRACT_ADDRESS etc.
pip install -r requirements.txt
uvicorn app.main:app --reload
```

API docs available at: http://localhost:8000/docs

### Frontend

```bash
cd frontend
npm install
npm run dev
```

App available at: http://localhost:5173

### Smart Contract (deploy once)

```bash
cd contracts
npm install
npx hardhat run scripts/deploy.js --network sepolia
```

Copy the deployed contract address into your `.env`.

---

## Environment Variables

Create `mintmuse-agent/.env`:

```
HF_TOKEN=your_huggingface_token
HF_MODEL=black-forest-labs/FLUX.1-schnell

RPC_URL=https://eth-sepolia.g.alchemy.com/v2/your_key
PRIVATE_KEY=your_wallet_private_key
ACCOUNT_ADDRESS=your_wallet_address
CONTRACT_ADDRESS=deployed_contract_address
ABI_PATH=solidity/contract_abi.json

LIGHTHOUSE_API_KEY=your_lighthouse_key   # optional, uses local fallback if missing
PUBLIC_BASE_URL=http://127.0.0.1:8000
```

---

## Notes

- This is an MVP / proof of concept built for a school assignment (BCU24D-LIA1)
- The GCP Agent Starter Pack was used as the initial project scaffold
- Minting uses the Sepolia testnet — no real ETH is required
