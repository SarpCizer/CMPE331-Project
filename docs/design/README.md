# Fridgely design package

## Current implementation

Read [the source-pinned alignment addendum](current/implementation-alignment.md) ([five-page PDF](current/implementation-alignment.pdf)) for the FastAPI, React, PostgreSQL and Cloudflare implementation inspected at `c67165407e71ee584a8fcfdf2d0a925fd42a2a42`.

[The manifest](current/source-manifest.json) records the inspected application file identities, original design blobs, CI provenance and the sanitized [33-check deployed-source result](current/live-verification-2026-11-25.json). The live result predates this documentation update; exporting the addendum does not call a provider.

To regenerate both addendum formats from the repository root, install the existing `scripts/tests/requirements-report.txt` dependencies and run `python scripts/design/export_alignment.py`. Content is in [alignment.json](current/alignment.json); editable Mermaid diagrams are included in the Markdown. ReportLab creates the simplified PDF diagrams.

## Historical design baseline

The [14 November report](../software-design-report.md) and [original PDF](../software-design-report.pdf) describe the design-stage Express proposal and its 13 editable [PlantUML models](arch/component.puml). All original model, rendered PNG and PDF blobs are retained unchanged from `02a7d3b6`. The current addendum identifies implementation deviations rather than silently relabelling those historical figures.

The design covers the approved 15 stories. Yeşim's changes-requested review is still a review decision, not an approval; follow-up corrections and their commits are explained in the addendum and PR #6. A teammate must independently review the updated head before integration.

Refs #6, #16, #24. The approved `a59556e` course ZIP/PDF pair is preserved separately; this design follow-up makes no final submission-source decision.
