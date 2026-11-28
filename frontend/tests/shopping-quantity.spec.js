import { test, expect } from './fixtures.js';
import AxeBuilder from '@axe-core/playwright';

async function setup(page) {
  const credentials = { email: `purchase-${crypto.randomUUID()}@example.test`, password: 'Shopping-browser-fixture-123!' };
  expect((await page.request.post('/api/accounts', { data: credentials })).status()).toBe(201);
  const { token } = await (await page.request.post('/api/sessions', { data: credentials })).json();
  const headers = { Authorization: `Bearer ${token}` };
  await page.goto('/');
  await page.evaluate(session => sessionStorage.setItem('fridgely.session', JSON.stringify(session)), { token, email: credentials.email });
  await page.goto('/#/shopping');
  await page.reload();
  return { headers, stock: async () => (await page.request.get('/api/inventory', { headers })).json() };
}

async function add(page, name, quantity = '', unit = 'pcs') {
  await page.getByLabel('Add a shopping item', { exact: true }).fill(name);
  await page.getByLabel('Quantity (optional)', { exact: true }).fill(quantity);
  await page.locator('#shopping-unit').selectOption(unit);
  await page.getByRole('button', { name: 'Add item', exact: true }).click();
}

for (const width of [360, 1440]) test(`shopping amounts and actual purchased quantities persist at ${width}px`, async ({ page }) => {
  await page.setViewportSize({ width, height: 900 });
  const kitchen = await setup(page);
  expect((await page.request.post('/api/inventory', { headers: kitchen.headers, data: { name: 'milk', quantity: .2, unit: 'L' } })).status()).toBe(201);
  await add(page, 'milk', '500', 'ml');
  const row = page.getByRole('listitem').filter({ has: page.getByRole('button', { name: 'Remove milk', exact: true }) });
  await expect(row).toContainText('500 ml');
  await page.reload();
  await expect(row).toContainText('500 ml');
  await page.getByRole('button', { name: 'Bought — add to fridge: milk', exact: true }).click();
  await expect(page.getByLabel('Bought quantity', { exact: true })).toHaveValue('500');
  await page.getByRole('button', { name: 'Cancel purchase', exact: true }).click();
  expect((await kitchen.stock())[0].quantity).toBe(.2);
  await page.getByRole('button', { name: 'Bought — add to fridge: milk', exact: true }).click();
  await page.getByLabel('Bought quantity', { exact: true }).fill('200');
  expect((await new AxeBuilder({ page }).include('main').analyze()).violations).toEqual([]);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.getByRole('button', { name: 'Confirm purchase and add to fridge', exact: true }).click();
  await expect(page.getByText('Purchase recorded. Your fridge has been updated.', { exact: true })).toBeVisible();
  await expect(row).toHaveCount(0);
  expect((await kitchen.stock())[0].quantity).toBe(.4);
  await page.reload();
  await expect(page.getByText('All set for now', { exact: true })).toBeVisible();
  await page.getByRole('link', { name: 'My fridge', exact: true }).click();
  await expect(page.getByRole('listitem').filter({ has: page.getByRole('button', { name: 'Remove milk', exact: true }) })).toContainText('0.4 L');
});

test('name-only shopping, validation, replacement and ordinary removal stay safe', async ({ page }) => {
  const kitchen = await setup(page);
  await add(page, 'egg', '1.5');
  await expect(page.locator('#shopping-quantity-error')).toContainText('whole numbers');
  await page.getByLabel('Quantity (optional)', { exact: true }).fill('2');
  await page.getByRole('button', { name: 'Add item', exact: true }).click();
  await expect(page.getByRole('listitem')).toContainText('2 pcs');
  await add(page, 'EGG', '3');
  await expect(page.getByRole('listitem')).toHaveCount(1);
  await expect(page.getByRole('listitem')).toContainText('3 pcs');
  await add(page, 'egg');
  await expect(page.getByRole('listitem')).toContainText('3 pcs');
  await page.getByRole('button', { name: 'Remove egg', exact: true }).click();
  expect(await kitchen.stock()).toEqual([]);
  await add(page, 'rice');
  await page.getByRole('button', { name: 'Bought — add to fridge: rice', exact: true }).click();
  await page.getByRole('button', { name: 'Confirm purchase and add to fridge', exact: true }).click();
  await expect(page.getByText('Enter a positive quantity up to 1,000,000; use whole numbers for count units.', { exact: true })).toBeVisible();
  expect(await kitchen.stock()).toEqual([]);
  await page.getByLabel('Bought quantity', { exact: true }).fill('500');
  await page.locator('select[id^="purchase-"]').selectOption('g');
  await page.getByRole('button', { name: 'Confirm purchase and add to fridge', exact: true }).click();
  await expect(page.getByText('All set for now', { exact: true })).toBeVisible();
  expect((await kitchen.stock())[0]).toMatchObject({ name: 'rice', quantity: 500, unit: 'g' });
});

