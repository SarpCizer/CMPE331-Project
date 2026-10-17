# Analysis diagram tools

These tools render documentation only and do not select the production frontend or backend stack.

1. Install the locked tools: `npm ci --prefix scripts/analysis --ignore-scripts`.
2. Run `node scripts/analysis/render.mjs` from any directory.
3. Run `python scripts/analysis/validate.py` from any directory.

Rendering uses a locally installed Edge/Chrome/Chromium in headless mode. Set `ANALYSIS_BROWSER` to its executable if it is not discovered, or run `npx --prefix scripts/analysis playwright install chromium`. Mermaid and Playwright are pinned in this folder's package lock. No remote renderer, CDN or AI provider receives the models.

Set `ANALYSIS_SCREENSHOTS` to a scratch directory to capture PNGs for visual review. Committed SVG data models are regenerated from .mmd sources. Behavioral diagrams use typed .dfd.json sources: circles are processes, rectangles external entities and parallel lines persistent stores. Mermaid supplies layout; the renderer draws the DFD store symbols. Model Markdown files document the same data flows and constraints. Update source/prose and regenerate images together. The validator checks data-model blocks, DFD structure, process inputs/outputs, external-interface balancing, all criterion mappings and links, and complete report figure coverage.

Open `docs/analysis/frontend/index.html` directly for the local mockup, or serve that folder with `python -m http.server 8766 --bind 127.0.0.1`. No backend, account credentials or network access is required for the mockup. See its own README for design and state coverage.

Export the complete review report with `python scripts/analysis/export_pdf.py --diagram-dir <rendered-png-directory> --output <report.pdf>`. Python packages `reportlab` and `Pillow` are required. Each SVG must have a matching PNG basename in the supplied directory; local PNG mockups are embedded directly. The exporter retains report prose and tables, gives each figure a separate landscape sheet, and converts relative links to their source paths on GitHub's `analysis_work` branch. Standard figures use A3; the dense `level-1-dfd.svg` overview uses A1 for readable labels. The `--overview-paper A1|A2|A3` option changes only that overview sheet. Text pages use portrait A4, tables repeat their headers, and every page carries a revision date, review-copy status and total page count. Use `--date` to set the displayed revision date; export does not imply approval. Render and visually inspect every exported page before delivery.
