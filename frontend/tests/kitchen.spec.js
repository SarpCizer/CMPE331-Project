import { test, expect } from "./fixtures.js";
import AxeBuilder from "@axe-core/playwright";

const password = "Browser-Test-Password!";
const email = () =>
  `browser-${Date.now()}-${Math.random().toString(36).slice(2)}@example.test`;
async function register(page, address = email()) {
  await page.goto("/");
  await page
    .getByRole("button", { name: "Create an account", exact: true })
    .click();
  await page.getByLabel("Email address").fill(address);
  await page.getByLabel("Password", { exact: true }).fill(password);
  await page
    .getByRole("button", { name: "Create account", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "My fridge", exact: true }),
  ).toBeVisible();
  await expect(page.getByText("A fresh canvas", { exact: true })).toBeVisible();
  return address;
}
async function add(page, name) {
  await page.getByLabel("Add an ingredient", { exact: true }).fill(name);
  await page
    .getByRole("button", { name: "Add ingredient", exact: true })
    .click();
  await expect(
    page.getByRole("button", { name: `Remove ${name}`, exact: true }),
  ).toBeVisible();
}

test("public API documentation loads the actual schema and bearer authorization", async ({
  page,
}) => {
  await page.goto("/");
  await page
    .getByRole("link", { name: "API documentation", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: /Fridgely API/ }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Authorize", exact: true }).first(),
  ).toBeVisible();
  await expect(
    page
      .locator(".opblock-summary-path")
      .filter({ hasText: "/inventory" })
      .first(),
  ).toBeVisible();
  await expect(
    page
      .locator(".opblock-summary-path")
      .filter({ hasText: "/recipes/generate" }),
  ).toBeVisible();
  const schema = await page.request.get("/api/openapi.json");
  expect(schema.status()).toBe(200);
  expect(
    (await schema.json()).components.securitySchemes.BearerAuth.bearerFormat,
  ).toBe("JWT");
});

