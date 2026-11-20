#!/bin/sh
set -eu
: "${DATABASE_URL:?Set DATABASE_URL to the managed PostgreSQL connection string}"
: "${JWT_SECRET:?Set a persistent JWT_SECRET of at least 32 bytes}"
python -m fridgely_app migrate
exec python -m uvicorn fridgely_app.host:create_app --factory --host 0.0.0.0 --port "${PORT:-10000}" --workers 1 --no-access-log
