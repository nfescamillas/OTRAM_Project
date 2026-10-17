import { expect, test } from '@playwright/test';

test('an administrator can sign in and register an asset end to end', async ({ page }) => {
  const password = process.env.OTARM_E2E_PASSWORD ?? process.env.OTARM_DEMO_PASSWORD;
  if (!password) {
    throw new Error('OTARM_E2E_PASSWORD or OTARM_DEMO_PASSWORD is required for end-to-end tests.');
  }

  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'Sign in to OTARM' })).toBeVisible();

  await page.getByLabel('Password').fill(password);
  await page.getByRole('button', { name: 'Sign in' }).click();

  await expect(page.getByRole('heading', { name: 'Operational risk, made legible.' })).toBeVisible();
  await expect(page.getByText('3 sites in scope')).toBeVisible();
  await expect(page.getByText('API CONNECTED')).toBeVisible();

  await page.getByRole('navigation', { name: 'Primary navigation' })
    .getByRole('button', { name: 'Asset inventory' })
    .click();
  await expect(page.getByRole('heading', { name: 'Asset inventory' })).toBeVisible();
  await expect(page.getByText(/\d+ assets shown/)).toBeVisible();

  await page.getByRole('button', { name: 'Register asset' }).click();
  const dialog = page.getByRole('dialog', { name: 'Register an OT asset' });
  const tag = `E2E-PLC-${Date.now()}`;
  await dialog.getByLabel('Asset tag').fill(tag);
  await dialog.getByLabel('Display name').fill('Pipeline Test PLC');
  await dialog.getByLabel('Site').selectOption('site-north');
  await dialog.getByLabel('Area').fill('CI Test Cell');
  await dialog.getByLabel('Vendor').fill('Fictional Automation');
  await dialog.getByLabel('Model').fill('CI-100');
  await dialog.getByLabel('Owner').fill('Pipeline Operator');
  await dialog.getByRole('button', { name: 'Register asset' }).click();

  await expect(page.getByText(`${tag} registered.`)).toBeVisible();
  await page.getByLabel('Search assets').fill(tag);
  await expect(page.getByText(tag, { exact: true })).toBeVisible();
  await expect(page.getByText('Pipeline Test PLC', { exact: true })).toBeVisible();
});