for (const recovery of ['retry', 'reload', 'changed amount']) test(`lost purchase response with ${recovery} never refills twice`, async ({ page }) => {
  const kitchen = await setup(page);
  await add(page, 'egg', '2');
  await page.getByRole('button', { name: 'Bought — add to fridge: egg', exact: true }).click();
  let dropped = false;
  await page.route('**/api/shopping-items/*/purchase', async route => {
    if (dropped) { await route.continue(); return; }
    dropped = true;
    const response = await route.fetch();
    expect(response.status()).toBe(200);
    await route.abort('failed');
  });
  await page.getByRole('button', { name: 'Confirm purchase and add to fridge', exact: true }).click();
  await expect(page.getByRole('alert')).toBeVisible();
  expect((await kitchen.stock())[0].quantity).toBe(2);
  if (recovery === 'reload') {
    await page.reload();
  } else {
    if (recovery === 'changed amount') await page.getByLabel('Bought quantity', { exact: true }).fill('3');
    await page.getByRole('button', { name: 'Confirm purchase and add to fridge', exact: true }).click();
  }
  await expect(page.getByText('All set for now', { exact: true })).toBeVisible();
  await page.reload();
  expect((await kitchen.stock())[0].quantity).toBe(2);
});

test('favorite adds measured deficits and bought amounts refill exactly enough stock', async ({ page }) => {
  const kitchen = await setup(page);
  for (const item of [{ name: 'banana', quantity: 1, unit: 'pcs' }, { name: 'milk', quantity: .1, unit: 'L' }, { name: 'sugar', quantity: .01, unit: 'kg' }]) {
    expect((await page.request.post('/api/inventory', { headers: kitchen.headers, data: item })).status()).toBe(201);
  }
  const before = await kitchen.stock();
  await page.getByRole('link', { name: 'Find recipes', exact: true }).click();
  await page.reload(); // Refresh inventory seeded through the isolated API.
  await page.getByRole('button', { name: 'Generate recipes', exact: true }).click();
  await page.getByRole('button', { name: 'View recipe', exact: true }).first().click();
  await page.getByRole('button', { name: 'Save favorite', exact: true }).click();
  await page.getByRole('button', { name: 'Close recipe', exact: true }).click();
  await page.getByRole('link', { name: 'Favorites', exact: true }).click();
  await page.getByRole('button', { name: 'View recipe', exact: true }).first().click();
  await page.getByRole('button', { name: 'Add missing ingredients', exact: true }).click();
  await expect(page.getByText('Missing ingredients added to shopping.', { exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Close recipe', exact: true }).click();
  await page.getByRole('link', { name: 'Shopping list', exact: true }).click();
  await page.reload();
  expect(await kitchen.stock()).toEqual(before);
  for (const [name, quantity, unit] of [['banana', '1', 'pcs'], ['milk', '100', 'ml'], ['sugar', '10', 'g']]) {
    const row = page.getByRole('listitem').filter({ has: page.getByRole('button', { name: `Remove ${name}`, exact: true }) });
    await expect(row).toContainText(`${quantity} ${unit}`);
    await page.getByRole('button', { name: `Bought — add to fridge: ${name}`, exact: true }).click();
    await expect(page.getByLabel('Bought quantity', { exact: true })).toHaveValue(quantity);
    await page.getByRole('button', { name: 'Confirm purchase and add to fridge', exact: true }).click();
    await expect(row).toHaveCount(0);
  }
  const stock = await kitchen.stock();
  expect(stock.find(i => i.name === 'banana').quantity).toBe(2);
  expect(stock.find(i => i.name === 'milk').quantity).toBe(.2);
  expect(stock.find(i => i.name === 'sugar').quantity).toBe(.02);
  await page.getByRole('link', { name: 'Favorites', exact: true }).click();
  await page.getByRole('button', { name: 'View recipe', exact: true }).first().click();
  await page.getByRole('button', { name: 'Add missing ingredients', exact: true }).click();
  await expect(page.getByText('Missing ingredients added to shopping.', { exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Close recipe', exact: true }).click();
  await page.getByRole('link', { name: 'Shopping list', exact: true }).click();
  await expect(page.getByText('All set for now', { exact: true })).toBeVisible();
});
