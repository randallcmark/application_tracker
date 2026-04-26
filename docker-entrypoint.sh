#!/bin/sh
set -eu

if [ "${AUTO_MIGRATE:-1}" != "0" ]; then
  echo "Running database migrations"
  alembic upgrade head
fi

exec "$@"
