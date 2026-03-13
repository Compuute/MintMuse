# MintMuse Contracts

This directory contains the **Solidity smart contracts** and Hardhat configuration used for the **MintMuseNFT** deployment.
It provides the blockchain layer for the MintMuse MVP and integrates with the backend (`mintmuse-agent`) via the deployed contract ABI and address.

---

## Project Structure

```
contracts/
├── contracts/
│   └── MintMuseNFT.sol       # ERC-721 NFT contract
├── scripts/
│   ├── deploy.mjs             # Deployment script (ESM)
│   └── modules/               # Ignition deploy modules
├── ignition/                  # Hardhat Ignition config
├── artifacts/                 # Auto-generated ABI + bytecode (git-ignored)
├── cache/                     # Hardhat build cache (git-ignored)
├── test/                      # Contract tests (Mocha/Chai)
├── hardhat.config.cjs         # Hardhat configuration
├── package.json
└── README.md
```

---

## Requirements

- Node.js 18+
- npm

Install dependencies:

```bash
npm install
```

---

## Quick Start (Local)

**1. Start a local Hardhat node:**

```bash
npx hardhat node
```

**2. Compile contracts:**

```bash
npx hardhat compile
```

**3. Deploy locally:**

```bash
npx hardhat run scripts/deploy.mjs --network localhost
```

Expected output:
```
🚀 Deploying contract using account: 0x...
✅ MintMuseNFT deployed at address: 0x...
📄 ABI saved to: ../solidity/MintMuseNFT.json
```

**4. Run tests:**

```bash
npx hardhat test
```

---

## Deploy to Sepolia Testnet

Add your network config to `hardhat.config.cjs`, then run:

```bash
npx hardhat run scripts/deploy.mjs --network sepolia
```

The deploy script saves the contract address and ABI to `../solidity/MintMuseNFT.json`, which is used by the Python backend (`mintmuse-agent`) to interact with the contract.

---

## Smart Contract Summary

**MintMuseNFT.sol**

| Property | Value |
|---|---|
| Standard | ERC-721 |
| Token Name | MintMuseNFT |
| Symbol | MMNFT |
| Access Control | Ownable (only owner can mint) |

**Key function:**

```solidity
function mintNFT(address recipient, string memory tokenURI) public onlyOwner
```

Mints a new NFT to `recipient` with the given `tokenURI` (IPFS metadata URI).

---

## Troubleshooting

| Error | Fix |
|---|---|
| `HH700: Artifact not found` | Make sure `MintMuseNFT.sol` is inside `contracts/` and run `npx hardhat compile` |
| `ECONNRESET during deployment` | Ensure `npx hardhat node` is running in a separate terminal |
| `nft.deployed is not a function` | Use `await nft.waitForDeployment()` instead of `.deployed()` |
| `invalid overrides parameter` | Check that constructor arguments in `deploy.mjs` match the contract |
