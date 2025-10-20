#!/bin/bash
# PostgreSQL Backup Script
# Usage: ./backup_postgres.sh

set -e

BACKUP_DIR="${BACKUP_DIR:-$HOME/backups/postgres}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="postgres_backup_${TIMESTAMP}.sql"
COMPRESSED_FILE="${BACKUP_FILE}.gz"

echo "========================================="
echo "PostgreSQL Backup Script"
echo "========================================="
echo "Backup directory: $BACKUP_DIR"
echo "Backup file: $COMPRESSED_FILE"
echo ""

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

echo "[1/3] Dumping PostgreSQL database..."
docker exec rag-postgres pg_dump -U rag_user rag_metadata > "$BACKUP_DIR/$BACKUP_FILE" || {
    echo "Error: Database dump failed"
    exit 1
}

echo "[2/3] Compressing backup..."
gzip "$BACKUP_DIR/$BACKUP_FILE"

echo "[3/3] Verifying backup..."
if [ -f "$BACKUP_DIR/$COMPRESSED_FILE" ]; then
    echo "Backup created successfully!"
else
    echo "Error: Backup file not found"
    exit 1
fi

echo ""
echo "========================================="
echo "Backup Complete!"
echo "========================================="
echo "Backup file: $BACKUP_DIR/$COMPRESSED_FILE"
ls -lh "$BACKUP_DIR/$COMPRESSED_FILE"
echo ""

# Clean up old backups (keep last 14 days)
echo "Cleaning up old backups (keeping last 14 days)..."
find "$BACKUP_DIR" -name "postgres_backup_*.sql.gz" -mtime +14 -delete
echo "Done!"
