import { test, expect } from './fixtures.js';
import AxeBuilder from '@axe-core/playwright';

async function setup(page, items = []) {
  const credentials = { email: `planner-${crypto.randomUUID()}@example.test`, password: 'Planner-browser-fixture-123!' };
  expect((await page.request.post('/api/accounts', { data: credentials })).status()).toBe(201);
  const { token } = await (await page.request.post('/api/sessions', { data: credentials })).json();
  const headers = { Authorization: `Bearer ${token}` };
  for (const item of items) expect((await page.request.post('/api/inventory', { headers, data: item })).status()).toBe(201);
  await page.goto('/');
  await page.evaluate(session => sessionStorage.setItem('fridgely.session', JSON.stringify(session)), { token, email: credentials.email });
  await page.goto('/#/weekly-plan');
  await page.reload();
  await expect(page.getByText('Loading weekly plan…', { exact: true })).toHaveCount(0);
  await page.locator('#plan-week').fill('2026-11-23');
  return { headers, stock: async () => (await page.request.get('/api/inventory', { headers })).json() };
}
const card = (page, day, meal) => page.locator(`[aria-label="${day} ${meal}"]`);
async function requestDish(scope, dish, portions) {
  await scope.getByLabel('Portions', { exact: true }).fill(String(portions));
  await scope.getByLabel('Or request a dish', { exact: true }).fill(dish);
  await scope.getByRole('button', { name: /^Create recipe & plan/ }).click();
  await expect(scope.getByText(`Planned: ${portions} ${portions === 1 ? 'portion' : 'portions'}`, { exact: false })).toBeVisible();
}

for (const width of [360,1440]) test(`different portions, main and dessert, preparation and weekly deficits at ${width}px`, async ({ page }) => {
  await page.setViewportSize({ width, height: 950 });
  const kitchen = await setup(page, [{ name: 'rice', quantity: .1, unit: 'kg' }, { name: 'egg', quantity: 1, unit: 'pcs' }]);
  const before = await kitchen.stock();
  const main = card(page,'Monday','Main meal'), dessert = card(page,'Monday','Dessert');
  await requestDish(main,'Tomato sauce pasta',1);
  await requestDish(dessert,'Rice pudding',4);
  await main.getByText('Ingredients & preparation', { exact: true }).click();
  await expect(main).toContainText('rice · 100 g');
  await expect(main).toContainText('Prepare the sauce.');
  await dessert.getByText('Ingredients & preparation', { exact: true }).click();
  await expect(dessert).toContainText('rice · 400 g');
  await expect(dessert).toContainText('egg · 4 pcs');
  expect((await new AxeBuilder({ page }).include('main').analyze()).violations).toEqual([]);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await main.getByRole('button', { name: /^View recipe/ }).click();
  await expect(page.getByRole('dialog')).toContainText('Prepare the sauce.');
  await page.getByRole('button', { name: 'Close recipe', exact: true }).click();
  await page.reload();
  await expect(main).toContainText('Planned: 1 portion');
  await expect(dessert).toContainText('Planned: 4 portions');
  await page.getByRole('button', { name: 'Generate weekly shopping list', exact: true }).click();
  await expect(page.getByText('Weekly shopping list updated.', { exact: true })).toBeVisible();
  const shopping = await (await page.request.get('/api/shopping-items', { headers: kitchen.headers })).json();
  expect(shopping.map(({ name,quantity,unit }) => ({ name,quantity,unit }))).toEqual([
    { name:'rice',quantity:400,unit:'g' }, { name:'egg',quantity:4,unit:'pcs' }]);
  await page.getByRole('button', { name: 'Generate weekly shopping list', exact: true }).click();
  await expect(page.getByText('Weekly shopping list updated.', { exact: true })).toBeVisible();
  expect(await (await page.request.get('/api/shopping-items', { headers: kitchen.headers })).json()).toEqual(shopping);
  expect(await kitchen.stock()).toEqual(before);
  await page.getByRole('link', { name:'View shopping list', exact:true }).click();
  await expect(page.getByRole('listitem').filter({ has: page.getByRole('button', { name:'Remove rice', exact:true }) })).toContainText('400 g');
});

