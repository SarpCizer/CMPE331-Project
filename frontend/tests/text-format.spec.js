import { test, expect } from "./fixtures.js";

// Text formatting regressions found while reviewing #56 (Refs #35, #37, #38).
// A Turkish browser locale shows that dates must not depend on the browser
// language: the fridge already uses an English medium date.
test.use({ locale: "tr-TR" });

async function registerWithRice(page) {
  await page.goto("/");
  await page
    .getByRole("button", { name: "Create an account", exact: true })
    .click();
  await page
    .getByLabel("Email address")
    .fill(`format-${crypto.randomUUID()}@example.test`);
  await page
    .getByLabel("Password", { exact: true })
    .fill("Text-Format-Password!");
  await page
    .getByRole("button", { name: "Create account", exact: true })
    .click();
  await page.getByLabel("Add an ingredient", { exact: true }).fill("rice");
  await page
    .getByRole("button", { name: "Add ingredient", exact: true })
    .click();
  await expect(
    page.getByRole("button", { name: "Remove rice", exact: true }),
  ).toBeVisible();
}

test("recipe introduction uses the singular for one ingredient", async ({
  page,
}) => {
  await registerWithRice(page);
  await page.getByRole("link", { name: "Find recipes", exact: true }).click();
  await expect(
    page.getByText(/Turn the 1 ingredient in your fridge into/),
  ).toBeVisible();
});

test("recently viewed dates use the same English format as the fridge", async ({
  page,
}) => {
  await registerWithRice(page);
  await expect(
    page.getByText(/^Added [A-Z][a-z]{2} \d{1,2}, \d{4}$/),
  ).toBeVisible();
  await page.getByRole("link", { name: "Find recipes", exact: true }).click();
  await page
    .getByRole("button", { name: "Generate recipes", exact: true })
    .click();
  await page.getByRole("button", { name: "View recipe" }).first().click();
  await page.getByRole("button", { name: "Close recipe" }).click();
  await page
    .getByRole("link", { name: "Recently viewed", exact: true })
    .click();
  await expect(
    page.getByText(
      /^Viewed [A-Z][a-z]{2} \d{1,2}, \d{4}, \d{1,2}:\d{2}\s(AM|PM)$/,
    ),
  ).toBeVisible();
});
