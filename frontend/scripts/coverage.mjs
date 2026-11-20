import fs from "node:fs/promises";
import path from "node:path";
import v8toIstanbul from "v8-to-istanbul";
import libCoverage from "istanbul-lib-coverage";
import libReport from "istanbul-lib-report";
import reports from "istanbul-reports";

const root = path.resolve(import.meta.dirname, "..");
const input = path.resolve(root, "../test-results/browser-v8");
const output = path.resolve(root, "../test-results/frontend-coverage");
const merged = libCoverage.createCoverageMap({});
for (const file of await fs.readdir(input)) {
  for (const entry of JSON.parse(
    await fs.readFile(path.join(input, file), "utf8"),
  )) {
    if (!entry.url.includes("/assets/") || !entry.url.endsWith(".js")) continue;
    const asset = path.join(
      root,
      "dist/assets",
      path.basename(new URL(entry.url).pathname),
    );
    const converter = v8toIstanbul(asset, 0, { source: entry.source });
    await converter.load();
    converter.applyCoverage(entry.functions);
    for (const [source, coverage] of Object.entries(converter.toIstanbul())) {
      if (source.startsWith(path.join(root, "src") + path.sep))
        merged.addFileCoverage(coverage);
    }
  }
}
if (!merged.files().length)
  throw new Error("No application coverage was collected");
const context = libReport.createContext({ dir: output, coverageMap: merged });
for (const format of ["lcovonly", "json-summary", "text-summary"])
  reports.create(format).execute(context);
console.log(`Frontend coverage reports: ${output}`);
