import { FormEvent, useState } from 'react';

import { ModelViewer } from './ModelViewer';

const apiBaseUrl = import.meta.env.VITE_ARTIFEX_API_URL ?? 'http://127.0.0.1:8000';

type GenerationState = 'idle' | 'generating' | 'ready' | 'error';

interface GenerationResponse {
  mesh_asset_id: string;
  provider: string;
  model: string;
}

export function App() {
  const [assetInput, setAssetInput] = useState('');
  const [assetId, setAssetId] = useState('');
  const [image, setImage] = useState<File | null>(null);
  const [provider, setProvider] = useState('fixture');
  const [generationState, setGenerationState] = useState<GenerationState>('idle');
  const [generationMessage, setGenerationMessage] = useState(
    'Use Fixture for a GPU-free local demo or TRELLIS when its runner is configured.',
  );

  const openAsset = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setAssetId(assetInput.trim());
  };

  const generate = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!image) return;

    setGenerationState('generating');
    setGenerationMessage('Preprocessing image and generating model…');
    const body = new FormData();
    body.append('file', image);

    try {
      const response = await fetch(
        `${apiBaseUrl}/v1/image-to-3d/generate?provider=${encodeURIComponent(provider)}`,
        { method: 'POST', body },
      );
      const payload = (await response.json()) as GenerationResponse | { detail?: { message?: string } };
      if (!response.ok || !('mesh_asset_id' in payload)) {
        const detail = 'detail' in payload ? payload.detail?.message : undefined;
        throw new Error(detail ?? `Generation failed with HTTP ${response.status}`);
      }

      setAssetId(payload.mesh_asset_id);
      setAssetInput(payload.mesh_asset_id);
      setGenerationState('ready');
      setGenerationMessage(`Generated with ${payload.provider} · ${payload.model}`);
    } catch (error) {
      setGenerationState('error');
      setGenerationMessage(error instanceof Error ? error.message : 'Generation failed');
    }
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

      <section className="generator-card" data-qa-id="image-to-3d-generator">
        <div>
          <p className="eyebrow">Image → 3D</p>
          <h2>Generate a model</h2>
          <p className="generator-description">
            Upload an image, preprocess it and send it through the selected ARTIFEX provider.
          </p>
        </div>
        <form className="generator-form" onSubmit={generate} data-qa-id="image-to-3d-form">
          <label htmlFor="source-image">Source image</label>
          <input
            id="source-image"
            type="file"
            accept="image/png,image/jpeg,image/webp"
            data-qa-id="source-image-input"
            onChange={(event) => setImage(event.target.files?.[0] ?? null)}
          />
          <label htmlFor="provider">Provider</label>
          <select
            id="provider"
            value={provider}
            data-qa-id="provider-select"
            onChange={(event) => setProvider(event.target.value)}
          >
            <option value="fixture">Fixture · local demo</option>
            <option value="trellis">TRELLIS · configured GPU runner</option>
          </select>
          <button
            type="submit"
            data-qa-id="generate-model-button"
            disabled={!image || generationState === 'generating'}
          >
            {generationState === 'generating' ? 'Generating…' : 'Generate 3D model'}
          </button>
        </form>
        <p
          className={`generation-status generation-status--${generationState}`}
          data-qa-id="generation-status"
        >
          {generationMessage}
        </p>
      </section>

      <section className="workspace-card" data-qa-id="generated-model-workspace">
        <div className="workspace-toolbar">
          <div>
            <h2>Generated model</h2>
            <p>Inspect the generated GLB without modifying its source geometry.</p>
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
