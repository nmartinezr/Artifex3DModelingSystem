import { expect, test } from '@playwright/test';

const png = Buffer.from(
  'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Wl2ZQAAAABJRU5ErkJggg==',
  'base64',
);

test('upload → generate → viewer → validation → 3MF export', async ({ page, request }) => {
  await page.goto('/');

  await page.locator('[data-qa-id="source-image-input"]').setInputFiles({
    name: 'fixture.png',
    mimeType: 'image/png',
    buffer: png,
  });
  await page.locator('[data-qa-id="provider-select"]').selectOption('fixture');
  await page.locator('[data-qa-id="generate-model-button"]').click();

  await expect(page.locator('[data-qa-id="generation-status"]')).toContainText('Generated with fixture');
  await expect(page.locator('[data-qa-id="geometry-score"]')).toHaveText('100');
  await expect(page.locator('[data-qa-id="generated-model-viewer"]')).toBeVisible();
  await expect(page.locator('[data-qa-id="generated-model-viewer-status"]')).toContainText('Generated model ready');

  await page.locator('[data-qa-id="export-3mf-button"]').click();
  const link = page.locator('[data-qa-id="download-export-link"]');
  await expect(link).toBeVisible();
  await expect(link).toContainText('Download 3MF');

  const href = await link.getAttribute('href');
  expect(href).toBeTruthy();
  const response = await request.get(href!);
  expect(response.ok()).toBeTruthy();
  expect(response.headers()['content-type']).toContain('model/3mf');
  expect((await response.body()).byteLength).toBeGreaterThan(100);
});
