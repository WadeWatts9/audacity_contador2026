#!/usr/bin/env bash
set -e

BACKUP_DIR="${1:-./backups}"
mkdir -p "$BACKUP_DIR"

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/audacity_backup_${TIMESTAMP}.sql"

echo "Iniciando respaldo de base de datos Audacity..."
docker compose exec -T db pg_dump -U audacity_user -d audacity_db > "$BACKUP_FILE"

echo "Respaldo completado exitosamente en: $BACKUP_FILE"
ls -lh "$BACKUP_FILE"
