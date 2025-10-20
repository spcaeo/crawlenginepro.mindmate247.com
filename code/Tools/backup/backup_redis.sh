#!/bin/bash
# Redis Backup Script
# Usage: ./backup_redis.sh

set -e

BACKUP_DIR="${BACKUP_DIR:-$HOME/backups/redis}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="redis_backup_${TIMESTAMP}.rdb"

echo "========================================="
echo "Redis Backup Script"
echo "========================================="
echo "Backup directory: $BACKUP_DIR"
echo "Backup file: $BACKUP_FILE"
echo ""

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

echo "[1/3] Triggering Redis background save..."
docker exec rag-redis redis-cli BGSAVE

echo "[2/3] Waiting for save to complete..."
sleep 3

echo "[3/3] Copying RDB file..."
docker cp rag-redis:/data/dump.rdb "$BACKUP_DIR/$BACKUP_FILE" || {
    echo "Error: Failed to copy RDB file"
    exit 1
}

echo ""
echo "========================================="
echo "Backup Complete!"
echo "========================================="
echo "Backup file: $BACKUP_DIR/$BACKUP_FILE"
ls -lh "$BACKUP_DIR/$BACKUP_FILE"
echo ""

# Clean up old backups (keep last 7 days)
echo "Cleaning up old backups (keeping last 7 days)..."
find "$BACKUP_DIR" -name "redis_backup_*.rdb" -mtime +7 -delete
echo "Done!"
