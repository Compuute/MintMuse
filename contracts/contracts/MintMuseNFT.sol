// SPDX-License-Identifier: MIT
pragma solidity ^0.8.30;

import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract MintMuseNFT is ERC721URIStorage, Ownable {
    uint256 private _tokenIds;

    constructor(address initialOwner) ERC721("MintMuseNFT", "MMNFT") Ownable(initialOwner) {
        // Start token ID counter at 0
        _tokenIds = 0;
    }

    function mintNFT(address recipient, string memory tokenURI) public onlyOwner returns (uint256) {
        _tokenIds++;
        uint256 newItemId = _tokenIds;
        _mint(recipient, newItemId);
        _setTokenURI(newItemId, tokenURI);
        return newItemId;
    }
}
