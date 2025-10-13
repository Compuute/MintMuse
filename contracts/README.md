# MintMuse Contracts

This directory contains the **Solidity smart contracts** and Hardhat configuration used for the **MintMuseNFT** deployment.  
It provides the blockchain layer for the MintMuse MVP and integrates with the backend (`mintmuse-agent`) via the deployed contract ABI and address.

---

## 📁 Project Structure

contracts/
├── contracts/ # Solidity smart contracts
│ └── MintMuseNFT.sol # ERC721 NFT contract (MintMuse core)
├── scripts/ # Deployment and utility scripts
│ └── deploy.mjs # Deployment script using Hardhat + ESM
├── artifacts/ # Auto-generated build artifacts (ABI, bytecode)
├── cache/ # Hardhat build cache
├── test/ # Contract test files (Mocha/Chai)
├── hardhat.config.cjs # Hardhat configuration (uses CJS syntax)
├── package.json # Node.js dependencies
├── package-lock.json # Dependency lock file
└── README.md # This file


## Requirements

Before running contracts locally, ensure you have:  
- **Node.js 18+** and **npm** installed  
- **Hardhat**: Ethereum development environment – [Docs](https://hardhat.org)  
- **Ganache / Hardhat Network** (local blockchain)  
- **OpenZeppelin Contracts** library  

Install dependencies:  
```bash
npm install

🚀 Quick Start (Local Testing)

1. Start a local Hardhat node
npx hardhat node

2. Compile contracts
npx hardhat compile

3. Deploy contract locally
npx hardhat run scripts/deploy.mjs --network localhost

Expected output:
🚀 Deploying contract using account: 0x...
✅ MintMuseNFT deployed at address: 0x...
📄 ABI and contract address saved to: ../solidity/MintMuseNFT.json

This JSON file is used by the Python backend (mintmuse-agent) to interact with the contract.

4. Run tests
npx hardhat test

🌐 Deploy to Testnet / Mainnet

Edit your hardhat.config.cjs with network settings (Infura, Alchemy, etc.), then run:

npx hardhat run scripts/deploy.mjs --network goerli

💡 Smart Contract Summary
MintMuseNFT.sol
    Standard: ERC721 (NFT) with metadata storage

    Features:

        .mintNFT(address recipient, string memory tokenURI) → Creates a new NFT and assigns it

        .Uses Ownable (only owner can mint)

        .Metadata stored on-chain (tokenURI)

        .Constructor: 
            constructor(address initialOwner) 
                ERC721("MintMuseNFT", "MMNFT") 
                Ownable(initialOwner) {}

🧪 Run Tests
npx hardhat test

🛠️ Troubleshooting
Common errors and fixes:

    HH700: Artifact for contract not found
    → Ensure MintMuseNFT.sol is inside contracts/ and re-run npx hardhat compile.

    ECONNRESET during deployment
    → Make sure npx hardhat node is running in another terminal before deploying.

    TypeError: nft.deployed is not a function
    → Use await nft.waitForDeployment() instead of .deployed() in deploy scripts.

    invalid overrides parameter
    → Check constructor arguments in deploy.mjs match your contract.