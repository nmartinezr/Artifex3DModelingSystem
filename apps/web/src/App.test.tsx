import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { App } from './App';

describe('App', () => {
  it('renders Image to 3D generation, style, provider, viewer and export controls with stable QA hooks', () => {
    render(<App />);

    expect(screen.getByRole('heading', { name: /3D Modeling System/i })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: /Generate a model/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/Source image/i)).toHaveAttribute('data-qa-id', 'source-image-input');

    const style = screen.getByLabelText(/^Style$/i) as HTMLSelectElement;
    expect(style).toHaveAttribute('data-qa-id', 'style-select');
    expect(style.value).toBe('none');
    fireEvent.change(style, { target: { value: 'collectible-vinyl' } });
    expect(style.value).toBe('collectible-vinyl');
    expect(screen.getByRole('option', { name: /Chibi/i })).toBeInTheDocument();
    expect(screen.getByRole('option', { name: /Realistic Bust/i })).toBeInTheDocument();

    const provider = screen.getByLabelText(/3D provider/i) as HTMLSelectElement;
    expect(provider).toHaveAttribute('data-qa-id', 'provider-select');
    expect(provider.value).toBe('fixture');
    fireEvent.change(provider, { target: { value: 'spar3d' } });
    expect(provider.value).toBe('spar3d');
    expect(screen.getByRole('option', { name: /Stable Fast 3D/i })).toBeInTheDocument();
    expect(screen.getByRole('option', { name: /Hunyuan3D/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Generate 3D model/i })).toHaveAttribute(
      'data-qa-id',
      'generate-model-button',
    );
    expect(screen.getByRole('heading', { name: /Generated model/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/Asset ID/i)).toHaveAttribute('data-qa-id', 'asset-id-input');
    expect(screen.getByText(/Enter an ARTIFEX asset ID/i)).toHaveAttribute(
      'data-qa-id',
      'generated-model-viewer-status',
    );

    for (const format of ['3MF', 'STL', 'GLB']) {
      const button = screen.getByRole('button', { name: new RegExp(`Export ${format}`, 'i') });
      expect(button).toBeDisabled();
    }
  });
});
