import { test, expect } from "./fixtures.js";
import AxeBuilder from "@axe-core/playwright";

async function register(page) {
  await page.goto("/");
  await page
    .getByRole("button", { name: "Create an account", exact: true })
    .click();
  await page
    .getByLabel("Email address")
    .fill(`completion-${crypto.randomUUID()}@example.test`);
  await page
    .getByLabel("Password", { exact: true })
    .fill("Frontend-Completion-Password!");
  await page
    .getByRole("button", { name: "Create account", exact: true })
    .click();
  await expect(page.getByText("A fresh canvas", { exact: true })).toBeVisible();
}

async function addRice(page) {
  await page.getByLabel("Add an ingredient", { exact: true }).fill("rice");
  await page
    .getByRole("button", { name: "Add ingredient", exact: true })
    .click();
  await expect(
    page.getByRole("button", { name: "Remove rice", exact: true }),
  ).toBeVisible();
}

async function generate(page) {
  await page.getByRole("link", { name: "Find recipes", exact: true }).click();
  await page
    .getByRole("button", { name: "Generate recipes", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Tomato rice", exact: true }),
  ).toBeVisible();
}

test("invalid fields explain the problem at the input without sending writes", async ({
  page,
}) => {
  let writes = 0;
  page.on("request", (request) => {
    if (request.method() === "POST" || request.method() === "PUT") writes++;
  });
  await page.goto("/");
  await page
    .getByRole("button", { name: "Create an account", exact: true })
    .click();
  await page.getByLabel("Email address").fill("invalid");
  await page.getByLabel("Password", { exact: true }).fill("short");
  await page
    .getByRole("button", { name: "Create account", exact: true })
    .click();
  await expect(page.getByLabel("Email address")).toHaveAttribute(
    "aria-invalid",
    "true",
  );
  await expect(page.getByLabel("Email address")).toHaveAccessibleDescription(
    /valid email/i,
  );
  await expect(
    page.getByLabel("Password", { exact: true }),
  ).toHaveAccessibleDescription(/at least 8/i);
  expect(writes).toBe(0);
  await page
    .getByLabel("Email address")
    .fill(`validation-${crypto.randomUUID()}@example.test`);
  await page
    .getByLabel("Password", { exact: true })
    .fill("Frontend-Completion-Password!");
  await page
    .getByRole("button", { name: "Create account", exact: true })
    .click();
  await expect(page.getByText("A fresh canvas", { exact: true })).toBeVisible();
  const before = writes;
  await page.getByLabel("Add an ingredient", { exact: true }).fill("   ");
  await page
    .getByRole("button", { name: "Add ingredient", exact: true })
    .click();
  await expect(
    page.getByLabel("Add an ingredient", { exact: true }),
  ).toHaveAccessibleDescription(/enter an ingredient/i);
  await page.getByRole("link", { name: "Shopping list", exact: true }).click();
  await page.getByLabel("Add a shopping item").fill("   ");
  await page.getByRole("button", { name: "Add item", exact: true }).click();
  await expect(
    page.getByLabel("Add a shopping item"),
  ).toHaveAccessibleDescription(/enter a shopping item/i);
  await page.getByRole("link", { name: "Preferences", exact: true }).click();
  await page
    .getByLabel("Dietary preferences")
    .fill(Array.from({ length: 101 }, (_, i) => `preference${i}`).join(","));
  await page.getByLabel("Ingredients to exclude").fill("a".repeat(129));
  await page.getByRole("button", { name: "Save preferences" }).click();
  await expect(
    page.getByLabel("Dietary preferences"),
  ).toHaveAccessibleDescription(/at most 100/i);
  await expect(
    page.getByLabel("Ingredients to exclude"),
  ).toHaveAccessibleDescription(/at most 128/i);
  expect(writes).toBe(before);
  await page.getByLabel("Dietary preferences").fill("vegan");
  await page.getByLabel("Ingredients to exclude").fill("peanut");
  await page.getByRole("button", { name: "Save preferences" }).click();
  await expect(page.getByRole("status")).toContainText("Preferences saved");
  await page.reload();
  await expect(page.getByLabel("Dietary preferences")).toHaveValue("vegan");
});

test("a failed collection does not discard inventory or turn a committed write into failure", async ({
  page,
}) => {
  await register(page);
  await addRice(page);
  let unavailable = true;
  await page.route("**/api/favorites", (route) =>
    unavailable && route.request().method() === "GET"
      ? route.fulfill({
          status: 503,
          json: { error: "Isolated collection outage" },
        })
      : route.continue(),
  );
  await page.reload();
  await expect(
    page.getByRole("button", { name: "Remove rice", exact: true }),
  ).toBeVisible();
  await page.getByLabel("Add an ingredient", { exact: true }).fill("onion");
  await page
    .getByRole("button", { name: "Add ingredient", exact: true })
    .click();
  await expect(
    page.getByRole("button", { name: "Remove onion", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByLabel("Add an ingredient", { exact: true }),
  ).toHaveValue("");
  await page.getByRole("link", { name: "Favorites", exact: true }).click();
  await expect(page.getByRole("alert")).toContainText(
    "Favorites could not be loaded",
  );
  await expect(page.getByText("Keep the good ones close")).toHaveCount(0);
  unavailable = false;
  await page
    .getByRole("button", { name: "Retry favorites", exact: true })
    .click();
  await expect(page.getByText("Keep the good ones close")).toBeVisible();
});

test("a slow collection does not block unrelated screens", async ({ page }) => {
  await register(page);
  await addRice(page);
  let release;
  const waiting = new Promise((resolve) => {
    release = resolve;
  });
  await page.route("**/api/favorites", async (route) => {
    await waiting;
    await route.continue();
  });
  try {
    await page.reload({ waitUntil: "domcontentloaded" });
    await expect(
      page.getByRole("button", { name: "Remove rice", exact: true }),
    ).toBeVisible({ timeout: 5000 });
    await page.getByRole("link", { name: "Favorites", exact: true }).click();
    await expect(page.getByRole("status")).toContainText("Loading favorites");
  } finally {
    release();
  }
  await expect(page.getByText("Keep the good ones close")).toBeVisible();
});

test("a committed write is acknowledged even when its subsequent list refresh fails", async ({
  page,
}) => {
  await register(page);
  let failRefresh = false;
  let writes = 0;
  await page.route("**/api/shopping-items", (route) => {
    if (route.request().method() === "POST") {
      failRefresh = true;
      writes++;
      return route.continue();
    }
    return failRefresh
      ? route.fulfill({ status: 503, json: { error: "refresh outage" } })
      : route.continue();
  });
  await page.getByRole("link", { name: "Shopping list", exact: true }).click();
  await page.getByLabel("Add a shopping item").fill("tomato");
  await page.getByRole("button", { name: "Add item", exact: true }).click();
  await expect(page.getByRole("status")).toContainText(
    "Shopping item added. Some saved data could not be refreshed",
  );
  await expect(page.getByRole("alert")).toContainText(
    "Shopping list could not be loaded",
  );
  expect(writes).toBe(1);
  failRefresh = false;
  await page
    .getByRole("button", { name: "Retry shopping list", exact: true })
    .click();
  await expect(
    page.getByRole("button", { name: "Remove tomato", exact: true }),
  ).toBeVisible();
  await expect(page.getByLabel("Add a shopping item")).toHaveValue("");
  expect(writes).toBe(1);
});

test("an expired session wins over a simultaneous collection outage", async ({
  page,
}) => {
  await register(page);
  await page.route("**/api/favorites", (route) =>
    route.fulfill({ status: 503, json: { error: "outage" } }),
  );
  await page.route("**/api/inventory", async (route) => {
    await new Promise((resolve) => setTimeout(resolve, 150));
    await route.fulfill({ status: 401, json: { error: "expired" } });
  });
  await page.reload();
  await expect(
    page.getByRole("heading", { name: "Welcome back." }),
  ).toBeVisible();
  await expect(page.getByRole("alert")).toContainText("Your session ended");
  expect(
    await page.evaluate(() => sessionStorage.getItem("fridgely.session")),
  ).toBeNull();
});

test("recipe actions show modal errors, prevent duplicate writes and open the resulting shopping list", async ({
  page,
}) => {
  await register(page);
  await addRice(page);
  await generate(page);
  await page
    .getByRole("article")
    .filter({
      has: page.getByRole("heading", { name: "Tomato rice", exact: true }),
    })
    .getByRole("button", { name: "View recipe" })
    .click();
  const dialog = page.getByRole("dialog");
  let release;
  let posts = 0;
  const waiting = new Promise((resolve) => {
    release = resolve;
  });
  await page.route("**/api/favorites", async (route) => {
    if (route.request().method() !== "POST") return route.continue();
    posts++;
    await waiting;
    await route.fulfill({
      status: 503,
      json: { error: "private provider diagnostic" },
    });
  });
  try {
    await dialog
      .getByRole("button", { name: "Save favorite", exact: true })
      .click();
    await expect(
      dialog.getByRole("button", { name: "Save favorite", exact: true }),
    ).toBeDisabled();
    await expect(
      dialog.getByRole("button", {
        name: "Add missing ingredients",
        exact: true,
      }),
    ).toBeDisabled();
  } finally {
    release();
  }
  await expect(dialog.getByRole("alert")).toContainText(
    "temporarily unavailable",
  );
  await expect(dialog).not.toContainText("private provider diagnostic");
  expect(posts).toBe(1);
  await page.unroute("**/api/favorites");
  await dialog
    .getByRole("button", { name: "Save favorite", exact: true })
    .click();
  await expect(
    dialog.getByRole("button", { name: "Remove favorite", exact: true }),
  ).toBeVisible();
  await dialog
    .getByRole("button", { name: "Add missing ingredients", exact: true })
    .click();
  await expect(dialog.getByRole("status")).toContainText(
    "Missing ingredients added",
  );
  await dialog
    .getByRole("link", { name: "View shopping list", exact: true })
    .click();
  await expect(dialog).toHaveCount(0);
  await expect(
    page.getByRole("heading", { name: "Shopping list", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Remove tomato", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Remove rice", exact: true }),
  ).toHaveCount(0);
});

test("failed generation keeps previous results and hides provider diagnostics", async ({
  page,
}) => {
  await register(page);
  await addRice(page);
  await generate(page);
  for (const status of [502, 422]) {
    await page.route("**/api/recipes/generate", (route) =>
      route.fulfill({ status, json: { error: "PRIVATE_UPSTREAM_DIAGNOSTIC" } }),
    );
    await page
      .getByRole("button", { name: "Generate recipes", exact: true })
      .click();
    await expect(page.getByRole("alert")).toBeVisible();
    await expect(page.getByRole("alert")).not.toContainText(
      "PRIVATE_UPSTREAM_DIAGNOSTIC",
    );
    await expect(
      page.getByRole("heading", { name: "Tomato rice", exact: true }),
    ).toBeVisible();
    await page.unroute("**/api/recipes/generate");
  }
  await page
    .getByRole("button", { name: "Generate recipes", exact: true })
    .click();
  await expect(page.getByRole("status")).toContainText("Recipes are ready");
});

for (const width of [360, 768, 1440]) {
  test(`validation and unavailable screens remain accessible at ${width}px`, async ({
    page,
  }) => {
    await page.setViewportSize({ width, height: 900 });
    await page.goto("/");
    await page.getByRole("button", { name: "Sign in", exact: true }).click();
    await expect(page.getByLabel("Email address")).toHaveAttribute(
      "aria-invalid",
      "true",
    );
    expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
    await register(page);
    await page.route("**/api/favorites", (route) =>
      route.fulfill({ status: 503, json: { error: "outage" } }),
    );
    await page.reload();
    for (const name of [
      "My fridge",
      "Find recipes",
      "Shopping list",
      "Favorites",
      "Recently viewed",
      "Preferences",
    ]) {
      await page.getByRole("link", { name, exact: true }).click();
      await expect(
        page.getByRole("heading", { name, exact: true }),
      ).toBeVisible();
      if (name === "Favorites") {
        await expect(page.getByRole("alert")).toContainText(
          "Favorites could not be loaded",
        );
        await page
          .getByRole("button", { name: "Retry favorites", exact: true })
          .focus();
        await expect(
          page.getByRole("button", { name: "Retry favorites", exact: true }),
        ).toBeFocused();
      }
      expect(
        await page.evaluate(
          () => document.documentElement.scrollWidth <= innerWidth,
        ),
      ).toBe(true);
      expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
    }
  });
}
