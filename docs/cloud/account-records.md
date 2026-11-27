# Account records and password warning

The existing FREE Render PostgreSQL instance is **fridgely-postgres** in the team
workspace. The web service uses its private DATABASE_URL. Opening the website
does not collect a visitor's email. Registration stores a normalized email,
account ID, creation time, Argon2id password hash and session-revocation version
in `accounts`. Passwords cannot be read back. Users see their own account context;
there is no public user-directory API or user-list page.

Authorized administrators: open Render Dashboard, select **fridgely-postgres**,
then **Connect**, and use its connection method in psql, DBeaver or a PostgreSQL
client. External clients need TLS and an allowed source IP; do not open access to
all IPs. Keep connection strings outside chat, Git and browser code.
[Render connection guide](https://render.com/docs/postgresql-creating-connecting).

A read-only query that omits password hashes and session information:

```sql
BEGIN READ ONLY;
SELECT email, created_at FROM accounts ORDER BY created_at DESC;
COMMIT;
```

`@example.test` rows are synthetic verification accounts, not actual customer
registrations. Keep access and exports within the authorized project team.
Signing in with an existing account does not create another email record.

## Chrome password warning

The screenshot shows Google Password Manager's compromised-password warning.
It reports a known compromised credential match; by itself it does not establish
that Fridgely's database was breached.
[Google explanation](https://support.google.com/chrome/answer/10311524?hl=en).
The website cannot safely dismiss or disable this browser protection.

Use **Preferences > Change your password**. Enter the current password, a new
unique password of at least 12 characters, and confirmation. Successful rotation
invalidates earlier sessions, keeps kitchen data and asks the user to sign in
again. Update Chrome's saved password when prompted. Change that exposed
password anywhere else it was reused. Never share the new password in chat.
Existing accounts and version-zero tokens survive migration; rotation increments
the version and revokes earlier tokens.
