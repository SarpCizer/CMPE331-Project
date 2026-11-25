# Final source delivery

Refs #16, #22, #40, #47, #48.

## Approved course files

The team's approved course source is `a59556e366ffd65adf799bb8aa9bc47e95dea16e`.
[Sarp reaffirmed İrem's approval](https://github.com/SarpCizer/CMPE331-Project/issues/24#issuecomment-7159653107),
and the annotated [v0.1.0 tag](https://github.com/SarpCizer/CMPE331-Project/tree/v0.1.0)
points to that commit. Use the files in the
[approved delivery folder](https://github.com/SarpCizer/CMPE331-Project/tree/delivery/irem-approved-a59556e/delivery):

- `Fridgely-source-0.1.0.zip` and its SHA-256 sidecar.
- `Fridgely-Software-Test-Report.pdf` and its SHA-256 sidecar.

[CI 45474025963](https://github.com/SarpCizer/CMPE331-Project/actions/runs/45474025963)
passed seven jobs for that source, including 133 backend/PostgreSQL, 28
acceptance and 22 browser tests. The ZIP preserves the committed Markdown and
README from that revision, including the older report for `25c111a`. For the
tested submission source, use the companion PDF and the [matching Markdown
report](tests/software-test-report.md) reviewed in
[#67](https://github.com/SarpCizer/CMPE331-Project/pull/67). The later [design
addendum](design/current/implementation-alignment.md) is available in the
repository. Use the isolated, controlled-provider tests described in the
[root README](../README.md#verify) to verify the frozen archive's flows without
a provider credential or model charge.

## Live demo

The [free Render application](https://fridgely-web.onrender.com) deploys reviewed
`main`. The
[verification in #40](https://github.com/SarpCizer/CMPE331-Project/issues/40#issuecomment-7159892391)
identifies deployed `32bf77578564cc57b243b7953c655e2597c3182b` with the
Cloudflare adapter, which was added after the course source.
[CI 45594103954](https://github.com/SarpCizer/CMPE331-Project/actions/runs/45594103954)
recorded 471 backend/PostgreSQL, 28 acceptance and 22 browser tests at that
revision. Cite the exact demo source and its evidence during the walkthrough.

The [team rehearsal and BİLGİ Learn confirmation](https://github.com/SarpCizer/CMPE331-Project/issues/48)
require records of the actual rehearsal and submission.

## Rebuilding for a reviewed source

Build a source-only archive from the exact Git revision under review:

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

The archive review and regression evidence are recorded in
[the archive review evidence](tests/release-package-review.md) and
[#66](https://github.com/SarpCizer/CMPE331-Project/pull/66). A different
submission revision requires a source decision and its own ZIP, checksums,
test evidence and matching report.
