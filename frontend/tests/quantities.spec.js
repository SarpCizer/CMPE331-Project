import { test, expect } from "./fixtures.js";

async function register(page) {
  await page.goto("/");
  await page.getByRole("button", { name: "Create an account", exact: true }).click();
  await page.getByLabel("Email address").fill(`quantity-${crypto.randomUUID()}@example.test`);
  await page.getByLabel("Password", { exact: true }).fill("Quantity-browser-test-password!");
  await page.getByRole("button", { name: "Create account", exact: true }).click();
  await expect(page.getByText("A fresh canvas", { exact: true })).toBeVisible();
}

test("manual quantities survive reload and edits can be saved or cancelled", async ({ page }) => {
  await register(page);
  await page.getByLabel("Add an ingredient", { exact: true }).fill("rice");
  await page.getByLabel("Quantity", { exact: true }).fill("0.5");
  await page.getByLabel("Unit", { exact: true }).selectOption("kg");
  await page.getByRole("button", { name: "Add ingredient", exact: true }).click();
  const row = page.getByRole("listitem").filter({ has: page.getByRole("button", { name: "Remove rice", exact: true }) });
  await expect(row).toContainText("0.5 kg");
  await page.reload();
  await expect(row).toContainText("0.5 kg");
  await page.getByRole("button", { name: "Edit quantity for rice", exact: true }).click();
  await page.getByLabel("Quantity", { exact: true }).fill("1.25");
  await page.getByRole("button", { name: "Save quantity", exact: true }).click();
  await expect(row).toContainText("1.25 kg");
  await page.getByRole("button", { name: "Edit quantity for rice", exact: true }).click();
  await page.getByLabel("Quantity", { exact: true }).fill("9");
  await page.getByRole("button", { name: "Cancel edit", exact: true }).click();
  await page.reload();
  await expect(row).toContainText("1.25 kg");
});

test("invalid quantities focus their own field, explain the error and send no write", async ({ page }) => {
  await register(page);
  let writes = 0;
  page.on("request", request => {
    if (request.url().includes("/api/inventory") && ["POST", "PATCH"].includes(request.method())) writes++;
  });
  await page.getByLabel("Add an ingredient", { exact: true }).fill("rice");
  const quantity = page.getByLabel("Quantity", { exact: true });
  await quantity.fill("1.5");
  await page.getByRole("button", { name: "Add ingredient", exact: true }).click();
  await expect(quantity).toBeFocused();
  await expect(quantity).toHaveAttribute("aria-invalid", "true");
  await expect(quantity).toHaveAccessibleDescription(/positive quantity|whole numbers/i);
  expect(writes).toBe(0);
  await page.getByLabel("Unit", { exact: true }).selectOption("kg");
  await expect(quantity).toHaveAttribute("aria-invalid", "false");
  await page.getByRole("button", { name: "Add ingredient", exact: true }).click();
  await expect(page.getByRole("button", { name: "Remove rice", exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Edit quantity for rice", exact: true }).click();
  await quantity.fill("-1");
  await page.getByRole("button", { name: "Save quantity", exact: true }).click();
  await expect(quantity).toBeFocused();
  await expect(quantity).toHaveAccessibleDescription(/positive quantity/i);
  expect(writes).toBe(1);
});
