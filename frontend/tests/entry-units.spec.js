import { test, expect } from './fixtures.js';

const units = ['pcs', 'kg', 'g', 'L', 'ml', 'bunch'];
for (const width of [360, 1440]) {
  test(`fridge and shopping entry omit pack and keep every other unit at ${width}`, async ({ page }) => {
    await page.setViewportSize({ width, height: 1000 });
    await page.goto('/');
    await page.getByRole('button', { name: 'Create an account', exact: true }).click();
    await page.getByLabel('Email address').fill(`entry-units-${crypto.randomUUID()}@example.test`);
    await page.getByLabel('Password', { exact: true }).fill(crypto.randomUUID()+crypto.randomUUID());
    await page.getByRole('button', { name: 'Create account', exact: true }).click();
    await expect(page.getByLabel('Add an ingredient', { exact: true })).toBeVisible();
    await expect(page.getByLabel('Unit', { exact: true }).locator('option')).toHaveText(units);
    await page.getByLabel('Add an ingredient', { exact: true }).fill('unit-option-milk');
    await page.getByLabel('Quantity', { exact: true }).fill('1.5');
    await page.getByLabel('Unit', { exact: true }).selectOption('L');
    const stored = page.waitForResponse(r => r.url().endsWith('/api/inventory') && r.request().method()==='POST');
    await page.getByRole('button', { name: 'Add ingredient', exact: true }).click();
    expect(await (await stored).json()).toMatchObject({name:'unit-option-milk',quantity:1.5,unit:'L'});
    await expect(page.getByRole('button', { name: 'Remove unit-option-milk', exact: true })).toBeVisible();

    const session=await page.evaluate(() => JSON.parse(sessionStorage.getItem('fridgely.session')));
    const headers={Authorization:`Bearer ${session.token}`};
    const legacy=await (await page.request.post('/api/inventory', {headers,data:{name:'legacy-unit-stock',quantity:2,unit:'pack'}})).json();
    await page.reload();
    await page.getByRole('button', {name:'Edit quantity for legacy-unit-stock',exact:true}).click();
    await expect(page.getByLabel('Unit', {exact:true})).toHaveValue('pack');
    await expect(page.getByLabel('Unit', {exact:true}).locator('option[value="pack"]')).toBeDisabled();
    await page.getByLabel('Quantity', {exact:true}).fill('3');
    const edited=page.waitForResponse(r => r.url().endsWith(`/api/inventory/${legacy.id}`) && r.request().method()==='PATCH');
    await page.getByRole('button', {name:'Save quantity',exact:true}).click();
    expect(await (await edited).json()).toMatchObject({quantity:3,unit:'pack'});
    await expect(page.getByLabel('Unit', {exact:true}).locator('option')).toHaveText(units);

    await page.getByRole('link', { name: 'Shopping list', exact: true }).click();
    await expect(page.getByLabel('Unit', { exact: true }).locator('option')).toHaveText(units);
    await page.getByLabel('Add a shopping item').fill('unit-option-rice');
    await page.getByLabel('Quantity (optional)').fill('0.75');
    await page.getByLabel('Unit', { exact: true }).selectOption('kg');
    const shopping = page.waitForResponse(r => r.url().endsWith('/api/shopping-items') && r.request().method()==='POST');
    await page.getByRole('button', { name: 'Add item', exact: true }).click();
    expect(await (await shopping).json()).toMatchObject({name:'unit-option-rice',quantity:0.75,unit:'kg'});
    expect(await page.evaluate(() => document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  });
}
