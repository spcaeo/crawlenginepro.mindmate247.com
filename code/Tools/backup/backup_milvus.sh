#!/bin/bash
# Milvus Data Backup Script
# Usage: ./backup_milvus.sh

set -e

BACKUP_DIR="${BACKUP_DIR:-$HOME/backups/milvus}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="milvus_backup_${TIMESTAMP}.tar.gz"

echo "========================================="
echo "Milvus Backup Script"
echo "========================================="
echo "Backup directory: $BACKUP_DIR"
echo "Backup file: $BACKUP_FILE"
echo ""

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

echo "[1/4] Stopping Milvus to ensure data consistency..."
docker stop milvus-standalone || {
    echo "Error: Failed to stop Milvus"
    exit 1
}

echo "[2/4] Creating volume backup..."
docker run --rm \
    -v rag-services_milvus_data:/data \
    -v "$BACKUP_DIR":/backup \
    ubuntu \
    tar czf "/backup/$BACKUP_FILE" -C /data . || {
    echo "Error: Backup failed"
    docker start milvus-standalone
    exit 1
}

echo "[3/4] Restarting Milvus..."
docker start milvus-standalone

echo "[4/4] Waiting for Milvus to be healthy..."
sleep 5
for i in {1..30}; do
    if curl -s http://localhost:9091/healthz | grep -q "Healthy"; then
        echo "Milvus is healthy!"
        break
    fi
    echo "Waiting for Milvus... ($i/30)"
    sleep 2
done

echo ""
echo "========================================="
echo "Backup Complete!"
echo "========================================="
echo "Backup file: $BACKUP_DIR/$BACKUP_FILE"
ls -lh "$BACKUP_DIR/$BACKUP_FILE"
echo ""

# Clean up old backups (keep last 7 days)
echo "Cleaning up old backups (keeping last 7 days)..."
find "$BACKUP_DIR" -name "milvus_backup_*.tar.gz" -mtime +7 -delete
echo "Done!"
