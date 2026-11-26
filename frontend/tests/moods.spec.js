import { test, expect } from "./fixtures.js";
import AxeBuilder from "@axe-core/playwright";

for (const width of [360, 1440])
  test(`mood recipes preserve stock and work at ${width}px`, async ({
    page,
  }) => {
    await page.setViewportSize({ width, height: 1000 });
    await page.emulateMedia({ reducedMotion: "reduce" });
    const credentials = {
      email: `mood-${crypto.randomUUID()}@example.test`,
      password: "Synthetic-mood-fixture-123!",
    };
    await page.request.post("/api/accounts", { data: credentials });
    const { token } = await (
      await page.request.post("/api/sessions", { data: credentials })
    ).json();
    const headers = { Authorization: `Bearer ${token}` };
    for (const [name, quantity, unit] of [
      ["banana", 2, "pcs"],
      ["milk", 200, "ml"],
      ["sugar", 20, "g"],
    ])
      await page.request.post("/api/inventory", {
        headers,
        data: { name, quantity, unit },
      });
    const before = await (
      await page.request.get("/api/inventory", { headers })
    ).json();
    await page.goto("/");
    await page.evaluate(
      (value) =>
        sessionStorage.setItem("fridgely.session", JSON.stringify(value)),
      { token, email: credentials.email },
    );
    await page.goto("/#/recipes");
    await page.reload();
    const moods = page.getByRole("group", { name: "What's your mood?" });
    for (const label of [
      "I'm Lazy",
      "High Protein",
      "Sweet Cravings",
      "Low Budget",
      "Quick & Easy",
      "Healthy",
    ])
      await expect(
        moods.getByRole("button", { name: new RegExp(label) }),
      ).toBeVisible();
    const lazy = moods.getByRole("button", { name: /I'm Lazy/ });
    await lazy.focus();
    await page.keyboard.press("Space");
    await expect(lazy).toHaveAttribute("aria-pressed", "true");
    const pending = page.waitForRequest(
      (r) => r.url().endsWith("/recipes/generate") && r.method() === "POST",
    );
    await page
      .getByRole("button", { name: "Generate recipes", exact: true })
      .click();
    expect((await pending).postDataJSON()).toEqual({ mood: "lazy" });
    await expect(
      page.getByRole("heading", { name: "Banana shake", exact: true }),
    ).toBeVisible();
    expect(
      await (await page.request.get("/api/inventory", { headers })).json(),
    ).toEqual(before);
    expect(
      (await new AxeBuilder({ page }).include("main").analyze()).violations,
    ).toEqual([]);
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
    await page.screenshot({ path: `../test-results/mood-${width}.png`, fullPage: true });
    await moods
      .getByRole("button", { name: "Clear mood", exact: true })
      .click();
    await expect(lazy).toHaveAttribute("aria-pressed", "false");
    const next = page.waitForRequest(
      (r) => r.url().endsWith("/recipes/generate") && r.method() === "POST",
    );
    await page
      .getByRole("button", { name: "Generate recipes", exact: true })
      .click();
    expect((await next).postDataJSON()).toEqual({});
    await expect(
      page.getByRole("heading", { name: "Banana shake", exact: true }),
    ).toBeVisible();
    for (const [id, label] of [
      ["high-protein", "High Protein"],
      ["sweet", "Sweet Cravings"],
      ["budget", "Low Budget"],
      ["quick", "Quick & Easy"],
      ["healthy", "Healthy"],
    ]) {
      await moods.getByRole("button", { name: new RegExp(label) }).click();
      const request = page.waitForRequest(
        (r) => r.url().endsWith("/recipes/generate") && r.method() === "POST",
      );
      await page
        .getByRole("button", { name: "Generate recipes", exact: true })
        .click();
      expect((await request).postDataJSON()).toEqual({ mood: id });
      await expect(
        page.getByRole("heading", { name: "Banana shake", exact: true }),
      ).toBeVisible();
    }
  });

test("empty fridge, pending request and provider failure have honest mood states", async ({
  page,
}) => {
  const credentials = {
    email: `mood-error-${crypto.randomUUID()}@example.test`,
    password: "Synthetic-mood-fixture-123!",
  };
  await page.request.post("/api/accounts", { data: credentials });
  const { token } = await (
    await page.request.post("/api/sessions", { data: credentials })
  ).json();
  const headers = { Authorization: `Bearer ${token}` };
  await page.goto("/");
  await page.evaluate(
    (value) =>
      sessionStorage.setItem("fridgely.session", JSON.stringify(value)),
    { token, email: credentials.email },
  );
  await page.goto("/#/recipes");
  await page.reload();
  await expect(
    page.getByRole("button", { name: "Generate recipes", exact: true }),
  ).toBeDisabled();
  await page.request.post("/api/inventory", {
    headers,
    data: { name: "banana", quantity: 2, unit: "pcs" },
  });
  await page.reload();
  const moods = page.getByRole("group", { name: "What's your mood?" });
  const sweet = moods.getByRole("button", { name: /Sweet Cravings/ });
  await sweet.click();
  let release;
  const ready = new Promise((resolve) => {
    release = resolve;
  });
  await page.route("**/api/recipes/generate", async (route) => {
    await ready;
    await route.fulfill({
      status: 503,
      contentType: "application/json",
      body: JSON.stringify({
        error: "The recipe service is temporarily unavailable.",
        retryable: true,
      }),
    });
  });
  await page
    .getByRole("button", { name: "Generate recipes", exact: true })
    .click();
  await expect(sweet).toBeDisabled();
  await expect(
    page.getByRole("button", { name: "Finding inspiration…", exact: true }),
  ).toBeDisabled();
  release();
  await expect(page.getByRole("alert")).toContainText(
    "The service is temporarily unavailable. Please try again.",
  );
  await expect(sweet).toHaveAttribute("aria-pressed", "true");
  await expect(sweet).toBeEnabled();
  await page.unroute("**/api/recipes/generate");
  await page
    .getByRole("button", { name: "Generate recipes", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Banana shake", exact: true }),
  ).toBeVisible();
  await sweet.click();
  await expect(sweet).toHaveAttribute("aria-pressed", "false");
});
