import { test as base, expect } from "@playwright/test";
import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import { createHash } from "node:crypto";

export const test = base.extend({
  browserCoverage: [
    async ({ page }, use, testInfo) => {
      await page.coverage.startJSCoverage({ resetOnNavigation: false });
      await use();
      const coverage = await page.coverage.stopJSCoverage();
      const directory = path.resolve(
        import.meta.dirname,
        "../../test-results/browser-v8",
      );
      await mkdir(directory, { recursive: true });
      const id = createHash("sha256")
        .update(testInfo.testId)
        .digest("hex")
        .slice(0, 16);
      await writeFile(
        path.join(directory, `${id}.json`),
        JSON.stringify(coverage),
      );
    },
    { auto: true },
  ],
});
export { expect };
