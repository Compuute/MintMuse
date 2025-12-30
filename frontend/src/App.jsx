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

  // Calls the backend /api/generate endpoint to create AI asset + metadata
  const generate = async () => {
    if (!prompt.trim()) {
      alert("Please enter a prompt before generating.");
      return;
    }

    setLoading(true);
    setMintError(null);
    setTxHash(null);
    setTokenId(null);

    try {
      const res = await fetch("http://localhost:8000/api/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt }),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        const msg =
          errData.detail || `Generate failed with status ${res.status}`;
        throw new Error(msg);
      }

      const data = await res.json();

      // Save preview image URL
      setPreview(data.preview_url || null);

      // Save metadata for display and later minting
      setMetadata(data.metadata || null);
    } catch (error) {
      console.error("Generation failed:", error);
      alert(`Generation failed: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Calls the backend /api/mint endpoint to mint the NFT (fake or real)
  // Later this can be extended with a direct blockchain call from the frontend.
  const mint = async () => {
    if (!metadata) return;

    setMinting(true);
    setMintError(null);
    setTxHash(null);
    setTokenId(null);

    try {
      const res = await fetch("http://localhost:8000/api/mint", {
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
      setTxHash(data.tx_hash || null);
      setTokenId(
        typeof data.token_id === "number" || typeof data.token_id === "string"
          ? data.token_id
          : null
      );
    } catch (error) {
      console.error("Mint failed:", error);
      setMintError(error.message);
    } finally {
      setMinting(false);
    }
  };

  return (
    <div
      style={{
        padding: 30,
        fontFamily: "sans-serif",
        maxWidth: 700,
        margin: "0 auto",
      }}
    >
      <h1>MintMuse — AI NFT Generator</h1>
      <p style={{ color: "#555", marginBottom: 20 }}>
        Type a creative prompt, generate an AI asset + metadata, then mint it as
        an NFT.
      </p>

      {/* Prompt input field */}
      <label style={{ display: "block", marginBottom: 8 }}>
        <strong>Prompt</strong>
      </label>
      <textarea
        placeholder="Describe the artwork, certificate or asset you want to mint..."
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        style={{
          width: "100%",
          height: 120,
          padding: 10,
          fontSize: 14,
          boxSizing: "border-box",
        }}
      />

      {/* Trigger AI generation */}
      <button
        onClick={generate}
        disabled={loading}
        style={{
          marginTop: 15,
          padding: "10px 18px",
          fontSize: 14,
          cursor: loading ? "default" : "pointer",
        }}
      >
        {loading ? "Generating..." : "Generate AI Asset"}
      </button>

      {/* Display preview image */}
      {preview && (
        <div style={{ marginTop: 30 }}>
          <h3>Preview</h3>
          <img
            src={preview}
            alt="preview"
            style={{
              width: "100%",
              borderRadius: 8,
              border: "1px solid #ddd",
            }}
          />
        </div>
      )}

      {/* Display metadata returned by backend */}
      {metadata && (
        <div style={{ marginTop: 30 }}>
          <h3>Metadata</h3>
          <pre
            style={{
              background: "#f7f7f7",
              padding: 15,
              borderRadius: 8,
              overflowX: "auto",
            }}
          >
            {JSON.stringify(metadata, null, 2)}
          </pre>

          {/* Mint button is only visible once metadata exists */}
          <button
            onClick={mint}
            disabled={minting}
            style={{
              marginTop: 15,
              padding: "10px 18px",
              fontSize: 14,
              cursor: minting ? "default" : "pointer",
            }}
          >
            {minting ? "Minting..." : "Mint NFT"}
          </button>
        </div>
      )}

      {/* Mint result section */}
      {(txHash || tokenId || mintError) && (
        <div style={{ marginTop: 30 }}>
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
