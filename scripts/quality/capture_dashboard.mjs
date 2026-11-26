import { mkdir, writeFile } from 'node:fs/promises';
import { chromium } from '../../frontend/node_modules/@playwright/test/index.mjs';

const base = process.env.SONAR_HOST_URL || 'http://127.0.0.1:9000';
if (!['127.0.0.1', 'localhost'].includes(new URL(base).hostname)) throw new Error('Only the isolated CI Sonar server is allowed');
const output = 'test-results/sonarqube';
await mkdir(output, { recursive: true });
const browser = await chromium.launch({ headless: true });
try {
  const page = await browser.newPage({ viewport: { width: 1280, height: 1000 }, deviceScaleFactor: 2 });
  await page.goto(base + '/dashboard?id=fridgely');
  await page.waitForLoadState('networkidle');
  if (await page.locator('input[type="password"]').count()) {
    if (!process.env.SONAR_ADMIN_PASSWORD) throw new Error('Ephemeral CI login is missing');
    await page.getByRole('textbox', { name: /login|username/i }).fill('admin');
    await page.locator('input[type="password"]').fill(process.env.SONAR_ADMIN_PASSWORD);
    await page.getByRole('button', { name: /log in|sign in/i }).click();
    await page.goto(base + '/dashboard?id=fridgely');
    await page.waitForLoadState('networkidle');
  }
  await page.getByText(/Quality Gate/i).first().waitFor();
  const overall = page.getByText('Overall Code', { exact: true });
  if (await overall.count() === 1) {
    await overall.click();
    await page.waitForLoadState('networkidle');
  }
  await page.getByText(/Coverage/i).first().waitFor();
  if ((await page.locator('input[type="password"]').count()) || !page.url().includes('dashboard')) throw new Error('Dashboard was not reached');
  await page.screenshot({ path: output + '/dashboard.png', fullPage: true });
  await writeFile(output + '/dashboard-capture.json', JSON.stringify({
    revision: process.env.TESTED_REVISION, captured_at_utc: new Date().toISOString(),
    source: 'Actual ephemeral SonarQube dashboard after completed analysis',
    url: page.url(), credential_fields_present: false,
  }, null, 2));
} catch (error) {
  let message = String(error.message);
  for (const secret of [process.env.SONAR_ADMIN_PASSWORD, process.env.SONAR_TOKEN].filter(Boolean)) message = message.replaceAll(secret, '[REDACTED]');
  await writeFile(output + '/dashboard-capture-error.txt', message);
  throw new Error('Dashboard capture failed; see sanitized diagnostic artifact');
} finally {
  await browser.close();
}
