import { test, expect } from "./fixtures.js";
import AxeBuilder from "@axe-core/playwright";

async function kitchen(page) {
  const credentials = {
    email: `wheel-${crypto.randomUUID()}@example.test`,
    password: "Isolated-wheel-fixture-123!",
  };
  await page.request.post("/api/accounts", { data: credentials });
  const { token } = await (
    await page.request.post("/api/sessions", { data: credentials })
  ).json();
  const headers = { Authorization: `Bearer ${token}` };
  // A fully stocked historical recipe must not enter the current results' wheel.
  await page.request.post("/api/inventory", {
    headers,
    data: { name: "milk", quantity: 200, unit: "ml" },
  });
  const old = await (
    await page.request.post("/api/recipes/generate", { headers, data: {} })
  ).json();
  expect(old[0].title).toBe("Warm milk");
  for (const [name, quantity, unit] of [
    ["banana", 2, "pcs"],
    ["sugar", 20, "g"],
  ])
    await page.request.post("/api/inventory", {
      headers,
      data: { name, quantity, unit },
    });
  const stock = await (
    await page.request.get("/api/inventory", { headers })
  ).json();
  await page.goto("/");
  await page.evaluate(
    (s) => sessionStorage.setItem("fridgely.session", JSON.stringify(s)),
    { token, email: credentials.email },
  );
  await page.goto("/#/recipes");
  await page.reload();
  return { headers, stock };
}
for (const width of [360, 1440])
  test(`wheel uses only fully stocked displayed recipes at ${width}`, async ({
    page,
  }) => {
    await page.setViewportSize({ width, height: 1000 });
    await page.emulateMedia({ reducedMotion: "reduce" });
    const { headers, stock } = await kitchen(page);
    const generation = page.waitForResponse(
      (r) =>
        r.url().endsWith("/api/recipes/generate") &&
        r.request().method() === "POST",
    );
    await page
      .getByRole("button", { name: "Generate recipes", exact: true })
      .click();
    const displayed = await (await generation).json();
    const cards = page
      .locator("main")
      .getByRole("heading", { name: "Banana shake", exact: true });
    await expect(cards).toBeVisible();
    const wheel = page.getByRole("region", {
      name: "Surprise me recipe wheel",
    });
    await wheel
      .getByRole("button", { name: "Spin the wheel", exact: true })
      .click();
    await expect(
      wheel.getByRole("heading", { name: "Banana shake", exact: true }),
    ).toBeVisible();
    await wheel.locator("summary").click();
    await expect(wheel.locator("li")).toHaveText(["Banana shake"]);
    await expect(wheel).not.toContainText("Warm milk");
    expect(
      (await new AxeBuilder({ page }).include("main").analyze()).violations,
    ).toEqual([]);
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
    expect(
      await (await page.request.get("/api/inventory", { headers })).json(),
    ).toEqual(stock);
    const detail = page.waitForRequest((r) =>
      r.url().endsWith(`/api/recipes/${displayed[0].id}`),
    );
    await wheel.getByRole("button", { name: "View selected recipe" }).click();
    await detail;
    await expect(page.getByRole("dialog")).toContainText("Blend.");
    await page
      .getByRole("button", { name: "Close recipe", exact: true })
      .click();
    const banana = stock.find((x) => x.name === "banana");
    await page.request.patch("/api/inventory/" + banana.id, {
      headers,
      data: { quantity: 1, unit: "pcs" },
    });
    await wheel.getByRole("button", { name: "Refresh wheel recipes" }).click();
    await expect(wheel).toContainText("No fully stocked recipes");
    await expect(wheel.locator("li")).toHaveCount(0);
  });

test("wheel waits for displayed results and resets after regeneration or clearing results", async ({
  page,
}) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await kitchen(page);
  const wheel = page.getByRole("region", { name: "Surprise me recipe wheel" });
  await expect(
    wheel.getByRole("button", { name: "Spin the wheel", exact: true }),
  ).toBeDisabled();
  await expect(
    wheel.getByRole("button", { name: "Refresh wheel recipes" }),
  ).toBeDisabled();
  await page
    .getByRole("button", { name: "Generate recipes", exact: true })
    .click();
  await wheel
    .getByRole("button", { name: "Spin the wheel", exact: true })
    .click();
  await expect(
    wheel.getByRole("button", { name: "View selected recipe" }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Generate recipes", exact: true })
    .click();
  await expect(
    wheel.getByRole("button", { name: "View selected recipe" }),
  ).toHaveCount(0);
  await wheel
    .getByRole("button", { name: "Spin the wheel", exact: true })
    .click();
  await expect(
    wheel.getByRole("heading", { name: "Banana shake", exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: /Quick & Easy/ }).click();
  await expect(
    wheel.getByRole("button", { name: "Spin the wheel", exact: true }),
  ).toBeDisabled();
  await expect(
    wheel.getByRole("button", { name: "View selected recipe" }),
  ).toHaveCount(0);
});
