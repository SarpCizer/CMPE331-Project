import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests",
  globalSetup: "./tests/global-setup.js",
  timeout: 45000,
  fullyParallel: false,
  workers: 1,
  reporter: [
    ["list"],
    ["junit", { outputFile: "../test-results/browser-junit.xml" }],
  ],
  use: {
    baseURL: process.env.WEB_BASE_URL || "http://127.0.0.1:8000",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    ...(process.env.PLAYWRIGHT_CHANNEL
      ? { channel: process.env.PLAYWRIGHT_CHANNEL }
      : {}),
  },
});
