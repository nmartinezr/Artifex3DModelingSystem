import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { App } from './App';

describe('App', () => {
  it('renders the ARTIFEX development-ready shell', () => {
    render(<App />);

    expect(screen.getByRole('heading', { name: /ARTIFEX 3D Modeling System/i })).toBeInTheDocument();
    expect(screen.getByText(/Technical foundation ready/i)).toHaveAttribute(
      'data-qa-id',
      'development-readiness-status',
    );
  });
});
