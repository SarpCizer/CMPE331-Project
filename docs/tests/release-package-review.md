# PR #53 archive review correction

Refs #16, #47, #48. Irem's changes-requested review at
[review 6023490951](https://github.com/SarpCizer/CMPE331-Project/pull/53#pullrequestreview-6023490951)
identified two reproduced release defects at `db52aff3b0cc567730f4b86b850c7d04a07591fd`:
the ZIP read the working directory instead of the declared commit, and repeated
builds used different timestamps and therefore different bytes.

## Executed test-first evidence

Test-only commit `802c4a32c242f04fc9cc6ad21ee73be190c8e1aa` adds seven real temporary
Git-repository tests without changing the implementation. On the unchanged
`db52aff` packager, six fail and the existing release-filter case passes. The raw
[RED log](evidence/release-package/red.log) is retained. The fixed implementation
passes all seven cases; see the [GREEN log](evidence/release-package/green.log)
and [source hashes](evidence/release-package/source-manifest.json).

The cases cover a dirty working tree with untracked files and a different HEAD,
files absent from the working tree but present in the requested commit, unknown
commits, a folder without its own Git checkout, tracked symlinks, source-output
collision, generated-data exclusions, repeat digests and normalized modes/times.
All accounts, repositories and file payloads are disposable fixtures. No existing
application database, teammate branch or main ref is changed by the tests.

## Resulting behavior and CI

The packager validates the exact commit and reads only regular blobs from its
tree. It preserves original bytes and Git executable modes, omits symlinks and
gitlinks, and normalizes ZIP metadata. The source selection never reads local
file contents. It refuses an unknown revision instead of labelling another tree
with that SHA. The CLI still exports the per-file manifest and ZIP checksum.

A dedicated standard-library CI job runs the regressions, packages the actual PR
head twice and requires byte equality before exporting the artifact. Application
source/test/image checks remain separate; this correction does not claim that a
new final application candidate has already been integrated or uploaded to the
course platform. The PR's final checks and Irem's re-review determine acceptance;
the author does not dismiss or replace the reviewer's changes-requested decision.
