import { useState } from "react";

// Derive current step from app state
function getStep(preview, txHash) {
  if (txHash) return 3;
  if (preview) return 2;
  return 1;
}

function StepIndicator({ current }) {
  const steps = ["Describe", "Generate", "Mint"];
  return (
    <div className="steps">
      {steps.map((label, i) => {
        const num = i + 1;
        const state = num < current ? "done" : num === current ? "active" : "";
        return (
          <div key={num} style={{ display: "flex", alignItems: "center" }}>
            <div className={`step ${state}`}>
              <div className="step-num">{num < current ? "✓" : num}</div>
              <span>{label}</span>
            </div>
            {i < steps.length - 1 && <div className="step-divider" />}
          </div>
        );
      })}
    </div>
  );
}

export default function App() {
  const [prompt,    setPrompt]    = useState("");
  const [loading,   setLoading]   = useState(false);
  const [preview,   setPreview]   = useState(null);
  const [metadata,  setMetadata]  = useState(null);
  const [minting,      setMinting]      = useState(false);
  const [txHash,       setTxHash]       = useState(null);
  const [tokenId,      setTokenId]      = useState(null);
  const [etherscanUrl, setEtherscanUrl] = useState(null);
  const [mintError,    setMintError]    = useState(null);

  const step = getStep(preview, txHash);

  // ── Generate ──────────────────────────────────────────────────────────────
  const generate = async () => {
    if (!prompt.trim()) return;

    setLoading(true);
    setPreview(null);
    setMetadata(null);
    setTxHash(null);
    setTokenId(null);
    setEtherscanUrl(null);
    setMintError(null);

    try {
      const res = await fetch("http://127.0.0.1:8000/api/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Generation failed (${res.status})`);
      }

      const data = await res.json();
      setPreview(data.preview_url || null);
      setMetadata(data.metadata   || null);
    } catch (e) {
      alert(`Generation failed: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  // ── Mint ──────────────────────────────────────────────────────────────────
  const mint = async () => {
    if (!metadata) return;

    setMinting(true);
    setTxHash(null);
    setTokenId(null);
    setEtherscanUrl(null);
    setMintError(null);

    try {
      const res = await fetch("http://127.0.0.1:8000/api/mint", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt, metadata }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Minting failed (${res.status})`);
      }

      const data = await res.json();
      setTxHash(data.tx_hash         || null);
      setTokenId(data.token_id       ?? null);
      setEtherscanUrl(data.etherscan_url || null);
    } catch (e) {
      setMintError(e.message);
    } finally {
      setMinting(false);
    }
  };

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <div className="app">

      {/* Header */}
      <header className="header">
        <div className="logo">
          <div className="logo-icon">✦</div>
          <span className="logo-text">MintMuse</span>
        </div>
        <h1>AI NFT Generator</h1>
        <p>Describe your vision — we generate the art and mint it on-chain.</p>
      </header>

      {/* Step indicator */}
      <StepIndicator current={step} />

      {/* Prompt card */}
      <div className="card">
        <label className="prompt-label">Your prompt</label>
        <textarea
          placeholder="Describe the artwork or asset you want to mint…"
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && e.metaKey && generate()}
        />
        <button
          className="btn-primary"
          onClick={generate}
          disabled={loading || !prompt.trim()}
        >
          {loading ? (
            <><div className="spinner" /> Generating image…</>
          ) : (
            <>✦ Generate AI Asset</>
          )}
        </button>
      </div>

      {/* Image preview */}
      {preview && (
        <div className="section">
          <p className="section-title">Preview</p>
          <img
            className="preview-img"
            src={preview}
            alt="AI-generated NFT preview"
            onError={(e) => {
              e.target.src = "https://placehold.co/800x500/0d0d12/444?text=Image+unavailable";
            }}
          />
        </div>
      )}

      {/* NFT Info + Mint */}
      {metadata && (
        <div className="section">
          <p className="section-title">NFT Info</p>

          <div className="nft-card">
            <p className="nft-label">Name</p>
            <p className="nft-name">{metadata.name}</p>
            <p className="nft-description">{metadata.description}</p>

            {metadata.attributes?.length > 0 && (
              <div className="nft-tags">
                {metadata.attributes.map((a, i) => (
                  <span key={i} className="nft-tag">
                    <span>{a.trait_type}:</span>{a.value}
                  </span>
                ))}
              </div>
            )}
          </div>

          {/* Technical details collapsible */}
          <details>
            <summary>▸ Technical details (JSON)</summary>
            <pre>{JSON.stringify(metadata, null, 2)}</pre>
          </details>

          {/* Mint button — only show if not yet minted */}
          {!txHash && (
            <button className="btn-mint" onClick={mint} disabled={minting}>
              {minting ? (
                <><div className="spinner" /> Minting on-chain…</>
              ) : (
                <>⬡ Mint NFT</>
              )}
            </button>
          )}
        </div>
      )}

      {/* Mint result */}
      {txHash && (
        <div className="section">
          <p className="section-title">Mint result</p>
          <div className="mint-success">
            <div className="mint-success-title">
              ✓ NFT minted successfully
            </div>

            {tokenId !== null && (
              <div className="mint-row">
                <span className="mint-row-label">Token ID</span>
                <span className="token-id-badge">#{tokenId}</span>
              </div>
            )}

            <div className="mint-row">
              <span className="mint-row-label">Transaction</span>
              <span className="mint-row-value">{txHash}</span>
            </div>

            {etherscanUrl && (
              <a
                className="etherscan-link"
                href={etherscanUrl}
                target="_blank"
                rel="noopener noreferrer"
              >
                View on Etherscan ↗
              </a>
            )}
          </div>
        </div>
      )}

      {/* Mint error */}
      {mintError && (
        <div className="section">
          <div className="mint-error">
            <strong>Mint failed:</strong> {mintError}
          </div>
        </div>
      )}

    </div>
  );
}
