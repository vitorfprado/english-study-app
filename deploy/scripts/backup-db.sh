#!/usr/bin/env sh
set -eu

TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP_DIR="${BACKUP_DIR:-./backups}"
BACKUP_FILE="$BACKUP_DIR/db-$TIMESTAMP.sql.gz"

mkdir -p "$BACKUP_DIR"

docker exec english-study-postgres pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" | gzip > "$BACKUP_FILE"

if [ -n "${S3_BACKUP_BUCKET:-}" ]; then
  aws s3 cp "$BACKUP_FILE" "s3://$S3_BACKUP_BUCKET/"
fi

echo "Backup criado: $BACKUP_FILE"
