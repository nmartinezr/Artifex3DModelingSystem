import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { App } from './App';

describe('App', () => {
  it('renders the generated model workspace with stable QA hooks', () => {
    render(<App />);

    expect(screen.getByRole('heading', { name: /3D Modeling System/i })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: /Generated model/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/Asset ID/i)).toHaveAttribute('data-qa-id', 'asset-id-input');
    expect(screen.getByRole('button', { name: /Open model/i })).toHaveAttribute(
      'data-qa-id',
      'open-asset-button',
    );
    expect(screen.getByText(/Enter an ARTIFEX asset ID/i)).toHaveAttribute(
      'data-qa-id',
      'generated-model-viewer-status',
    );
  });
});
