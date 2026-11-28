import { test, expect } from "./fixtures.js";
import AxeBuilder from "@axe-core/playwright";

for (const width of [360, 1440]) {
  test(`ready recipes and wheel survive incomplete transport at ${width}px`, async ({
    page,
  }) => {
    await page.setViewportSize({ width, height: 1000 });
    const credentials = {
      email: `resilience-${crypto.randomUUID()}@example.test`,
      password: "Synthetic-resilience-123!",
    };
    await page.request.post("/api/accounts", { data: credentials });
    const { token } = await (
      await page.request.post("/api/sessions", { data: credentials })
    ).json();
    const headers = { Authorization: `Bearer ${token}` };
    await page.request.post("/api/inventory", {
      headers,
      data: { name: "milk", quantity: 1000, unit: "ml" },
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
    // Actual fixture generation/storage; only the outcome header is controlled.
    let incomplete = true;
    await page.route("**/api/recipes/generate", async (route) => {
      const response = await route.fetch();
      expect(response.status()).toBe(200);
      await route.fulfill({
        response,
        headers: {
          ...response.headers(),
          ...(incomplete ? { "x-fridgely-generation-incomplete": "true" } : {}),
        },
      });
    });
    const button = page.getByRole("button", {
      name: "Generate recipes",
      exact: true,
    });
    await button.click();
    await expect(
      page.getByRole("heading", { name: "Warm milk", exact: true }),
    ).toBeVisible();
    const notice = page
      .getByRole("status")
      .filter({ hasText: "Some additional suggestions could not finish" });
    await expect(notice).toBeVisible();
    const wheel = page.getByRole("region", {
      name: "Surprise me recipe wheel",
    });
    await expect(wheel.locator("summary")).toContainText("(1)");
    await expect(wheel.locator("li")).toHaveText(["Warm milk"]);
    incomplete = false;
    await button.click();
    await expect(notice).toHaveCount(0);
    await expect(
      page.getByRole("heading", { name: "Warm milk", exact: true }),
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
  });
}
