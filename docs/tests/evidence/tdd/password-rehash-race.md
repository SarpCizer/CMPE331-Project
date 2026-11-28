# Password rotation / transparent rehash regression

Refs #16, #40, #67, #99. Added with Codex assistance under Sarp's final-release
instruction. The application source before the fix is
`abdca3f5b2e58d7842dacbe83a4c5d2722c13d3a`.

The real sign-in route loads an older Argon2 hash, verifies the password and
pauses immediately before its transparent rehash. A concurrent authenticated
password change commits successfully (204). Resuming the sign-in must not
overwrite the replacement password with a hash of the original password.

Before production code changed, the new SQLite regression failed with:

```text
AssertionError: Concurrent sign-in reverted the successfully changed password
1 failed, 1 passed, 2 skipped in 1.65s
```

The passing control overlaps two legitimate rehashes of the same unchanged
password and requires both returned sessions to remain usable. The two skipped
parameters require an isolated PostgreSQL TEST_DATABASE_URL; they are not
counted as passing local database verification. The integrated CI supplies that
database and must execute both variants before release.

The tests use only random synthetic accounts and temporary/isolated databases.
They verify saved password state, token revocation and preserved owned inventory;
they do not use a live account, provider credential or real AI call. The test
commit is retained separately from the implementation.

The retained red commit is `03d0f3d` (resolve the full commit in the branch
history). The conditional hash/version update and conflict re-verification pass
the two SQLite interleaving cases plus the existing account, password-rotation
and throttle cases: **44 passed, 2 PostgreSQL parameters skipped in 11.92s**.
The seeded mutation campaign adds M27, which removes this conditional update;
the new race test must detect that regression in CI. These local results do not
replace the required PostgreSQL or full integrated CI run.