test("real account, saved preferences, recipe details and collections survive reload and user switching", async ({
  page,
}) => {
  const alice = await register(page);
  await page.getByLabel("Quantity", { exact: true }).fill("0.5");
  await page.getByLabel("Unit", { exact: true }).selectOption("kg");
  await add(page, "rice");
  await expect(page.getByText("· 0.5 kg", { exact: true })).toBeVisible();
  await page.getByRole("link", { name: "Preferences", exact: true }).click();
  await page.getByLabel("Dietary preferences").fill("vegan");
  await page.getByLabel("Ingredients to exclude").fill("peanut");
  await page.getByRole("button", { name: "Save preferences" }).click();
  await expect(page.getByRole("status")).toContainText("Preferences saved");
  await page.getByRole("link", { name: "Find recipes", exact: true }).click();
  await page
    .getByRole("button", { name: "Generate recipes", exact: true })
    .click();
  const card = page.getByRole("article").filter({
    has: page.getByRole("heading", { name: "Tomato rice", exact: true }),
  });
  await card.getByRole("button", { name: "View recipe" }).click();
  const dialog = page.getByRole("dialog");
  await expect(dialog).toContainText("Estimated 25 minutes");
  await expect(dialog.getByRole("listitem")).toContainText([
    "rice · 150 g",
    "tomato · 2 pcs",
    "onion · 1 pcs",
    "Cook the rice.",
    "Simmer tomato and onion.",
    "Combine and serve.",
  ]);
  await dialog
    .getByRole("button", { name: "Save favorite", exact: true })
    .click();
  await expect(
    dialog.getByRole("button", { name: "Remove favorite" }),
  ).toBeVisible();
  await dialog.getByRole("button", { name: "Add missing ingredients" }).click();
  await dialog.getByRole("button", { name: "Close recipe" }).click();
  await page.getByRole("link", { name: "Shopping list", exact: true }).click();
  await expect(
    page.getByRole("button", { name: "Remove tomato", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Remove rice", exact: true }),
  ).toHaveCount(0);
  await page.reload();
  await expect(
    page.getByRole("button", { name: "Remove tomato", exact: true }),
  ).toBeVisible();
  await page.getByRole("link", { name: "Favorites", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Tomato rice", exact: true }),
  ).toBeVisible();
  await page
    .getByRole("link", { name: "Recently viewed", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Tomato rice", exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Sign out", exact: true }).click();
  await register(page);
  await expect(
    page.getByRole("button", { name: "Remove rice", exact: true }),
  ).toHaveCount(0);
  await page.getByRole("link", { name: "Favorites", exact: true }).click();
  await expect(page.getByText("Keep the good ones close")).toBeVisible();
  await page.getByRole("button", { name: "Sign out", exact: true }).click();
  await page.getByLabel("Email address").fill(alice);
  await page.getByLabel("Password", { exact: true }).fill(password);
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await page.getByRole("link", { name: "My fridge", exact: true }).click();
  await expect(
    page.getByRole("button", { name: "Remove rice", exact: true }),
  ).toBeVisible();
});

test("empty fridge and provider failure remain honest and retryable", async ({
  page,
}) => {
  await register(page);
  await page.getByRole("link", { name: "Find recipes", exact: true }).click();
  await expect(
    page.getByRole("button", { name: "Generate recipes", exact: true }),
  ).toBeDisabled();
  await page.getByRole("link", { name: "My fridge", exact: true }).click();
  await add(page, "provider-failure");
  await page.getByRole("link", { name: "Find recipes", exact: true }).click();
  await page
    .getByRole("button", { name: "Generate recipes", exact: true })
    .click();
  await expect(page.getByRole("alert")).toContainText(
    "temporarily unavailable",
  );
  await expect(page.getByRole("article")).toHaveCount(0);
  await expect(
    page.getByRole("button", { name: "Generate recipes", exact: true }),
  ).toBeEnabled();
  await page.getByRole("link", { name: "My fridge", exact: true }).click();
  await expect(
    page.getByRole("button", { name: "Remove provider-failure", exact: true }),
  ).toBeVisible();
});

for (const width of [360, 768, 1440])
  test(`core screens fit ${width}px and retain labelled controls`, async ({
    page,
  }) => {
    await page.setViewportSize({ width, height: 1000 });
    await register(page);
    await add(page, "tomato");
    await page.screenshot({
      path: `../test-results/screens/fridge-${width}.png`,
      fullPage: true,
    });
    await add(
      page,
      "a-very-long-ingredient-name-to-check-wrapping-in-the-layout",
    );
    for (const label of [
      "My fridge",
      "Find recipes",
      "Shopping list",
      "Favorites",
      "Recently viewed",
      "Preferences",
    ]) {
      await page.getByRole("link", { name: label, exact: true }).click();
      await expect(
        page.getByRole("heading", { name: label, exact: true }),
      ).toBeVisible();
      expect(
        await page.evaluate(
          () => document.documentElement.scrollWidth <= window.innerWidth,
        ),
      ).toBe(true);
      if (width === 1440) {
        await page.getByRole("link", {name:label,exact:true}).evaluate(element =>
          Promise.all(element.getAnimations().map(animation => animation.finished.catch(() => {}))));
        const audit = await new AxeBuilder({ page })
          .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
          .analyze();
        expect(audit.violations).toEqual([]);
      }
    }
  });

test("keyboard skip link focuses the active main region", async ({ page }) => {
  await register(page);
  await page.getByRole("link", { name: "Preferences", exact: true }).click();
  await page.getByRole("link", { name: "Skip to content" }).focus();
  await page.keyboard.press("Enter");
  await expect(page.getByRole("main")).toBeFocused();
  await expect(
    page.getByRole("heading", { name: "Preferences", exact: true }),
  ).toBeVisible();
});

test("core kitchen actions work with keyboard-only input", async ({ page }) => {
  async function tabTo(locator) {
    for (let attempt = 0; attempt < 45; attempt++) {
      if (
        await locator.evaluate((element) => element === document.activeElement)
      )
        return;
      await page.keyboard.press("Tab");
    }
    throw new Error("Core control could not be reached with Tab");
  }
  async function activate(locator) {
    await tabTo(locator);
    await page.keyboard.press("Enter");
  }
  async function enter(locator, value) {
    await tabTo(locator);
    await page.keyboard.type(value);
  }
  await page.goto("/");
  await activate(
    page.getByRole("button", { name: "Create an account", exact: true }),
  );
  await enter(page.getByLabel("Email address"), email());
  await enter(page.getByLabel("Password", { exact: true }), password);
  await activate(
    page.getByRole("button", { name: "Create account", exact: true }),
  );
  await expect(
    page.getByRole("heading", { name: "My fridge", exact: true }),
  ).toBeVisible();
  await enter(page.getByLabel("Add an ingredient", { exact: true }), "rice");
  await activate(
    page.getByRole("button", { name: "Add ingredient", exact: true }),
  );
  await expect(
    page.getByRole("button", { name: "Remove rice", exact: true }),
  ).toBeVisible();
  await activate(page.getByRole("link", { name: "Preferences", exact: true }));
  await enter(page.getByLabel("Dietary preferences"), "vegan");
  await enter(page.getByLabel("Ingredients to exclude"), "peanut");
  await activate(page.getByRole("button", { name: "Save preferences" }));
  await expect(page.getByRole("status")).toContainText("Preferences saved");
  await activate(page.getByRole("link", { name: "Find recipes", exact: true }));
  await activate(
    page.getByRole("button", { name: "Generate recipes", exact: true }),
  );
  const card = page.getByRole("article").filter({
    has: page.getByRole("heading", { name: "Tomato rice", exact: true }),
  });
  await expect(card).toBeVisible();
  await activate(card.getByRole("button", { name: "View recipe" }));
  const dialog = page.getByRole("dialog");
  await expect(dialog).toBeVisible();
  await activate(
    dialog.getByRole("button", { name: "Save favorite", exact: true }),
  );
  await expect(
    dialog.getByRole("button", { name: "Remove favorite", exact: true }),
  ).toBeVisible();
  await activate(
    dialog.getByRole("button", { name: "Add missing ingredients" }),
  );
  await activate(dialog.getByRole("button", { name: "Close recipe" }));
  await activate(
    page.getByRole("link", { name: "Shopping list", exact: true }),
  );
  await expect(
    page.getByRole("button", { name: "Remove onion", exact: true }),
  ).toBeVisible();
  await activate(
    page.getByRole("button", { name: "Remove onion", exact: true }),
  );
  await expect(
    page.getByRole("button", { name: "Remove onion", exact: true }),
  ).toHaveCount(0);
  await activate(page.getByRole("link", { name: "Favorites", exact: true }));
  await expect(
    page.getByRole("heading", { name: "Tomato rice", exact: true }),
  ).toBeVisible();
  await activate(
    page.getByRole("link", { name: "Recently viewed", exact: true }),
  );
  await expect(
    page.getByRole("heading", { name: "Tomato rice", exact: true }),
  ).toBeVisible();
  await activate(page.getByRole("link", { name: "My fridge", exact: true }));
  await activate(
    page.getByRole("button", { name: "Remove rice", exact: true }),
  );
  await expect(page.getByText("A fresh canvas", { exact: true })).toBeVisible();
  await activate(page.getByRole("button", { name: "Sign out", exact: true }));
  await expect(
    page.getByRole("heading", { name: "Welcome back.", exact: true }),
  ).toBeVisible();
});
