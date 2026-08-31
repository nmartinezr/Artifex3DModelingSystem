import { FormEvent, useState } from 'react';

import { ModelViewer } from './ModelViewer';

const apiBaseUrl = import.meta.env.VITE_ARTIFEX_API_URL ?? 'http://127.0.0.1:8000';

type GenerationState = 'idle' | 'generating' | 'ready' | 'error';
type ExportFormat = '3mf' | 'stl' | 'glb';

interface AnalysisFinding {
  code: string;
  severity: 'info' | 'warning' | 'error';
  message: string;
}

interface MeshAnalysis {
  score: number;
  findings: AnalysisFinding[];
  exportBlocked: boolean;
  metrics: {
    triangleCount: number;
    vertexCount: number;
    componentCount: number;
    watertight: boolean | null;
    manifold: boolean | null;
    dimensionsMm: number[] | null;
    durationMs: number;
  };
}

interface GenerationResponse {
  mesh_asset_id: string;
  provider: string;
  model: string;
  analysis: MeshAnalysis;
}

interface ExportResponse {
  export_asset_id: string;
  format: ExportFormat;
  warning: string | null;
}

export function App() {
  const [assetInput, setAssetInput] = useState('');
  const [assetId, setAssetId] = useState('');
  const [image, setImage] = useState<File | null>(null);
  const [provider, setProvider] = useState('fixture');
  const [generationState, setGenerationState] = useState<GenerationState>('idle');
  const [generationMessage, setGenerationMessage] = useState(
    'Use Fixture for a GPU-free demo, or select a configured inference provider.',
  );
  const [analysis, setAnalysis] = useState<MeshAnalysis | null>(null);
  const [exportResult, setExportResult] = useState<ExportResponse | null>(null);
  const [exportMessage, setExportMessage] = useState('');

  const openAsset = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setAssetId(assetInput.trim());
    setAnalysis(null);
    setExportResult(null);
  };

  const generate = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!image) return;

    setGenerationState('generating');
    setGenerationMessage('Preprocessing image, generating model and validating geometry…');
    setAnalysis(null);
    setExportResult(null);
    setExportMessage('');
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
      setAnalysis(payload.analysis);
      setGenerationState('ready');
      setGenerationMessage(`Generated with ${payload.provider} · ${payload.model}`);
    } catch (error) {
      setGenerationState('error');
      setGenerationMessage(error instanceof Error ? error.message : 'Generation failed');
    }
  };

  const exportModel = async (format: ExportFormat) => {
    if (!assetId || analysis?.exportBlocked) return;
    setExportResult(null);
    setExportMessage(`Preparing ${format.toUpperCase()}…`);
    try {
      const response = await fetch(
        `${apiBaseUrl}/v1/exports/${encodeURIComponent(assetId)}?format=${format}`,
        { method: 'POST' },
      );
      const payload = (await response.json()) as ExportResponse | { detail?: { message?: string } };
      if (!response.ok || !('export_asset_id' in payload)) {
        const detail = 'detail' in payload ? payload.detail?.message : undefined;
        throw new Error(detail ?? `Export failed with HTTP ${response.status}`);
      }
      setExportResult(payload);
      setExportMessage(payload.warning ?? `${format.toUpperCase()} export ready.`);
    } catch (error) {
      setExportMessage(error instanceof Error ? error.message : 'Export failed');
    }
  };

  const assetUrl = assetId ? `${apiBaseUrl}/v1/assets/${encodeURIComponent(assetId)}` : undefined;
  const exportUrl = exportResult
    ? `${apiBaseUrl}/v1/assets/${encodeURIComponent(exportResult.export_asset_id)}`
    : undefined;

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
            <option value="trellis">TRELLIS · high-quality runner</option>
            <option value="spar3d">SPAR3D · backside-aware reconstruction</option>
            <option value="stable-fast-3d">Stable Fast 3D · lower VRAM / fast</option>
            <option value="hunyuan3d">Hunyuan3D · experimental adapter</option>
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

      {analysis && (
        <section className="analysis-card" data-qa-id="mesh-analysis-panel">
          <div className="analysis-score">
            <span>Geometry score</span>
            <strong data-qa-id="geometry-score">{analysis.score}</strong>
          </div>
          <div className="analysis-metrics">
            <span>{analysis.metrics.triangleCount.toLocaleString()} triangles</span>
            <span>{analysis.metrics.componentCount} component(s)</span>
            <span>{analysis.metrics.watertight ? 'Watertight' : 'Open mesh'}</span>
            <span>{analysis.metrics.manifold ? 'Manifold' : 'Non-manifold'}</span>
            {analysis.metrics.dimensionsMm && (
              <span>
                {analysis.metrics.dimensionsMm.map((value) => value.toFixed(1)).join(' × ')} mm
              </span>
            )}
          </div>
          <div className="analysis-findings" data-qa-id="geometry-findings">
            {analysis.findings.length === 0 ? (
              <p>No basic geometry findings detected.</p>
            ) : (
              analysis.findings.map((finding) => (
                <p key={finding.code} className={`finding finding--${finding.severity}`}>
                  <strong>{finding.code}</strong> · {finding.message}
                </p>
              ))
            )}
          </div>
        </section>
      )}

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

        <div className="export-bar" data-qa-id="export-controls">
          <div>
            <strong>Manufacturing export</strong>
            <p>{exportMessage || 'Choose an output format after geometry validation.'}</p>
          </div>
          <div className="export-actions">
            {(['3mf', 'stl', 'glb'] as ExportFormat[]).map((format) => (
              <button
                key={format}
                type="button"
                onClick={() => void exportModel(format)}
                disabled={!assetId || analysis?.exportBlocked === true}
                data-qa-id={`export-${format}-button`}
              >
                Export {format.toUpperCase()}
              </button>
            ))}
            {exportUrl && (
              <a href={exportUrl} data-qa-id="download-export-link">
                Download {exportResult?.format.toUpperCase()}
              </a>
            )}
          </div>
        </div>
      </section>
    </main>
  );
}
