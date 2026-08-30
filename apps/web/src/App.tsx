import { FormEvent, useState } from 'react';

import { ModelViewer } from './ModelViewer';

const apiBaseUrl = import.meta.env.VITE_ARTIFEX_API_URL ?? 'http://127.0.0.1:8000';

export function App() {
  const [assetInput, setAssetInput] = useState('');
  const [assetId, setAssetId] = useState('');

  const openAsset = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setAssetId(assetInput.trim());
  };

  const assetUrl = assetId ? `${apiBaseUrl}/v1/assets/${encodeURIComponent(assetId)}` : undefined;

  return (
    <main className="app-shell" data-qa-id="app-shell">
      <header className="app-header">
        <div>
          <p className="eyebrow">ARTIFEX · Digital Craft</p>
          <h1>3D Modeling System</h1>
          <p className="subtitle">Image → 3D manufacturing workspace</p>
        </div>
      </header>

      <section className="workspace-card" data-qa-id="generated-model-workspace">
        <div className="workspace-toolbar">
          <div>
            <h2>Generated model</h2>
            <p>Inspect an ARTIFEX GLB asset without modifying its source geometry.</p>
          </div>
          <form className="asset-form" onSubmit={openAsset} data-qa-id="asset-open-form">
            <label htmlFor="asset-id">Asset ID</label>
            <div className="asset-form-row">
              <input
                id="asset-id"
                data-qa-id="asset-id-input"
                value={assetInput}
                onChange={(event) => setAssetInput(event.target.value)}
                placeholder="asset_…"
                autoComplete="off"
              />
              <button type="submit" data-qa-id="open-asset-button" disabled={!assetInput.trim()}>
                Open model
              </button>
            </div>
          </form>
        </div>

        <ModelViewer assetUrl={assetUrl} />
      </section>
    </main>
  );
}
