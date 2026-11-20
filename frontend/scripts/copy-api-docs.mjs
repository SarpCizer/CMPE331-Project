import { copyFile, mkdir } from "node:fs/promises";
import { createRequire } from "node:module";
import path from "node:path";

const require = createRequire(import.meta.url);
const source = path.dirname(require.resolve("swagger-ui-dist/package.json"));
const target = path.resolve(import.meta.dirname, "../dist/api-docs");
await mkdir(target, { recursive: true });
for (const name of [
  "swagger-ui-bundle.js",
  "swagger-ui.css",
  "favicon-32x32.png",
]) {
  await copyFile(path.join(source, name), path.join(target, name));
}
