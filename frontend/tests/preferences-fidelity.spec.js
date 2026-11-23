import { test, expect } from "./fixtures.js";

async function account(page) {
  const credentials = {
    email: `fidelity-${crypto.randomUUID()}@example.test`,
    password: "Preference-Fidelity-Fixture!",
  };
  const registered = await page.request.post("/api/accounts", { data: credentials });
  expect(registered.status()).toBe(201);
  const login = await page.request.post("/api/sessions", { data: credentials });
  expect(login.status()).toBe(200);
  const { token } = await login.json();
  await page.goto("/");
  await page.evaluate((session) => {
    sessionStorage.setItem("fridgely.session", JSON.stringify(session));
  }, { email: credentials.email, token });
  return { Authorization: `Bearer ${token}` };
}

test("saving API preferences without edits preserves exact strings, order and repeats", async ({ page }) => {
  const headers = await account(page);
  const saved = {
    dietary: ["  Vegan  ", "low,sodium", 'say "no"', "line\nbreak", "Vegan", "Vegan"],
    allergens: [" peanut ", "milk, powder", 'a "quoted" name', "sesame", "sesame"],
  };
  expect((await page.request.put("/api/profile/preferences", { headers, data: saved })).status()).toBe(200);
  await page.goto("/#/preferences");
  await page.reload();
  await expect(page.getByLabel("Dietary preferences")).toBeVisible();
  const written = page.waitForResponse((response) => response.url().endsWith("/api/profile/preferences") && response.request().method() === "PUT");
  await page.getByRole("button", { name: "Save preferences" }).click();
  expect((await written).status()).toBe(200);
  const read = await page.request.get("/api/profile/preferences", { headers });
  expect(await read.json()).toEqual(saved);
  await page.reload();
  await expect(page.getByLabel("Dietary preferences")).toBeVisible();
  await page.getByRole("button", { name: "Save preferences" }).click();
  await expect(page.getByRole("status")).toContainText("Preferences saved");
  expect(await (await page.request.get("/api/profile/preferences", { headers })).json()).toEqual(saved);
});

test("quoted preference edits preserve names and invalid quoting never sends a write", async ({ page }) => {
  const headers = await account(page);
  const saved = { dietary: ["original"], allergens: [" sesame ", "milk, powder", "sesame"] };
  expect((await page.request.put("/api/profile/preferences", { headers, data: saved })).status()).toBe(200);
  await page.goto("/#/preferences");
  await page.reload();
  await expect(page.getByLabel("Dietary preferences")).toHaveValue("original");
  let writes = 0;
  page.on("request", (request) => {
    if (request.method() === "PUT" && request.url().endsWith("/api/profile/preferences")) writes++;
  });
  await page.getByLabel("Dietary preferences").fill('"unfinished');
  await page.getByRole("button", { name: "Save preferences" }).click();
  await expect(page.getByLabel("Dietary preferences")).toHaveAttribute("aria-invalid", "true");
  await expect(page.getByLabel("Dietary preferences")).toHaveAccessibleDescription(/quoted/i);
  expect(writes).toBe(0);
  expect(await (await page.request.get("/api/profile/preferences", { headers })).json()).toEqual(saved);
  await page.getByLabel("Dietary preferences").fill('"  Vegan  ", "low,sodium", "say ""no""", vegan, vegan');
  await page.getByRole("button", { name: "Save preferences" }).click();
  await expect(page.getByRole("status")).toContainText("Preferences saved");
  expect(await (await page.request.get("/api/profile/preferences", { headers })).json()).toEqual({
    dietary: ["  Vegan  ", "low,sodium", 'say "no"', "vegan", "vegan"],
    allergens: saved.allergens,
  });
  await page.getByLabel("Dietary preferences").fill("");
  await page.getByRole("button", { name: "Save preferences" }).click();
  await expect(page.getByRole("status")).toContainText("Preferences saved");
  expect(await (await page.request.get("/api/profile/preferences", { headers })).json()).toEqual({
    dietary: [], allergens: saved.allergens,
  });
});
