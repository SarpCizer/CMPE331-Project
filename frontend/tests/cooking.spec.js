import { test, expect } from './fixtures.js';
import AxeBuilder from '@axe-core/playwright';

async function setup(page, stock) {
  const credentials = { email: `cook-${crypto.randomUUID()}@example.test`, password: 'Cooking-browser-fixture-123!' };
  expect((await page.request.post('/api/accounts', { data: credentials })).status()).toBe(201);
  const { token } = await (await page.request.post('/api/sessions', { data: credentials })).json();
  const headers = { Authorization: `Bearer ${token}` };
  for (const item of stock) expect((await page.request.post('/api/inventory', { headers, data: item })).status()).toBe(201);
  await page.goto('/');
  await page.evaluate(session => sessionStorage.setItem('fridgely.session', JSON.stringify(session)), { token, email: credentials.email });
  await page.goto('/#/recipes');
  await page.reload();
  await page.getByRole('button', { name: 'Generate recipes', exact: true }).click();
  await page.getByRole('button', { name: 'View recipe', exact: true }).first().click();
  await expect(page.getByRole('dialog')).toBeVisible();
  return { headers, stock: async () => (await page.request.get('/api/inventory', { headers })).json() };
}

test('confirm cooking, red depleted stock, one-click shopping and refill survive reload', async ({ page }) => {
  await page.setViewportSize({ width: 360, height: 800 });
  const kitchen = await setup(page, [{ name: 'rice', quantity: .15, unit: 'kg' }]);
  const before = await kitchen.stock();
  await page.getByRole('button', { name: 'I cooked this', exact: true }).click();
  await expect(page.getByLabel('Used rice (kg)', { exact: true })).toHaveValue('0.15');
  await expect(page.getByText('Available: 0.15 kg · Remaining: 0 kg', { exact: true })).toBeVisible();
  await expect(page.getByText('Not in stock — no deduction.')).toHaveCount(2);
  expect((await new AxeBuilder({ page }).include('dialog').analyze()).violations).toEqual([]);
  await page.getByRole('button', { name: 'Cancel cooking', exact: true }).click();
  expect(await kitchen.stock()).toEqual(before);
  await page.getByRole('button', { name: 'I cooked this', exact: true }).click();
  await page.getByLabel('Used rice (kg)', { exact: true }).fill('.2');
  await page.getByRole('button', { name: 'Confirm cooking and update fridge', exact: true }).click();
  await expect(page.getByRole('alert')).toContainText('Review each amount');
  expect(await kitchen.stock()).toEqual(before);
  await page.getByLabel('Used rice (kg)', { exact: true }).fill('.15');
  await page.getByRole('button', { name: 'Confirm cooking and update fridge', exact: true }).click();
  await expect(page.getByText('Cooking recorded. Your fridge has been updated.', { exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Close recipe', exact: true }).click();
  await page.getByRole('link', { name: 'My fridge', exact: true }).click();
  await page.reload();
  const row = page.getByRole('listitem').filter({ has: page.getByRole('button', { name: 'Remove rice', exact: true }) });
  await expect(row).toContainText('0 kg');
  await expect(row).toContainText('Out of stock');
  await expect(row).toHaveClass(/text-red-800/);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.getByRole('button', { name: 'Add rice to shopping list', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Add rice to shopping list', exact: true })).toBeDisabled();
  await page.getByRole('link', { name: 'Shopping list', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Remove rice', exact: true })).toHaveCount(1);
  await page.getByRole('link', { name: 'Find recipes', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Generate recipes', exact: true })).toBeDisabled();
  await page.getByRole('link', { name: 'My fridge', exact: true }).click();
  await page.getByRole('button', { name: 'Edit quantity for rice', exact: true }).click();
  await page.getByLabel('Quantity', { exact: true }).fill('.5');
  await page.getByRole('button', { name: 'Save quantity', exact: true }).click();
  await expect(row).not.toContainText('Out of stock');
});

test('ambiguous stock units require reviewed input, duplicates can be selected and zero skips', async ({ page }) => {
  const kitchen = await setup(page, [
    { name: 'rice', quantity: 2, unit: 'pack' },
    { name: 'rice', quantity: .5, unit: 'kg' },
    { name: 'tomato', quantity: 3, unit: 'pcs' },
  ]);
  await page.getByRole('button', { name: 'I cooked this', exact: true }).click();
  await expect(page.getByLabel('Used rice (pack)', { exact: true })).toHaveValue('');
  await page.getByLabel('Used rice (pack)', { exact: true }).fill('1.5');
  await page.getByRole('button', { name: 'Confirm cooking and update fridge', exact: true }).click();
  await expect(page.getByRole('alert')).toContainText('Review each amount');
  const stock = await kitchen.stock();
  await page.getByLabel('Fridge entry for rice', { exact: true }).selectOption(stock.find(item => item.unit === 'kg').id);
  await expect(page.getByLabel('Used rice (kg)', { exact: true })).toHaveValue('0.15');
  await page.getByLabel('Used rice (kg)', { exact: true }).fill('0');
  await page.getByLabel('Used tomato (pcs)', { exact: true }).fill('0');
  await page.getByRole('button', { name: 'Confirm cooking and update fridge', exact: true }).click();
  await expect(page.getByRole('alert')).toContainText('at least one stocked ingredient');
  await page.getByLabel('Used tomato (pcs)', { exact: true }).fill('2');
  await page.getByRole('button', { name: 'Confirm cooking and update fridge', exact: true }).click();
  await expect(page.getByText('Cooking recorded. Your fridge has been updated.', { exact: true })).toBeVisible();
  expect((await kitchen.stock()).find(item => item.name === 'tomato').quantity).toBe(1);
});

test('lost response retries the same cooking confirmation without double deduction', async ({ page }) => {
  const kitchen = await setup(page, [{ name: 'rice', quantity: .5, unit: 'kg' }]);
  const submitted = [];
  await page.route('**/api/recipes/*/cook', async route => {
    submitted.push(route.request().postDataJSON());
    const response = await route.fetch();
    if (submitted.length === 1) await route.abort();
    else await route.fulfill({ response });
  });
  await page.getByRole('button', { name: 'I cooked this', exact: true }).click();
  await page.getByRole('button', { name: 'Confirm cooking and update fridge', exact: true }).click();
  await expect(page.getByRole('alert')).toContainText('could not reach');
  await page.getByRole('button', { name: 'Confirm cooking and update fridge', exact: true }).click();
  await expect(page.getByText('Cooking recorded. Your fridge has been updated.', { exact: true })).toBeVisible();
  expect(submitted).toHaveLength(2);
  expect(submitted[0]).toEqual(submitted[1]);
  expect((await kitchen.stock())[0].quantity).toBe(.35);
});

test('concurrent stock changes refresh available quantities with a cooking-specific error', async ({ page }) => {
  const kitchen = await setup(page, [{ name: 'rice', quantity: .5, unit: 'kg' }]);
  await page.getByRole('button', { name: 'I cooked this', exact: true }).click();
  const [item] = await kitchen.stock();
  expect((await page.request.patch(`/api/inventory/${item.id}`, { headers: kitchen.headers,
    data: { quantity: .1, unit: 'kg' } })).status()).toBe(200);
  await page.getByRole('button', { name: 'Confirm cooking and update fridge', exact: true }).click();
  await expect(page.getByRole('alert')).toContainText('Stock changed or is insufficient');
  await expect(page.getByText('Available: 0.1 kg', { exact: true })).toBeVisible();
  await page.getByLabel('Used rice (kg)', { exact: true }).fill('.1');
  await page.getByRole('button', { name: 'Confirm cooking and update fridge', exact: true }).click();
  await expect(page.getByText('Cooking recorded. Your fridge has been updated.', { exact: true })).toBeVisible();
});

test('200 ml recipe usage converts to 0.2 L and legacy unknown stock is never guessed', async ({ page }) => {
  const kitchen = await setup(page, [{ name: 'milk', quantity: 1, unit: 'L' }, { name: 'milk' }]);
  await expect(page.getByRole('dialog')).toContainText('milk · 200 ml');
  await page.getByRole('button', { name: 'I cooked this', exact: true }).click();
  await expect(page.getByLabel('Used milk (L)', { exact: true })).toHaveValue('0.2');
  const stock = await kitchen.stock();
  const selector = page.getByLabel('Fridge entry for milk', { exact: true });
  await selector.selectOption(stock.find(item => item.quantity == null).id);
  await expect(page.getByText('Stock amount unknown. Set its quantity in My Fridge before deducting.', { exact: true })).toBeVisible();
  await selector.selectOption(stock.find(item => item.quantity === 1).id);
  await page.getByRole('button', { name: 'Confirm cooking and update fridge', exact: true }).click();
  await expect(page.getByText('Cooking recorded. Your fridge has been updated.', { exact: true })).toBeVisible();
  const after = await kitchen.stock();
  expect(after.find(item => item.unit === 'L').quantity).toBe(.8);
  expect(after.find(item => item.quantity == null).quantity).toBeNull();
});

test('reload after a committed lost response replays the entire original confirmation including depleted stock', async ({ page }) => {
  const kitchen = await setup(page, [{ name: 'rice', quantity: .15, unit: 'kg' },
    { name: 'tomato', quantity: 5, unit: 'pcs' }]);
  const submitted = [];
  await page.route('**/api/recipes/*/cook', async route => {
    submitted.push(route.request().postDataJSON());
    const response = await route.fetch();
    if (submitted.length === 1) await route.abort();
    else await route.fulfill({ response });
  });
  await page.getByRole('button', { name: 'I cooked this', exact: true }).click();
  await page.getByRole('button', { name: 'Confirm cooking and update fridge', exact: true }).click();
  await expect(page.getByRole('alert')).toContainText('could not reach');
  let stock = await kitchen.stock();
  expect(stock.find(item => item.name === 'rice').quantity).toBe(0);
  expect(stock.find(item => item.name === 'tomato').quantity).toBe(3);
  await page.reload();
  await page.getByRole('link', { name: 'Recently viewed', exact: true }).click();
  await page.getByRole('button', { name: 'View recipe', exact: true }).first().click();
  await page.getByRole('button', { name: 'I cooked this', exact: true }).click();
  await page.getByRole('button', { name: /^(Confirm cooking and update fridge|Retry previous confirmation)$/ }).click();
  await expect(page.getByText('Cooking recorded. Your fridge has been updated.', { exact: true })).toBeVisible();
  expect(submitted).toHaveLength(2);
  expect(submitted[1]).toEqual(submitted[0]);
  stock = await kitchen.stock();
  expect(stock.find(item => item.name === 'rice').quantity).toBe(0);
  expect(stock.find(item => item.name === 'tomato').quantity).toBe(3);
});
