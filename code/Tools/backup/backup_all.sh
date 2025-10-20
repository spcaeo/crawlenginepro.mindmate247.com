#!/bin/bash
# Complete Infrastructure Backup Script
# Usage: ./backup_all.sh

set -e

BACKUP_ROOT="${BACKUP_ROOT:-$HOME/backups}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="$BACKUP_ROOT/full_backup_$TIMESTAMP"

echo "========================================="
echo "Complete Infrastructure Backup"
echo "========================================="
echo "Backup directory: $BACKUP_DIR"
echo ""

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup Milvus
echo "▶ Backing up Milvus..."
export BACKUP_DIR="$BACKUP_DIR/milvus"
./backup_milvus.sh || {
    echo "Error: Milvus backup failed"
    exit 1
}

# Backup PostgreSQL
echo ""
echo "▶ Backing up PostgreSQL..."
export BACKUP_DIR="$BACKUP_DIR/postgres"
./backup_postgres.sh || {
    echo "Error: PostgreSQL backup failed"
    exit 1
}

# Backup Redis
echo ""
echo "▶ Backing up Redis..."
export BACKUP_DIR="$BACKUP_DIR/redis"
./backup_redis.sh || {
    echo "Error: Redis backup failed"
    exit 1
}

# Backup docker-compose files
echo ""
echo "▶ Backing up Docker Compose files..."
mkdir -p "$BACKUP_DIR/docker-compose"
cp ~/backups/rag-services/docker-compose.yml "$BACKUP_DIR/docker-compose/rag-services-docker-compose.yml" 2>/dev/null || true
cp ~/apisix/docker-compose.yml "$BACKUP_DIR/docker-compose/apisix-docker-compose.yml" 2>/dev/null || true
echo "Docker Compose files backed up"

# Backup APISIX configuration
echo ""
echo "▶ Backing up APISIX configuration..."
mkdir -p "$BACKUP_DIR/apisix"
cp -r ~/apisix/apisix_conf "$BACKUP_DIR/apisix/" 2>/dev/null || true
cp -r ~/apisix/dashboard_conf "$BACKUP_DIR/apisix/" 2>/dev/null || true
echo "APISIX configuration backed up"

# Backup .env files
echo ""
echo "▶ Backing up environment configurations..."
mkdir -p "$BACKUP_DIR/env"
cp ~/services/PipeLineServices/.env "$BACKUP_DIR/env/pipeline_services.env" 2>/dev/null || true
echo "Environment files backed up"

# Create backup manifest
echo ""
echo "▶ Creating backup manifest..."
cat > "$BACKUP_DIR/BACKUP_MANIFEST.txt" <<EOF
==============================================
Complete Infrastructure Backup
==============================================
Backup Date: $(date)
Backup Directory: $BACKUP_DIR
Server: $(hostname)
User: $(whoami)

Components Backed Up:
- Milvus Vector Database
- PostgreSQL Database
- Redis Cache
- Docker Compose files
- APISIX Configuration
- Environment files

Backup Contents:
EOF

find "$BACKUP_DIR" -type f -exec ls -lh {} \; >> "$BACKUP_DIR/BACKUP_MANIFEST.txt"

echo "Manifest created"

# Calculate total backup size
TOTAL_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)

echo ""
echo "========================================="
echo "Complete Backup Finished!"
echo "========================================="
echo "Backup location: $BACKUP_DIR"
echo "Total size: $TOTAL_SIZE"
echo ""
echo "To restore this backup on a new server:"
echo "1. Copy the entire backup directory to the new server"
echo "2. Follow the restoration instructions in INFRASTRUCTURE.md"
echo ""

# Clean up old full backups (keep last 3)
echo "Cleaning up old full backups (keeping last 3)..."
cd "$BACKUP_ROOT"
ls -dt full_backup_* | tail -n +4 | xargs rm -rf 2>/dev/null || true
echo "Done!"
