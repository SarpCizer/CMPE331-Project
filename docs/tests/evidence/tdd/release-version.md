# Source ZIP version provenance

Refs #16, #67, #103. The final packaging review found a hard-coded `0.1.0`
manifest despite both components identifying `0.6.0`. This did not change source
bytes, but it mislabelled the final package's application version.

Before changing the packager, two regressions failed against implementation
`3d0eacbde2c66ca13d96a7d622398b2d0f794993` in 1.414 seconds: a requested
committed 0.6.0 source was labelled 0.1.0, and conflicting committed frontend /
backend versions did not stop publication. The tests also leave working files
at 0.7.0 to prove that the selected Git commit, not the checkout, determines the
manifest version. The test-first commit precedes the production fix.

The frozen approved source `a59556e` has matching 0.1.0 component metadata.
Its source, branch, tag, files and published ZIP/PDF remain unchanged.

After the version is read from those Git blobs, all ten archive regressions
complete with nine passes and one explicit Windows symlink-privilege skip
(5.486 seconds). The two previously failing cases pass. The Linux CI job must
execute the symlink case as well; its result is not inferred from this local run.
