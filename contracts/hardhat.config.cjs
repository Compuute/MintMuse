require("@nomicfoundation/hardhat-toolbox");
require("dotenv").config(); // loads contracts/.env when running from contracts/

const SEPOLIA_RPC_URL     = process.env.SEPOLIA_RPC_URL     || "";
const SEPOLIA_PRIVATE_KEY = process.env.SEPOLIA_PRIVATE_KEY || "";

/** @type import('hardhat/config').HardhatUserConfig */
module.exports = {
  solidity: "0.8.30",

  networks: {
    // ── Local Hardhat node (default — nothing changes here) ──────────────
    localhost: {
      url: "http://127.0.0.1:8545",
    },

    // ── Sepolia testnet ───────────────────────────────────────────────────
    // Deploy: npx hardhat run scripts/deploy.mjs --network sepolia
    sepolia: {
      url: SEPOLIA_RPC_URL,
      accounts: SEPOLIA_PRIVATE_KEY ? [SEPOLIA_PRIVATE_KEY] : [],
      chainId: 11155111,
    },
  },
};
