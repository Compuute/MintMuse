// scripts/deploy.js
const { ethers } = require('hardhat');

async function main() {
  const MintMuseNFT = await ethers.getContractFactory('MintMuseNFT');
  const mintMuseNFT = await MintMuseNFT.deploy();

  await mintMuseNFT.deployed();

  console.log(`✅ Contract deployed to: ${mintMuseNFT.address}`);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
