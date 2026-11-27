import { test, expect } from "./fixtures.js";

for (const width of [360, 1440]) {
  test(`password rotation keeps kitchen data and rejects old credentials at ${width}px`, async ({ page }) => {
    await page.setViewportSize({ width, height: 900 });
    const email = `rotation-${crypto.randomUUID()}@example.test`;
    const original = "Synthetic-Original-Password!42";
    const replacement = "Synthetic-Replacement-Password!73";
    await page.goto("/");
    await page.getByRole("button", { name: "Create an account", exact: true }).click();
    await page.getByLabel("Email address").fill(email);
    await page.getByLabel("Password", { exact: true }).fill(original);
    await page.getByRole("button", { name: "Create account", exact: true }).click();
    await page.getByLabel("Add an ingredient", { exact: true }).fill("rice");
    await page.getByRole("button", { name: "Add ingredient", exact: true }).click();
    await expect(page.getByRole("button", { name: "Remove rice", exact: true })).toBeVisible();
    await page.getByRole("button", { name: "Sign out", exact: true }).click();
    await page.getByLabel("Email address").fill(email);
    await page.getByLabel("Password", { exact: true }).fill(original);
    await page.getByRole("button", { name: "Sign in", exact: true }).click();
    await expect(page.getByRole("button", { name: "Remove rice", exact: true })).toBeVisible();
    await page.getByRole("link", { name: "Preferences", exact: true }).click();
    await page.getByLabel("Current password", { exact: true }).fill("wrong");
    await page.getByLabel("New password", { exact: true }).fill(replacement);
    await page.getByLabel("Confirm new password").fill("mismatch");
    await page.getByRole("button", { name: "Change password", exact: true }).click();
    await expect(page.getByLabel("Confirm new password")).toHaveAccessibleDescription(/do not match/i);
    await page.getByLabel("Confirm new password").fill(replacement);
    await page.getByRole("button", { name: "Change password", exact: true }).click();
    await expect(page.getByLabel("Current password", { exact: true })).toHaveAccessibleDescription(/check your current password/i);
    await page.getByLabel("Current password", { exact: true }).fill(original);
    await page.getByRole("button", { name: "Change password", exact: true }).click();
    await expect(page.getByText("Password changed. Sign in with your new password.", { exact: true })).toBeVisible();
    await page.getByLabel("Email address").fill(email);
    await page.getByLabel("Password", { exact: true }).fill(original);
    await page.getByRole("button", { name: "Sign in", exact: true }).click();
    await expect(page.getByText("Email or password is incorrect. Please try again.")).toBeVisible();
    await page.getByLabel("Password", { exact: true }).fill(replacement);
    await page.getByRole("button", { name: "Sign in", exact: true }).click();
    await page.getByRole("link", { name: "My fridge", exact: false }).click();
    await expect(page.getByRole("button", { name: "Remove rice", exact: true })).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  });
}
