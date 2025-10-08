# mintmuse-agent/app/mint.py

from web3 import Web3
import json
import os
from .config import get_env_var

# Load necessary environment variables
RPC_URL = get_env_var("RPC_URL")
PRIVATE_KEY = get_env_var("PRIVATE_KEY")
ACCOUNT_ADDRESS = get_env_var("ACCOUNT_ADDRESS")
CONTRACT_ADDRESS = get_env_var("CONTRACT_ADDRESS")
ABI_PATH = get_env_var("ABI_PATH", default="solidity/contract_abi.json")

# Establish connection to the blockchain network using HTTP provider
w3 = Web3(Web3.HTTPProvider(RPC_URL))

# Load the contract ABI (interface) from file
with open(ABI_PATH) as abi_file:
    contract_abi = json.load(abi_file)

# Create a contract instance
contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=contract_abi)

def mint_nft(recipient_address, token_uri):
    """
    Mint a new NFT to the specified recipient address.

    Parameters:
    - recipient_address: Ethereum address that will receive the NFT
    - token_uri: URL or IPFS hash that points to the metadata (JSON)

    Returns:
    - Transaction hash (string)
    """

    # Get the number of transactions sent from the account (needed for nonce)
    nonce = w3.eth.get_transaction_count(ACCOUNT_ADDRESS)

    # Prepare the mint transaction
    tx = contract.functions.mintNFT(recipient_address, token_uri).build_transaction({
        'from': ACCOUNT_ADDRESS,
        'nonce': nonce,
        'gas': 300000,
        'gasPrice': w3.to_wei('10', 'gwei')
    })

    # Sign the transaction with the private key
    signed_tx = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)

    # Send the signed transaction to the network
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)

    # Return the transaction hash in readable format
    return w3.to_hex(tx_hash)
