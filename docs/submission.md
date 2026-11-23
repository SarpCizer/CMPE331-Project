# Final source delivery and owner actions

Refs #16, #22, #40, #47, #48. Build the source-only course archive from a Git checkout containing the exact final GitHub revision:

```sh
python scripts/release/package_source.py --revision FULL_GITHUB_SHA
```

The builder reads regular files from the specified commit, even when the checkout is dirty or points at a different commit. ZIP timestamps and file modes come from fixed metadata and the committed modes, respectively. Rebuild with the same Python and compression versions to verify identical ZIP bytes. Run the packaging tests with `python scripts/release/test_package_source.py`.

The archive contains product source, tests, dependency definitions, Markdown/diagram sources and deployment definitions. It excludes installed libraries, virtual environments, build outputs, databases, real `.env` files, PDF reports, screenshots and raw runner evidence. A manifest records every included file hash and the declared source revision; a separate SHA-256 file verifies the ZIP. The full PDF with embedded screenshots and detailed evidence remains a separate reviewed deliverable in GitHub and for learn.bilgi. No archive is claimed submitted merely because it was built.

Repository-owner actions: grant Render GitHub access for the private project or an authorized private fork; enable/verify main protection; obtain the team's real independent reviews; apply the agreed integration plan; create the first version tag on the approved commit. Preserve the open teammate PRs until the team resolves their overlap.

Team/account actions: provide the provider credential directly in the host's secret environment; record live HTTPS/provider and deployment performance checks; confirm the project contact and GitHub Project board; ensure all six members contribute genuinely; rehearse the walkthrough; upload the approved PDF and final source ZIP through the authorized learn.bilgi account and verify receipt.

The assistant cannot manufacture another person's contribution/review or enable settings without owner access. These actions remain visible in the review-evidence index instead of being checked off speculatively. The updated test-plan email sets PR review on 25 November and approved PDF on 29 November; work should be prepared earlier. Final source delivery is 30 November 2026 in the syllabus.
