# Committed report evidence regression (#67 / #16)

The clean-checkout report job in run 45922968619 failed at source
`0ccb6ea6e11af2e4d724ba01b49e5cf94e70ae57`: the broad `coverage/` ignore
pattern omitted two retained coverage-policy JSON files. They existed locally,
so a report test copying local documents could not detect the omission.

Before adding those files, the new
`EvidenceCheckoutTests.test_every_indexed_follow_up_file_is_retained_in_the_commit`
failed against that source with:

```text
AssertionError: 128 != 0 : Indexed evidence absent from committed source:
docs/tests/evidence/review94-fafd3fd/coverage/coverage-gate-canary.json
```

The test reads every indexed artifact from the actual `HEAD` Git blob and
checks its byte length and SHA-256, independently of local ignored files.
The following fix retains only the two declared, non-secret coverage exports
through a narrowly scoped ignore exception. It does not alter their raw bytes
or reduce the report's hash/source validation.
