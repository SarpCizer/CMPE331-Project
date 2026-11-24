import { rm } from "node:fs/promises";
import path from "node:path";

export default async function () {
  await rm(path.resolve(import.meta.dirname, "../../test-results/browser-v8"), {
    recursive: true,
    force: true,
  });
}
