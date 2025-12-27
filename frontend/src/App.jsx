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

  // Calls the backend /generate endpoint
  const generate = async () => {
    setLoading(true);

    try {
      const res = await fetch("http://localhost:8000/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt }),
      });

      const data = await res.json();

      // Save preview image URL
      setPreview(data.preview_url);

      // Save metadata for display and later minting
      setMetadata(data.metadata);
    } catch (error) {
      console.error("Generation failed:", error);
    } finally {
      setLoading(false);
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
        </div>
      )}
    </div>
  );
}

export default App;
