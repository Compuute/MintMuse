// scripts/deploy.mjs

// ✅ ESM-style import of Hardhat
import hre from 'hardhat';

// ✅ Node.js file system and path modules for saving contract artifacts
import fs from 'fs';
import path from 'path';

async function main() {
  // 🔑 Get deployer account from local Hardhat network
  const [deployer] = await hre.ethers.getSigners();

  console.log(`🚀 Deploying contract using account: ${deployer.address}`);

  // 🛠️ Get contract factory for MintMuseNFT (matches Solidity contract name)
  const MintMuseNFT = await hre.ethers.getContractFactory('MintMuseNFT');

  // 🏗️ Deploy contract with constructor argument (initialOwner = deployer)
  const nft = await MintMuseNFT.deploy(deployer.address);

  // ⏳ Wait for deployment to complete
  await nft.waitForDeployment();

  // 📍 Get deployed contract address
  const address = await nft.getAddress();

  console.log(`✅ MintMuseNFT deployed at address: ${address}`);

  // 🧩 Prepare contract data for frontend/backend integration
  const contractData = {
    address: address,
    abi: JSON.parse(MintMuseNFT.interface.formatJson()), // Serialize ABI to JSON
  };

  // 📁 Define output path: 2 levels up → /solidity/MintMuseNFT.json
  const outputDir = path.resolve('..', '..', 'solidity');
  const outputFile = path.join(outputDir, 'MintMuseNFT.json');

  // 📂 Create directory if it doesn't exist
  fs.mkdirSync(outputDir, { recursive: true });

  // 📝 Write ABI and address to file
  fs.writeFileSync(outputFile, JSON.stringify(contractData, null, 2));

  console.log(`📄 ABI and contract address saved to: ${outputFile}`);
}

// 🛡️ Run main and catch errors
main().catch((error) => {
  console.error('❌ Deployment failed:', error);
  process.exit(1);
});
