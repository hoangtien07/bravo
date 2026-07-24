#!/usr/bin/env bash
# Read-only validation of one BRAVO backup set before an isolated restore drill.
# Usage: scripts/verify_backup_artifact.sh /var/backups/bravo 20260724_020000
set -euo pipefail

if [ "$#" -ne 2 ]; then
  echo "usage: $0 BACKUP_DIRECTORY TIMESTAMP" >&2
  exit 64
fi

DEST="$1"
TS="$2"
DB="$DEST/db_$TS.dump"
UPLOADS="$DEST/uploads_$TS.tgz"
PRIVATE="$DEST/private_$TS.tgz"

for artifact in "$DB" "$UPLOADS" "$PRIVATE"; do
  if [ ! -f "$artifact" ]; then
    echo "missing required backup artifact: $artifact" >&2
    exit 1
  fi
done

pg_restore --list "$DB" >/dev/null
tar tzf "$UPLOADS" >/dev/null
tar tzf "$PRIVATE" >/dev/null
echo "backup set $TS passed read-only integrity checks"
