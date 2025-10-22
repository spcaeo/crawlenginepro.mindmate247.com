# Backup Scripts

Automated backup scripts for all infrastructure components.

## Scripts Overview

| Script | Purpose | Frequency | Retention |
|--------|---------|-----------|-----------|
| `backup_milvus.sh` | Backup Milvus vector database | Daily | 7 days |
| `backup_postgres.sh` | Backup PostgreSQL database | Daily | 14 days |
| `backup_redis.sh` | Backup Redis cache | Daily | 7 days |
| `backup_all.sh` | Complete infrastructure backup | Weekly | 3 backups |

## Installation

### 1. Copy Scripts to Server

```bash
# On server
mkdir -p ~/scripts/backups
cd ~/scripts/backups

# Copy all scripts
scp -i ~/reku631_nebius backup_*.sh reku631@89.169.103.3:~/scripts/backups/

# Make executable
chmod +x ~/scripts/backups/*.sh
```

### 2. Setup Cron Jobs (Automated Backups)

```bash
# Edit crontab
crontab -e

# Add these lines:
# Daily Milvus backup at 2 AM
0 2 * * * /home/reku631/scripts/backups/backup_milvus.sh >> /home/reku631/logs/backup_milvus.log 2>&1

# Daily PostgreSQL backup at 2:30 AM
30 2 * * * /home/reku631/scripts/backups/backup_postgres.sh >> /home/reku631/logs/backup_postgres.log 2>&1

# Daily Redis backup at 3 AM
0 3 * * * /home/reku631/scripts/backups/backup_redis.sh >> /home/reku631/logs/backup_redis.log 2>&1

# Weekly full backup every Sunday at 4 AM
0 4 * * 0 /home/reku631/scripts/backups/backup_all.sh >> /home/reku631/logs/backup_all.log 2>&1
```

### 3. Create Log Directory

```bash
mkdir -p ~/logs
```

## Manual Backup

### Backup Milvus Only

```bash
cd ~/scripts/backups
./backup_milvus.sh
```

### Backup PostgreSQL Only

```bash
cd ~/scripts/backups
./backup_postgres.sh
```

### Backup Redis Only

```bash
cd ~/scripts/backups
./backup_redis.sh
```

### Complete Backup (All Components)

```bash
cd ~/scripts/backups
./backup_all.sh
```

## Backup Locations

Default backup directories:
- **Milvus**: `~/backups/milvus/`
- **PostgreSQL**: `~/backups/postgres/`
- **Redis**: `~/backups/redis/`
- **Full Backup**: `~/backups/full_backup_YYYYMMDD_HHMMSS/`

### Custom Backup Directory

```bash
# Set custom backup directory
export BACKUP_DIR=/path/to/custom/backup
./backup_milvus.sh
```

## Restoration

See `INFRASTRUCTURE.md` for detailed restoration procedures.

### Quick Restore Commands

#### Restore Milvus

```bash
# Stop services
docker stop milvus-standalone milvus-minio milvus-etcd

# Remove old volumes
docker volume rm rag-services_milvus_data

# Create new volume
docker volume create rag-services_milvus_data

# Restore from backup
docker run --rm \
  -v rag-services_milvus_data:/data \
  -v ~/backups/milvus:/backup \
  ubuntu \
  tar xzf /backup/milvus_backup_20251009_120000.tar.gz -C /data

# Restart services
cd ~/backups/rag-services
docker-compose up -d
```

#### Restore PostgreSQL

```bash
# Restore database
gunzip -c ~/backups/postgres/postgres_backup_20251009_120000.sql.gz | \
  docker exec -i rag-postgres psql -U rag_user rag_metadata
```

#### Restore Redis

```bash
# Stop Redis
docker stop rag-redis

# Copy backup to container
docker cp ~/backups/redis/redis_backup_20251009_120000.rdb rag-redis:/data/dump.rdb

# Start Redis
docker start rag-redis
```

## Monitoring Backups

### Check Backup Status

```bash
# View recent Milvus backups
ls -lht ~/backups/milvus/ | head

# View recent PostgreSQL backups
ls -lht ~/backups/postgres/ | head

# View full backups
ls -lht ~/backups/ | grep full_backup
```

### Check Backup Logs

```bash
# View Milvus backup log
tail -f ~/logs/backup_milvus.log

# View PostgreSQL backup log
tail -f ~/logs/backup_postgres.log

# View full backup log
tail -f ~/logs/backup_all.log
```

### Verify Backup Integrity

```bash
# Test Milvus backup (extract to temp)
mkdir -p /tmp/test_restore
tar xzf ~/backups/milvus/milvus_backup_20251009_120000.tar.gz -C /tmp/test_restore
ls -la /tmp/test_restore
rm -rf /tmp/test_restore

# Test PostgreSQL backup (dry run)
gunzip -c ~/backups/postgres/postgres_backup_20251009_120000.sql.gz | head -50
```

## Troubleshooting

### Backup Script Fails

**Check Docker containers are running**:
```bash
docker ps | grep -E "milvus|postgres|redis"
```

**Check disk space**:
```bash
df -h
```

**Check permissions**:
```bash
ls -la ~/backups/
```

### Backup Takes Too Long

**Milvus**: Large vector databases can take 10-30 minutes
- Consider incremental backups
- Use Milvus backup tool instead of volume backup

**PostgreSQL**: Large databases can take several minutes
- Consider using `pg_dump` with compression flags
- Use parallel dump (`pg_dump -j 4`)

### Out of Disk Space

**Clean up old backups**:
```bash
# Find large backup directories
du -sh ~/backups/* | sort -h

# Remove old backups manually
rm ~/backups/milvus/milvus_backup_20240901_*.tar.gz
```

## Best Practices

1. **Test Restores Regularly**: Verify backups can actually be restored
2. **Off-site Backups**: Copy backups to external storage (S3, another server)
3. **Monitor Cron Jobs**: Check logs regularly for failures
4. **Document Changes**: Update this README if you modify scripts
5. **Encrypt Sensitive Backups**: Use GPG for PostgreSQL backups containing sensitive data

## Off-site Backup (Recommended)

### Using rsync to Remote Server

```bash
# Add to crontab (daily at 5 AM)
0 5 * * * rsync -avz --delete ~/backups/ user@backup-server:/backups/production/
```

### Using AWS S3

```bash
# Install AWS CLI
pip install awscli

# Configure AWS credentials
aws configure

# Add to backup_all.sh
aws s3 sync ~/backups/full_backup_$TIMESTAMP/ s3://my-backup-bucket/production/full_backup_$TIMESTAMP/
```

---

**Last Updated**: October 9, 2025
