import { useState } from "react";

function App() {
  // User prompt text
  const [prompt, setPrompt] = useState("");

  // Loading indicator during AI generation
  const [loading, setLoading] = useState(false);

  // Image preview URL returned from backend
  const [preview, setPreview] = useState(null);

  // NFT metadata returned from backend (JSON object)
  const [metadata, setMetadata] = useState(null);

  // Minting state
  const [minting, setMinting] = useState(false);
  const [txHash, setTxHash] = useState(null);
  const [tokenId, setTokenId] = useState(null);
  const [mintError, setMintError] = useState(null);

  // Calls the backend /generate endpoint to create AI asset + metadata
  const generate = async () => {
    setLoading(true);
    setMintError(null);
    setTxHash(null);
    setTokenId(null);

    try {
      const res = await fetch("http://localhost:8000/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt }),
      });

      if (!res.ok) {
        throw new Error(`Generate failed with status ${res.status}`);
      }

      const data = await res.json();

      // Save preview image URL
      setPreview(data.preview_url);

      // Save metadata for display and later minting
      setMetadata(data.metadata);
    } catch (error) {
      console.error("Generation failed:", error);
      alert("Generation failed. Check backend logs.");
    } finally {
      setLoading(false);
    }
  };

  // Calls the backend /mint endpoint to (fake) mint the NFT
  // Later this will be replaced or extended with a real blockchain call.
  const mint = async () => {
    if (!metadata) return;

    setMinting(true);
    setMintError(null);
    setTxHash(null);
    setTokenId(null);

    try {
      const res = await fetch("http://localhost:8000/mint", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          prompt,
          metadata,
        }),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        const msg = errData.detail || `Mint failed with status ${res.status}`;
        throw new Error(msg);
      }

      const data = await res.json();

      // Save tx hash and token id returned by backend
      setTxHash(data.tx_hash);
      setTokenId(data.token_id);
    } catch (error) {
      console.error("Mint failed:", error);
      setMintError(error.message);
    } finally {
      setMinting(false);
    }
  };

  return (
    <div style={{ padding: 30, fontFamily: "sans-serif", maxWidth: 600 }}>
      <h1>MintMuse — AI NFT Generator</h1>

      {/* Prompt input field */}
      <textarea
        placeholder="Enter your prompt..."
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        style={{ width: "100%", height: 120 }}
      />

      {/* Trigger AI generation */}
      <button
        onClick={generate}
        disabled={loading}
        style={{ marginTop: 15, padding: 10 }}
      >
        {loading ? "Generating..." : "Generate"}
      </button>

      {/* Display preview image */}
      {preview && (
        <div style={{ marginTop: 20 }}>
          <h3>Preview</h3>
          <img src={preview} alt="preview" style={{ width: "100%" }} />
        </div>
      )}

      {/* Display metadata returned by backend */}
      {metadata && (
        <div style={{ marginTop: 20 }}>
          <h3>Metadata</h3>
          <pre>{JSON.stringify(metadata, null, 2)}</pre>

          {/* Mint button is only visible once metadata exists */}
          <button
            onClick={mint}
            disabled={minting}
            style={{ marginTop: 15, padding: 10 }}
          >
            {minting ? "Minting..." : "Mint NFT"}
          </button>
        </div>
      )}

      {/* Mint result section */}
      {(txHash || tokenId || mintError) && (
        <div style={{ marginTop: 20 }}>
          <h3>Mint result</h3>
          {txHash && (
            <p>
              <strong>Tx hash:</strong> {txHash}
            </p>
          )}
          {tokenId !== null && (
            <p>
              <strong>Token ID:</strong> {tokenId}
            </p>
          )}
          {mintError && (
            <p style={{ color: "red" }}>
              <strong>Error:</strong> {mintError}
            </p>
          )}
        </div>
      )}
    </div>
  );
}

export default App;
