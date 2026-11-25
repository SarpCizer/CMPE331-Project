# Analysis revision validation

Revision: 17 October 2026. Requirements baseline: approved `4839cdf`, merged to main as `d9178ed`. This record concerns the analysis revision, not implemented application behavior.

## Structural and semantic checks

- Retain all 15 stories and all 48 exact criterion texts; primary and supporting mappings link the transformations that realize each criterion.
- Validate 17 DFD sources: only external entities, processes and stores; each edge touches a process; each process has input and output; no yes/no control-flow labels; context/level-1 external groups balance.
- Retain ten E-R entities and use ordered preference keys so saved values/order/repeats are not silently collapsed.
- Check 19 source/SVG hashes, DFD parallel-line store symbols, model/source prose consistency and local documentation links.
- Confirm the report embeds all 19 analysis diagrams, with no obsolete activity/sequence figures.
- Independently audit complete recipe response data, ownership of URL/body references, missing versus foreign deletion outcomes, no inventory deduction, favorite/history independence and detail/history process responsibilities.
- Exported a 26-page review PDF: seven A4 text pages, eighteen A3 diagram sheets and one A1 level-1 overview sheet. All 19 analysis diagrams are embedded once, with pixels checked against the current rendered sources.
- Visually inspected every page for clipping, overlap, legibility, figure titles and footers. Corrected the authorization diagram's label spacing and the US-04 heading/list page break. A final raster comparison confirmed pages 1-25 unchanged after the last diagram correction; page 26 was inspected again.
- Checked all 62 unique PDF link destinations: 59 resolve to existing repository files on analysis_work; three refer to the approved requirements revision and review pages. Page numbering and review-copy status were checked on every page. GitHub file links require access to the private repository.

## Existing frontend baseline

The unchanged prototype was checked on 14 October at 360, 768 and 1440 px across five routes, including selected interactions and mobile modal/keyboard checks. Those results are retained as historical prototype evidence. This revision does not rerun or reinterpret them as backend, authentication, AI filtering, persistence, timing, deployment or accessibility certification. The [frontend guide](frontend/README.md) states the limitations.

## Reproduction and limits

Follow [analysis tooling](../../scripts/analysis/README.md). The validator checks DFD structure and traceability; the renderer/exporter produces all embedded figures. Structural checks do not prove semantic completeness automatically, so independent and reviewer audits remain necessary. No production services, real users, database migrations or application tests are changed. Review proposals A-01 through A-06 remain open.
