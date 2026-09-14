#!/usr/bin/env bash
set -e

BACKUP_FILE="$1"
if [ -z "$BACKUP_FILE" ]; then
    echo "Uso: ./scripts/restore.sh <ruta_archivo_backup.sql>"
    exit 1
fi

if [ ! -f "$BACKUP_FILE" ]; then
    echo "Error: Archivo no encontrado: $BACKUP_FILE"
    exit 1
fi

echo "ADVERTENCIA: Esto restaurará la base de datos Audacity desde: $BACKUP_FILE"
read -p "¿Continuar? (s/n): " confirm
if [ "$confirm" != "s" ]; then
    echo "Operación cancelada."
    exit 0
fi

echo "Restaurando base de datos..."
cat "$BACKUP_FILE" | docker compose exec -T db psql -U audacity_user -d audacity_db

echo "Restauración completada exitosamente."
