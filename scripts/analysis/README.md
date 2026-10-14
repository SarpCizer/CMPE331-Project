# Analysis diagram tools

These tools render documentation only and do not select the production frontend or backend stack.

1. Install the locked tools: `npm ci --prefix scripts/analysis --ignore-scripts`.
2. Run `node scripts/analysis/render.mjs` from any directory.
3. Run `python scripts/analysis/validate.py` from any directory.

Rendering uses a locally installed Edge/Chrome/Chromium in headless mode. Set `ANALYSIS_BROWSER` to its executable if it is not discovered, or run `npx --prefix scripts/analysis playwright install chromium`. Mermaid and Playwright are pinned in this folder's package lock. No remote renderer, CDN or AI provider receives the models.

Set `ANALYSIS_SCREENSHOTS` to a scratch directory to capture PNGs for visual review. Committed `.svg` diagrams are regenerated from `.mmd` sources. Markdown model files contain the same source for GitHub's native rendering. If a source changes, update its Markdown block and regenerate the SVG before committing. The validator detects differences between Markdown and source, checks every story/criterion mapping and local documentation links, and checks expected model coverage.

Open `docs/analysis/frontend/index.html` directly for the local mockup, or serve that folder with `python -m http.server 8766 --bind 127.0.0.1`. No backend, account credentials or network access is required for the mockup. See its own README for design and state coverage.
