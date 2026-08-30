import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { App } from './App';

describe('App', () => {
  it('renders Image to 3D generation and viewer controls with stable QA hooks', () => {
    render(<App />);

    expect(screen.getByRole('heading', { name: /3D Modeling System/i })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: /Generate a model/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/Source image/i)).toHaveAttribute('data-qa-id', 'source-image-input');
    expect(screen.getByLabelText(/Provider/i)).toHaveAttribute('data-qa-id', 'provider-select');
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
  });
});
