#!/bin/bash
# Boot: embedded PostgreSQL (unless SKIP_EMBEDDED_PG=1 for compose's split mode),
# apply schema+seed (idempotent), then launch the API server.
set -e

SOCKET=/var/run/postgresql

if [ "${SKIP_EMBEDDED_PG:-0}" != "1" ]; then
  export PGDATA=/var/lib/postgresql/data
  if [ ! -s "$PGDATA/PG_VERSION" ]; then
    echo "==> Initializing PostgreSQL cluster..."
    su postgres -c "/usr/lib/postgresql/*/bin/initdb -D $PGDATA --auth-local=trust --auth-host=scram-sha-256 -E UTF8" >/dev/null
  fi
  echo "==> Starting PostgreSQL..."
  su postgres -c "pg_ctl -D $PGDATA -o '-c listen_addresses=localhost -c unix_socket_directories=$SOCKET' -w -t 60 start"
  echo "==> Creating role & database (idempotent)..."
  su postgres -c "psql -h $SOCKET -d postgres -q -c \"DO \\$\\$ BEGIN IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname='bank') THEN CREATE ROLE bank LOGIN PASSWORD 'bank'; END IF; END \\$\\$;\""
  su postgres -c "psql -h $SOCKET -d postgres -q -tc \"SELECT 1 FROM pg_database WHERE datname='fictional_bank'\" | grep -q 1 || createdb -h $SOCKET -O bank fictional_bank"
else
  echo "==> Waiting for external PostgreSQL at DATABASE_URL..."
  for i in $(seq 1 60); do
    pg_isready -d "${DATABASE_URL}" >/dev/null 2>&1 && break
    sleep 1
  done
fi

echo "==> Applying schema + seed..."
psql "${DATABASE_URL}" -v ON_ERROR_STOP=1 -q -f /srv/database/schema.sql
psql "${DATABASE_URL}" -v ON_ERROR_STOP=1 -q -f /srv/database/seed.sql

echo "==> Starting FastAPI on :${PORT:-8000}..."
cd /srv/backend
exec python -m uvicorn main:app --host 0.0.0.0 --port "${PORT:-8000}"
