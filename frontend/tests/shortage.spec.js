import { test, expect } from './fixtures.js';

test('favorite recipe adds insufficient and absent ingredients, persists and permits removal', async ({ page }) => {
  const credentials = { email: `shortage-${crypto.randomUUID()}@example.test`, password: 'Shopping-browser-fixture-123!' };
  expect((await page.request.post('/api/accounts', { data: credentials })).status()).toBe(201);
  const { token } = await (await page.request.post('/api/sessions', { data: credentials })).json();
  const headers = { Authorization: `Bearer ${token}` };
  for (const item of [{ name: 'banana', quantity: 1, unit: 'pcs' }, { name: 'milk', quantity: .2, unit: 'L' }]) {
    expect((await page.request.post('/api/inventory', { headers, data: item })).status()).toBe(201);
  }
  const stock = async () => (await page.request.get('/api/inventory', { headers })).json();
  const before = await stock();
  await page.goto('/');
  await page.evaluate(session => sessionStorage.setItem('fridgely.session', JSON.stringify(session)), { token, email: credentials.email });
  await page.goto('/#/recipes');
  await page.reload();
  await page.getByRole('button', { name: 'Generate recipes', exact: true }).click();
  await page.getByRole('button', { name: 'View recipe', exact: true }).first().click();
  await page.getByRole('button', { name: 'Save favorite', exact: true }).click();
  await page.getByRole('button', { name: 'Close recipe', exact: true }).click();
  await page.getByRole('link', { name: 'Favorites', exact: true }).click();
  await page.reload();
  await page.getByRole('button', { name: 'View recipe', exact: true }).first().click();
  await page.getByRole('button', { name: 'Add missing ingredients', exact: true }).click();
  await expect(page.getByText('Missing ingredients added to shopping.', { exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Add missing ingredients', exact: true }).click();
  await page.getByRole('button', { name: 'Close recipe', exact: true }).click();
  await page.getByRole('link', { name: 'Shopping list', exact: true }).click();
  await page.reload();
  await expect(page.getByRole('button', { name: 'Remove banana', exact: true })).toHaveCount(1);
  await expect(page.getByRole('button', { name: 'Remove sugar', exact: true })).toHaveCount(1);
  await expect(page.getByRole('button', { name: 'Remove milk', exact: true })).toHaveCount(0);
  expect(await stock()).toEqual(before);
  await page.getByRole('button', { name: 'Remove banana', exact: true }).click();
  await page.getByRole('button', { name: 'Remove sugar', exact: true }).click();
  await page.reload();
  await expect(page.getByText('All set for now', { exact: true })).toBeVisible();
  expect(await stock()).toEqual(before);
});
