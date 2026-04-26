#!/usr/bin/env sh
set -eu

if [ -z "${1:-}" ]; then
  echo "Uso: ./restore-db.sh <arquivo-local.sql.gz | s3://bucket/arquivo.sql.gz>"
  exit 1
fi

SOURCE="$1"
TEMP_FILE="/tmp/restore-db.sql.gz"

if echo "$SOURCE" | grep -q "^s3://"; then
  aws s3 cp "$SOURCE" "$TEMP_FILE"
  SOURCE="$TEMP_FILE"
fi

gunzip -c "$SOURCE" | docker exec -i english-study-postgres psql -U "$POSTGRES_USER" "$POSTGRES_DB"
echo "Restore concluido."
