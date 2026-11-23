# Final source delivery and owner actions

Refs #16, #22, #40, #47, #48. Build the source-only course archive from the exact final GitHub revision:

```sh
python scripts/release/package_source.py --revision FULL_GITHUB_SHA
```

The archive contains product source, tests, dependency definitions, Markdown/diagram sources and deployment definitions. It excludes installed libraries, virtual environments, build outputs, databases, real `.env` files, PDF reports, screenshots and raw runner evidence. A manifest records every included file hash and the declared source revision; a separate SHA-256 file verifies the ZIP. The full PDF with embedded screenshots and detailed evidence remains a separate reviewed deliverable in GitHub and for learn.bilgi. No archive is claimed submitted merely because it was built.

Use a real Git checkout with the complete reviewed commit and its blobs available
locally. An unknown commit or a folder copied without its Git history is rejected;
the command does not fetch objects or stamp a remote SHA onto local files. It reads
the declared tree and regular blobs through `git ls-tree`/`git cat-file`, preserving
their exact bytes even if HEAD differs or the working directory is dirty. Untracked
files, local edits, tracked symlinks and submodules cannot enter the archive. Output
paths cannot overwrite tracked source or Git metadata.

Entries use sorted paths, a fixed 1980 ZIP timestamp and committed Git executable
modes. Two builds of the same revision with the same Python/zlib toolchain must
have identical ZIP bytes and SHA-256; the manifest also records each Git mode.
The dedicated CI archive job exercises seven isolated Git-fixture cases and builds
the actual checked-out commit twice before uploading the archive/checksum evidence.
It is an archive-verification artifact for that PR head, not a final submission.

```sh
python -B -m unittest discover -s scripts/release -p test_package_source.py -v
```

The #53 review correction and actual failing/passing evidence are recorded in
[the archive review evidence](tests/release-package-review.md). Integrate this
reviewed correction through the agreed PR stack before building the final team
candidate. Previously generated working-directory ZIPs are not a final source
freeze for a different commit.

Repository-owner actions: grant Render GitHub access for the private project or an authorized private fork; enable/verify main protection; obtain the team's real independent reviews; apply the agreed integration plan; create the first version tag on the approved commit. Preserve the open teammate PRs until the team resolves their overlap.

Team/account actions: provide the provider credential directly in the host's secret environment; record live HTTPS/provider and deployment performance checks; confirm the project contact and GitHub Project board; ensure all six members contribute genuinely; rehearse the walkthrough; upload the approved PDF and final source ZIP through the authorized learn.bilgi account and verify receipt.

The assistant cannot manufacture another person's contribution/review or enable settings without owner access. These actions remain visible in the review-evidence index instead of being checked off speculatively. The updated test-plan email sets PR review on 25 November and approved PDF on 29 November; work should be prepared earlier. Final source delivery is 30 November 2026 in the syllabus.