test('saved dishes scale per day without calling AI and clearing preserves the catalog', async ({ page }) => {
  await setup(page);
  const main = card(page,'Monday','Main meal');
  await requestDish(main,'Pasta',4);
  const rid = await main.getByLabel('Saved recipe', { exact:true }).inputValue();
  let aiCalls=0;
  page.on('request',request => { if(request.url().endsWith('/generate')) aiCalls++; });
  await main.getByLabel('Portions', { exact:true }).fill('1');
  await main.getByRole('button', { name:'Update portions', exact:true }).click();
  await expect(main).toContainText('Planned: 1 portion');
  await main.getByText('Ingredients & preparation', { exact:true }).click();
  await expect(main).toContainText('rice · 100 g');
  const tuesday=card(page,'Tuesday','Lunch');
  await tuesday.getByLabel('Portions', { exact:true }).fill('4');
  await tuesday.getByLabel('Saved recipe', { exact:true }).selectOption(rid);
  await expect(tuesday).toContainText('Planned: 4 portions');
  await main.getByLabel('Saved recipe', { exact:true }).selectOption('');
  await expect(main.getByText('Ingredients & preparation', { exact:true })).toHaveCount(0);
  await main.getByLabel('Saved recipe', { exact:true }).selectOption(rid);
  await expect(main).toContainText('Planned: 1 portion');
  expect(aiCalls).toBe(0);
  await page.getByRole('button', { name:'Next week', exact:true }).click();
  await expect(page.locator('#plan-week')).toHaveValue('2026-11-30');
  await expect(page.getByText('0 planned meals', { exact:true })).toBeVisible();
  await page.getByRole('button', { name:'Previous week', exact:true }).click();
  await expect(tuesday).toContainText('Planned: 4 portions');
});

test('invalid portions and unavailable requested dish leave existing meals intact', async ({ page }) => {
  await setup(page);
  const main = card(page,'Monday','Main meal');
  await main.getByLabel('Portions', { exact:true }).fill('0');
  await main.getByLabel('Or request a dish', { exact:true }).fill('Pasta');
  await main.getByRole('button', { name:/^Create recipe & plan/ }).click();
  await expect(main.getByRole('alert')).toContainText('between 1 and 20');
  await requestDish(main,'Pasta',1);
  await main.getByLabel('Or request a dish', { exact:true }).fill('provider-failure');
  await main.getByRole('button', { name:/^Create recipe & plan/ }).click();
  await expect(page.getByRole('alert')).toContainText('temporarily unavailable');
  await expect(main).toContainText('Planned: 1 portion');
  await expect(main.getByLabel('Or request a dish', { exact:true })).toHaveValue('provider-failure');
  await page.route('**/api/weekly-plan/0/dinner', route => route.fulfill({ status:503, json:{ error:'Plan could not be saved.' } }));
  await main.getByLabel('Portions', { exact:true }).fill('3');
  await main.getByRole('button', { name:'Update portions', exact:true }).click();
  await expect(page.getByRole('alert')).toContainText('Plan could not be saved');
  await expect(main).toContainText('Planned: 1 portion');
});

test('weekly load failure retries and stale generation refreshes the saved plan', async ({ page }) => {
  await page.route('**/api/weekly-plan?*', route => route.fulfill({ status:503,json:{ error:'Weekly storage unavailable' } }));
  await setup(page);
  await expect(page.getByRole('alert')).toContainText('Weekly storage unavailable');
  await page.unroute('**/api/weekly-plan?*');
  await page.getByRole('button', { name:'Retry weekly plan',exact:true }).click();
  const main = card(page,'Monday','Main meal');
  await requestDish(main,'Pasta',2);
  await page.route('**/api/weekly-plan/*/*/generate', route => route.fulfill({ status:409,json:{ error:'Meal changed. Refresh the week.' } }));
  await main.getByLabel('Or request a dish', { exact:true }).fill('New pasta');
  await main.getByRole('button', { name:/^Create recipe & plan/ }).click();
  await expect(page.getByRole('alert')).toContainText('Meal changed');
  await expect(main).toContainText('Planned: 2 portions');
});

test('unknown measures are flagged and expired planner sessions sign out', async ({ page }) => {
  const kitchen=await setup(page,[{name:'tomato',quantity:2,unit:'pcs'}]);
  const recipes=await (await page.request.post('/api/recipes/generate',{headers:kitchen.headers,json:{}})).json();
  await page.reload();
  const main=card(page,'Monday','Main meal');
  await main.getByLabel('Saved recipe',{exact:true}).selectOption(recipes[1].id);
  await main.getByText('Ingredients & preparation',{exact:true}).click();
  await expect(main).toContainText('Amount needs review');
  await page.getByRole('button',{name:'Generate weekly shopping list',exact:true}).click();
  await expect(page.getByRole('status').filter({hasText:'Amounts need review'})).toContainText('olive oil');
  await page.route('**/api/weekly-plan?*',route=>route.fulfill({status:401,json:{error:'Session expired'}}));
  await page.getByRole('button',{name:'Next week',exact:true}).click();
  await expect(page.getByRole('button',{name:'Sign in',exact:true})).toBeVisible();
});
