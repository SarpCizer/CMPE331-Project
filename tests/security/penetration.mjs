// Scoped attack probes against our isolated application, with disposable accounts.
import assert from "node:assert/strict";
import { randomUUID } from "node:crypto";
import { mkdir, writeFile } from "node:fs/promises";
import { chromium } from "../../frontend/node_modules/@playwright/test/index.mjs";

const base = process.env.API_BASE_URL || "http://127.0.0.1:8000";
if (!["127.0.0.1", "localhost", "[::1]"].includes(new URL(base).hostname)) {
  throw new Error("Use an isolated local test host for attack probes");
}
const results = [];
const credentials = { email: `attack-${randomUUID()}@example.test`, password: `Test-${randomUUID()}!` };
async function request(method, path, body, token, expected = 200) {
  const response = await fetch(`${base}${path}`, {
    method,
    headers: { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}) },
    ...(body === undefined ? {} : { body: JSON.stringify(body) }),
    signal: AbortSignal.timeout(10000),
  });
  assert.equal(response.status, expected, `${method} ${path}`);
  const text = await response.text();
  return text ? JSON.parse(text) : undefined;
}
await request("POST", "/api/accounts", credentials, undefined, 201);
const { token } = await request("POST", "/api/sessions", credentials);

// SQL syntax must remain literal application data, never alter a query or table.
const sql = "rice'); DROP TABLE accounts; --";
const item = await request("POST", "/api/inventory", { name: sql }, token, 201);
assert.equal(item.name, sql);
assert.ok((await request("GET", "/api/inventory", undefined, token)).some((row) => row.id === item.id && row.name === sql));
await request("POST", "/api/sessions", credentials);
results.push({ id: "PEN-01", scenario: "SQL injection payload retained literally; accounts remain usable", passed: true });

// Caller-supplied ownership fields cannot reassign an account's data.
const before = await request("GET", "/api/inventory", undefined, token);
await request("POST", "/api/inventory", { name: "tomato", owner_id: "another-account" }, token, 400);
assert.deepEqual(await request("GET", "/api/inventory", undefined, token), before);
await request("PUT", "/api/profile/preferences", { dietary: [], allergens: [], ownerId: "another-account" }, token, 400);
results.push({ id: "PEN-02", scenario: "Mass assignment rejected without state mutation", passed: true });

// Known configuration/source paths and encoded traversals must not disclose files.
for (const path of ["/.env", "/api/.env", "/api/docs/assets/%2e%2e%2f.env", "/backend/src/fridgely_app/security.py"]) {
  const response = await fetch(`${base}${path}`, { signal: AbortSignal.timeout(10000) });
  assert.equal(response.status, 404, path);
  assert.ok(!(await response.text()).includes("JWT_SECRET="));
}
results.push({ id: "PEN-03", scenario: "Configuration, source and encoded file-traversal probes denied", passed: true });

// A stored HTML payload must be visible as text and must never create an element.
const payload = '<img src=x onerror="window.__fridgelyProbe=1">';
await request("POST", "/api/inventory", { name: payload }, token, 201);
const browser = await chromium.launch({ headless: true, ...(process.env.PLAYWRIGHT_CHANNEL ? { channel: process.env.PLAYWRIGHT_CHANNEL } : {}) });
try {
  const page = await browser.newPage();
  await page.goto(base);
  await page.getByLabel("Email address").fill(credentials.email);
  await page.getByLabel("Password", { exact: true }).fill(credentials.password);
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await page.getByText(payload, { exact: true }).waitFor();
  assert.equal(await page.locator(".ingredient-list img").count(), 0);
  assert.equal(await page.evaluate(() => window.__fridgelyProbe), undefined);
  await page.reload();
  await page.getByText(payload, { exact: true }).waitFor();
  assert.equal(await page.evaluate(() => window.__fridgelyProbe), undefined);
  results.push({ id: "PEN-04", scenario: "Stored XSS rendered as inert text before and after reload", passed: true });
} finally {
  await browser.close();
}
await mkdir("test-results", { recursive: true });
await writeFile("test-results/penetration.json", JSON.stringify({
  passed: true, environment: "isolated actual FastAPI/SQL host and production React build",
  source_revision: process.env.TESTED_REVISION || "local working source",
  provider: "controlled external fixture; not exercised by these probes", results,
  limits: "Targeted automated penetration probes, not a complete third-party penetration assessment. No credentials or tokens exported.",
}, null, 2) + "\n");
console.log(`Penetration probes passed: ${results.length}; no credentials exported`);
