# Troubleshooting Guide - Milvus Storage Service v1.0.0

**Last Updated:** October 9, 2025

---

## Table of Contents

1. [Quick Diagnostics](#quick-diagnostics)
2. [Connection Issues](#connection-issues)
3. [Insert Failures](#insert-failures)
4. [Search Issues](#search-issues)
5. [Performance Problems](#performance-problems)
6. [Memory Issues](#memory-issues)
7. [Common Error Messages](#common-error-messages)

---

## Quick Diagnostics

### Health Check Script

```bash
#!/bin/bash
# save as check_storage_health.sh

echo "=== Milvus Storage Service Health Check ==="
echo

# 1. Check if service is running
echo "1. Checking storage service..."
curl -s http://localhost:8064/health | python3 -m json.tool || echo "✗ Service not responding"
echo

# 2. Check Milvus connection
echo "2. Checking Milvus..."
docker ps | grep milvus || echo "✗ Milvus not running"
echo

# 3. Check port availability
echo "3. Checking ports..."
lsof -i :8064 || echo "✗ Port 8064 not in use"
lsof -i :19530 || echo "✗ Port 19530 not in use"
echo

# 4. Check memory usage
echo "4. Memory usage:"
free -h | grep Mem
echo

# 5. Check logs
echo "5. Recent errors (last 10):"
tail -20 /tmp/storage_api.log 2>/dev/null | grep -i "error\|failed\|✗" | tail -10 || echo "No recent errors"
echo

echo "=== Health Check Complete ==="
```

### System Requirements Check

```python
import psutil
import sys

def check_system_requirements():
    """Check if system meets minimum requirements"""

    print("=== System Requirements Check ===\n")

    # RAM check
    ram_gb = psutil.virtual_memory().total / (1024**3)
    print(f"RAM: {ram_gb:.1f} GB", end="")
    if ram_gb >= 32:
        print(" ✅")
    else:
        print(f" ⚠️  (Minimum: 32 GB)")

    # CPU check
    cpu_count = psutil.cpu_count()
    print(f"CPUs: {cpu_count}", end="")
    if cpu_count >= 4:
        print(" ✅")
    else:
        print(" ⚠️  (Recommended: 4+)")

    # Disk space check
    disk = psutil.disk_usage('/')
    disk_free_gb = disk.free / (1024**3)
    print(f"Disk free: {disk_free_gb:.1f} GB", end="")
    if disk_free_gb >= 100:
        print(" ✅")
    else:
        print(" ⚠️  (Recommended: 100+ GB)")

    # Python version
    python_version = sys.version.split()[0]
    print(f"Python: {python_version}", end="")
    if sys.version_info >= (3, 12):
        print(" ✅")
    else:
        print(" ⚠️  (Required: 3.12+)")

    print("\n=== Check Complete ===")

if __name__ == "__main__":
    check_system_requirements()
```

---

## Connection Issues

### Problem: Cannot Connect to Milvus

**Symptoms:**
```
✗ Failed to connect to Milvus: [Errno 111] Connection refused
```

**Diagnosis:**
```bash
# Check if Milvus is running
docker ps | grep milvus

# Check if port 19530 is open
telnet localhost 19530

# Check Milvus logs
docker logs milvus-standalone | tail -50
```

**Solutions:**

**1. Milvus Not Running**
```bash
# Start Milvus
cd /path/to/milvus
docker-compose up -d

# Wait for startup (30-60 seconds)
sleep 60

# Verify
docker ps | grep milvus
```

**2. Wrong Host/Port in .env**
```bash
# Check .env file
cat ../../.env | grep MILVUS

# Verify configuration
MILVUS_HOST_DEVELOPMENT=localhost  # Should match Milvus location
MILVUS_PORT_DEVELOPMENT=19530      # Should match Milvus port
```

**3. Authentication Issues**
```bash
# Check credentials in .env
MILVUS_USER=your_username
MILVUS_PASSWORD=your_password

# Test connection with pymilvus
python3 << EOF
from pymilvus import connections
connections.connect(
    alias="test",
    host="localhost",
    port=19530,
    user="your_username",
    password="your_password"
)
print("✓ Connected successfully")
EOF
```

**4. Firewall Blocking**
```bash
# Check firewall rules (Linux)
sudo iptables -L | grep 19530

# Allow port (if blocked)
sudo iptables -A INPUT -p tcp --dport 19530 -j ACCEPT
```

### Problem: Connection Timeout

**Symptoms:**
```
✗ Failed to connect to Milvus: timeout
```

**Solutions:**

**1. Increase Timeout**
```python
# config.py
REQUEST_TIMEOUT = 60  # Increase from 30 to 60 seconds
```

**2. Check Network Latency**
```bash
# Ping Milvus host
ping localhost

# Check network issues
traceroute localhost
```

### Problem: Connection Pool Exhausted

**Symptoms:**
```
Error: Connection pool is full
```

**Solution:**
```python
# config.py
CONNECTION_POOL_SIZE = 20  # Increase from 10 to 20
```

---

## Insert Failures

### Problem: "Collection already exists"

**Symptoms:**
```json
{
  "success": false,
  "error": "Collection already exists"
}
```

**Solutions:**

**1. Use Existing Collection**
```python
# Set create_if_not_exists=False
insert_chunks(
    collection_name="existing_collection",
    chunks=chunks,
    create_if_not_exists=False  # Use existing
)
```

**2. Delete Existing Collection**
```python
from operations import delete_collection

delete_collection("my_collection")
# Then create new one
```

### Problem: "Field 'dense_vector' dimension mismatch"

**Symptoms:**
```
Error: Dense vector dimension is 768, expected 1024
```

**Solutions:**

**1. Check Embedding Service**
```bash
# Verify BGE-M3 is producing 1024-dim vectors
curl http://localhost:8062/health
```

**2. Match Dimension in Config**
```python
# config.py
DEFAULT_DIMENSION = 1024  # Must match BGE-M3 output
```

**3. Recreate Collection**
```python
# Delete collection with wrong dimension
delete_collection("my_collection")

# Create with correct dimension
create_collection("my_collection", dimension=1024)
```

### Problem: Insert Timeout

**Symptoms:**
```
Error: Insert operation timed out after 30 seconds
```

**Solutions:**

**1. Increase Timeout**
```python
# config.py
REQUEST_TIMEOUT = 60  # Increase timeout
```

**2. Reduce Batch Size**
```python
# Split large batch into smaller chunks
batch_size = 1000
for i in range(0, len(chunks), batch_size):
    batch = chunks[i:i + batch_size]
    insert_chunks(collection, batch)
```

**3. Check Milvus Performance**
```bash
# Check Milvus CPU/memory
docker stats milvus-standalone

# Check Milvus logs for errors
docker logs milvus-standalone | grep -i error
```

### Problem: "No space left on device"

**Symptoms:**
```
Error: [Errno 28] No space left on device
```

**Solutions:**

**1. Check Disk Space**
```bash
df -h

# Check Milvus data directory
du -sh /var/lib/docker/volumes/milvus-*
```

**2. Clean Up Old Collections**
```python
# Delete unused collections
collections = utility.list_collections()
for collection in collections:
    if "test_" in collection:
        delete_collection(collection)
```

**3. Increase Disk Space**
```bash
# Add more storage
# Or move Milvus data to larger volume
```

---

## Search Issues

### Problem: No Results Returned

**Symptoms:**
- Search returns empty list
- Expected results not found

**Diagnosis:**
```python
# Check if data exists
collection = get_collection("my_collection")
print(f"Entity count: {collection.num_entities}")

# Check if collection is loaded
print(f"Loaded: {collection.loaded}")
```

**Solutions:**

**1. Collection Not Loaded**
```python
collection.load()
```

**2. Wrong Filter Expression**
```python
# Bad filter (might exclude all results)
expr = 'tenant_id == "tenant_1" AND document_id == "nonexistent"'

# Verify filter matches data
results = collection.query(
    expr='tenant_id == "tenant_1"',
    output_fields=["id"],
    limit=10
)
print(f"Found {len(results)} entities")
```

**3. Data Not Flushed Yet**
```python
# Wait for auto-flush (1 second)
import time
time.sleep(1)

# Or manually flush (not recommended)
collection.flush()
```

### Problem: Search Returns Wrong Results

**Symptoms:**
- Results don't match query semantically
- Irrelevant results returned

**Solutions:**

**1. Check Vector Normalization**
```python
# Ensure vectors are normalized for IP metric
import numpy as np

vector = np.array(your_vector)
normalized = vector / np.linalg.norm(vector)
```

**2. Verify Index Type**
```python
# Check index
indexes = collection.indexes
for idx in indexes:
    print(f"Field: {idx.field_name}, Type: {idx.params}")

# Should see: FLAT with metric_type=IP
```

**3. Check Embedding Quality**
```bash
# Test embedding service
curl -X POST http://localhost:8062/v1/embed \
  -H "Content-Type: application/json" \
  -d '{"texts": ["test query"]}'
```

---

## Performance Problems

### Problem: Slow Insert Performance

**Symptoms:**
- Insert takes >30 seconds for 300 chunks
- Much slower than benchmarks

**Diagnosis:**
```python
# Add timing to each stage
import time

start = time.time()
result = insert_chunks(collection, chunks)
elapsed = time.time() - start

print(f"Insert time: {elapsed:.2f}s")
print(f"Chunks: {len(chunks)}")
print(f"Time per chunk: {elapsed/len(chunks)*1000:.2f}ms")
```

**Solutions:**

**1. Check for Manual Flush (Should Be Removed)**
```python
# operations.py line 255-258
# Should NOT have: collection.flush()
```

**2. Check Index Type**
```python
# config.py
# Should be FLAT, not IVF_FLAT
DENSE_INDEX_TYPE = "FLAT"
```

**3. Check Milvus Resources**
```bash
# Check CPU/memory
docker stats milvus-standalone

# Check if Milvus is swapping
free -h
```

**4. Batch Inserts**
```python
# Insert all at once (GOOD)
insert_chunks(collection, all_chunks)

# Not one by one (BAD)
for chunk in all_chunks:
    insert_chunks(collection, [chunk])
```

### Problem: Slow Search Performance

**Symptoms:**
- Search takes >500ms
- Much slower than expected

**Solutions:**

**1. Always Filter by tenant_id**
```python
# Good (fast)
expr = 'tenant_id == "tenant_1"'

# Bad (slow)
expr = ''  # No filter, searches all partitions
```

**2. Reduce Top-K**
```python
# Good
limit = 20

# Bad (slower)
limit = 1000
```

**3. Check Partition Count**
```python
# config.py
NUM_PARTITIONS = 256  # Should be configured

# Verify
collection = Collection("my_collection")
print(f"Partitions: {collection.num_partitions}")
```

**4. Check Index**
```python
# Should be FLAT for <1M vectors per partition
indexes = collection.indexes
for idx in indexes:
    if idx.field_name == "dense_vector":
        print(f"Index type: {idx.params.get('index_type')}")
        # Should be "FLAT"
```

---

## Memory Issues

### Problem: Out of Memory (OOM)

**Symptoms:**
```
Error: Cannot allocate memory
Killed (OOM killer)
```

**Diagnosis:**
```bash
# Check current memory usage
free -h

# Check Milvus memory
docker stats milvus-standalone

# Check storage service memory
ps aux | grep storage_api.py
```

**Solutions:**

**1. Reduce Partition Count**
```python
# config.py
NUM_PARTITIONS = 128  # Reduce from 256
# Saves ~1 GB
```

**2. Limit Milvus Memory**
```yaml
# docker-compose.yml
services:
  standalone:
    mem_limit: 24g  # Limit to 24GB
```

**3. Implement Data Cleanup**
```python
# Delete old data periodically
from datetime import datetime, timedelta

cutoff = datetime.now() - timedelta(days=30)
delete_chunks(
    collection_name="my_collection",
    filter_expr=f'created_at < "{cutoff.isoformat()}"'
)
```

**4. Switch to IVF_FLAT Index**
```python
# config.py (for >1M vectors)
DENSE_INDEX_TYPE = "IVF_FLAT"
DENSE_NLIST = 128
# Uses less memory than FLAT
```

### Problem: Memory Leak

**Symptoms:**
- Memory usage continuously grows
- Never releases memory

**Diagnosis:**
```python
# Monitor memory over time
import psutil
import time

process = psutil.Process()
for i in range(10):
    mem_mb = process.memory_info().rss / 1024 / 1024
    print(f"Memory: {mem_mb:.1f} MB")
    time.sleep(60)  # Check every minute
```

**Solutions:**

**1. Restart Service Periodically**
```bash
# Add cron job to restart daily
0 3 * * * systemctl restart milvus-storage
```

**2. Check for Unclosed Connections**
```python
# Always use context managers
with get_collection("my_collection") as collection:
    collection.insert(data)
```

---

## Common Error Messages

### "Protobuf version mismatch"

**Error:**
```
UserWarning: Protobuf gencode version 5.27.2 is exactly one major version older than the runtime version 6.31.1
```

**Solution:**
```bash
# Upgrade protobuf
pip install --upgrade protobuf

# Or downgrade if needed
pip install protobuf==5.27.2
```

**Impact:** Warning only, not critical

### "Collection not loaded"

**Error:**
```
Error: Collection 'my_collection' is not loaded
```

**Solution:**
```python
collection = Collection("my_collection")
collection.load()
```

### "Partition key not found"

**Error:**
```
Error: Field 'tenant_id' is not a partition key
```

**Solution:**
```python
# Check schema
collection = Collection("my_collection")
for field in collection.schema.fields:
    if field.name == "tenant_id":
        print(f"Is partition key: {field.is_partition_key}")

# If False, recreate collection with correct schema
```

### "Index not found"

**Error:**
```
Error: Index not found on field 'dense_vector'
```

**Solution:**
```python
from schema import create_indexes

collection = Collection("my_collection")
create_indexes(collection)
collection.load()
```

### "Invalid expression"

**Error:**
```
Error: Invalid expression: tenant_id = "tenant_1"
```

**Solution:**
```python
# Wrong (single =)
expr = 'tenant_id = "tenant_1"'

# Correct (double ==)
expr = 'tenant_id == "tenant_1"'
```

---

## Emergency Recovery

### Service Won't Start

**1. Check Process**
```bash
ps aux | grep storage_api.py
# If running, kill it
pkill -f storage_api.py
```

**2. Check Port**
```bash
lsof -i :8064
# If occupied by another process
kill -9 <PID>
```

**3. Check Logs**
```bash
tail -50 /tmp/storage_api.log
# Look for errors
```

**4. Reset Everything**
```bash
# Stop all services
pkill -f storage_api.py
docker-compose down

# Clear data (if acceptable)
docker-compose down -v

# Start fresh
docker-compose up -d
sleep 60
python3 storage_api.py
```

### Data Corruption

**Symptoms:**
- Collections show wrong entity counts
- Queries return corrupted data

**Solution:**
```bash
# 1. Stop services
docker-compose down

# 2. Backup data
tar -czf milvus-backup-$(date +%Y%m%d).tar.gz /var/lib/docker/volumes/milvus-*

# 3. Delete corrupted data
docker volume rm $(docker volume ls -q | grep milvus)

# 4. Restart Milvus
docker-compose up -d

# 5. Re-ingest data
# (Use backup or re-run ingestion pipeline)
```

---

## Getting Help

### Log Collection

```bash
#!/bin/bash
# collect_logs.sh

timestamp=$(date +%Y%m%d_%H%M%S)
output_dir="logs_$timestamp"
mkdir -p "$output_dir"

# Storage service logs
cp /tmp/storage_api.log "$output_dir/" 2>/dev/null

# Milvus logs
docker logs milvus-standalone > "$output_dir/milvus.log" 2>&1

# System info
free -h > "$output_dir/memory.txt"
df -h > "$output_dir/disk.txt"
docker ps > "$output_dir/containers.txt"

# Configuration
cp ../../.env "$output_dir/env.txt" 2>/dev/null
cp config.py "$output_dir/"

# Tar it up
tar -czf "logs_$timestamp.tar.gz" "$output_dir"
rm -rf "$output_dir"

echo "Logs collected: logs_$timestamp.tar.gz"
```

### Contact Information

**Documentation:** This folder (`milvus-storage-documentation/`)

**Common Issues:** Check this file first (07_TROUBLESHOOTING.md)

**GitHub Issues:** Create issue with:
- Error message
- Steps to reproduce
- Log output (from collect_logs.sh)
- System info (RAM, CPU, OS)

---

**Document Status:** ✅ COMPLETE
**Common Issues Covered:** YES
**Emergency Procedures:** YES
