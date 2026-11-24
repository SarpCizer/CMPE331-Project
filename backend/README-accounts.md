# Accounts, preferences and shared database - Berfin

This feature adds the real account/JWT and SQL persistence foundations required by
the current FastAPI backend. It builds on `backend_work` without replacing Sarp's
collections module. Recipe and web composition follow in dependent PRs.

## Behavior

- `POST /accounts`: normalized unique email, password of 8-1024 characters,
  salted Argon2id hash, atomic account/profile insert; public `{id,email}` only.
- `POST /sessions`: generic 401 for invalid credentials; signed HS256 JWT with
  required subject, issuer, audience, issued-at and finite expiry. Algorithm and
  signature are verified; identity comes solely from the verified JWT and an
  existing account. The injected server clock also checks expiry.
- `GET/PUT /profile/preferences`: authenticated, atomic replacement of ordered
  dietary/allergen arrays, including clearing with empty arrays.
- `GET/POST /inventory`, `DELETE /inventory/{id}`: authenticated, owner-qualified
  persistence of names and immutable UTC addition timestamps. Repeated names are
  allowed. Names are validated using the existing backend naming rules.
- Validation returns 400; invalid authentication 401; duplicate email 409;
  nonexistent/foreign resources 404; storage errors are sanitized.

## Install and migrate

Use Python 3.12 and a virtual environment. From the repository root:

```bash
python -m pip install -r backend/requirements-app.lock
python -m pip install --no-deps -e backend
export DATABASE_URL='sqlite:///./fridgely.db'
python -m fridgely_app migrate
python -m pytest backend/tests/test_accounts_database.py
```

For PostgreSQL, set `DATABASE_URL` to the managed connection string outside source
control. `postgres://` and `postgresql://` URLs select psycopg automatically. For
public-network database connections, configure the provider's required TLS policy
in the connection URL. Migration and runtime roles may be separated at deployment.
Never print or commit the connection string.

Migrations run explicitly before startup; importing the package creates no schema
or default user. Revision `0001_owned_schema` creates accounts, preferences,
inventory, recipes/ordered children and collections. It is intended for a new
Fridgely database. Revision `0002_ordered_preferences` then migrates the initial
JSON arrays to ordered dietary/allergen rows without changing their API values.
An already-populated unrelated legacy ZIP database is not migrated or
reset: use a separate database and plan an explicit reviewed import if needed.

The shared migration preserves the existing feature table/column names. It adds
account foreign keys and composite `(owner_id,recipe_id)` references to recipes.
The same physical SQL schema supports the existing feature models without
modifying their separate SQLAlchemy metadata. SQLite foreign-key enforcement is
enabled on every host connection; PostgreSQL enforces these constraints natively.

Ordered `dietary_preferences` and `allergen_exclusions` rows are keyed by owner
and position. They preserve exact saved strings, ordering and repeated values;
both lists are replaced in one transaction. The migrated profile has no JSON
shadow columns. See [the current database contract](../docs/database.md).
FastAPI/SQLAlchemy is retained to integrate the
implemented teammate modules, rather than introducing a second Express service.

The tests cover invalid/duplicate registration and distinct salted hashes.
They verify rejected passwords, required JWT claims, signatures and expiry, atomic preferences, owner
isolation, SQL metacharacters, foreign keys, repeat migration and reopening the
same database through a fresh application host. The PostgreSQL integration job
in the test PR supplements the SQLite runs; SQLite results alone do not establish
PostgreSQL behavior.
