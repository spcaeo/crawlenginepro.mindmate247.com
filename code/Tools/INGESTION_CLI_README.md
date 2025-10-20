# Ingestion CLI Tool

**One unified tool to manage all document ingestion operations - no more creating test files!**

## Overview

The `ingestion-cli` is a command-line interface that provides a simple, reusable way to interact with the Ingestion API. Instead of creating new test files for each operation, you use this single tool with different commands.

## Location

```
/Users/rakesh/Desktop/CrawlEnginePro/nebius_hosting/ai_studio/hosting/PipeLineServies/Tools/ingestion-cli
```

## Prerequisites

1. **Start the Ingestion API first:**
   ```bash
   cd /Users/rakesh/Desktop/CrawlEnginePro/nebius_hosting/ai_studio/hosting/PipeLineServies
   ./Tools/pipeline-manager ingestion
   ```

2. **The API must be running on port 8060** (default)

## Usage

### Basic Syntax

```bash
./Tools/ingestion-cli <command> [options]
```

### Available Commands

## 1. Ingest a Document

Upload and process a document file:

```bash
# Ingest with auto-generated document ID (from filename)
./Tools/ingestion-cli ingest --file path/to/document.md --tenant mytenant

# Ingest with custom document ID
./Tools/ingestion-cli ingest --file path/to/document.md --tenant mytenant --doc-id my-doc-123

# Ingest with default tenant (if --tenant not specified, uses "default_tenant")
./Tools/ingestion-cli ingest --file path/to/document.md
```

**Parameters:**
- `--file` (required): Path to the document file
- `--tenant` (optional): Tenant identifier (default: "default_tenant")
- `--doc-id` (optional): Custom document ID (default: filename without extension)

**Example Output:**
```
ℹ Checking Ingestion API at http://localhost:8060...
✓ Ingestion API is running

ℹ Ingesting document: my-document for tenant: mytenant
✓ Document ingested successfully!
  Tenant: mytenant
  Document ID: my-document
  Chunks: 42
  Time: 3.5s
```

---

## 2. Delete a Specific Document

Remove a single document:

```bash
./Tools/ingestion-cli delete-doc --tenant mytenant --doc-id my-doc-123
```

**Parameters:**
- `--tenant` (required): Tenant identifier
- `--doc-id` (required): Document identifier

**Example Output:**
```
ℹ Deleting document: my-doc-123 for tenant: mytenant
✓ Document deleted successfully!
  Deleted chunks: 42
```

---

## 3. Delete All Documents for a Tenant

Remove all documents belonging to a tenant:

```bash
./Tools/ingestion-cli delete-tenant --tenant mytenant
```

**Safety:** Requires confirmation by typing the tenant ID

**Example:**
```
⚠ This will delete ALL documents for tenant: mytenant
Type 'mytenant' to confirm: mytenant
ℹ Deleting all documents for tenant: mytenant
✓ Tenant data deleted successfully!
  Deleted chunks: 1250
```

---

## 4. Delete All Collections (DANGEROUS)

**⚠️ WARNING: This deletes ALL data from ALL tenants!**

```bash
./Tools/ingestion-cli delete-all --confirm
```

**Safety:** Requires `--confirm` flag AND typing "DELETE ALL"

**Example:**
```
⚠️  WARNING: This will DELETE ALL DATA from ALL TENANTS!
Type 'DELETE ALL' to confirm: DELETE ALL
ℹ Deleting all collections...
✓ All collections deleted successfully!
  Collections dropped: 5
```

---

## 5. Check Ingestion Status

Get status information:

```bash
# Status for entire tenant
./Tools/ingestion-cli status --tenant mytenant

# Status for specific document
./Tools/ingestion-cli status --tenant mytenant --doc-id my-doc-123
```

**Parameters:**
- `--tenant` (required): Tenant identifier
- `--doc-id` (optional): Document identifier

---

## 6. List Tenants

```bash
./Tools/ingestion-cli list-tenants
```

*Note: This feature will query Milvus to list all tenants*

---

## 7. List Documents

List all documents for a tenant:

```bash
./Tools/ingestion-cli list-docs --tenant mytenant
```

*Note: This feature will query Milvus to list all documents for the tenant*

---

## Common Use Cases

### Test a New Markdown File

```bash
# Just pass the file, everything else is automatic
./Tools/ingestion-cli ingest --file new-document.md --tenant test-tenant
```

### Replace an Existing Document

```bash
# 1. Delete the old document
./Tools/ingestion-cli delete-doc --tenant mytenant --doc-id old-doc

# 2. Ingest the new one
./Tools/ingestion-cli ingest --file new-document.md --tenant mytenant --doc-id old-doc
```

### Clean Up Test Data

```bash
# Delete all test tenant data
./Tools/ingestion-cli delete-tenant --tenant test-tenant
```

### Fresh Start (Development Only)

```bash
# Delete everything and start fresh
./Tools/ingestion-cli delete-all --confirm
```

---

## Tips

1. **Color Output**: The CLI uses colors for better readability:
   - 🟢 Green: Success messages
   - 🔴 Red: Error messages
   - 🔵 Blue: Info messages
   - 🟡 Yellow: Warnings

2. **API Health Check**: The CLI automatically checks if the Ingestion API is running before executing commands

3. **Error Handling**: Clear error messages with HTTP status codes and details

4. **Confirmation Required**: Destructive operations (delete-tenant, delete-all) require confirmation to prevent accidents

5. **Default Values**:
   - Default tenant: "default_tenant"
   - Default doc-id: filename without extension
   - Default API URL: http://localhost:8060

---

## Configuration

Edit the CLI file to change defaults:

```python
# Configuration
INGESTION_API_URL = "http://localhost:8060"  # Change if API runs on different port
DEFAULT_TENANT = "default_tenant"             # Change default tenant
```

---

## Troubleshooting

### "Ingestion API is not running"

Start the API first:
```bash
./Tools/pipeline-manager ingestion
```

### "File not found"

Check the file path - use absolute or relative path from current directory

### "HTTP Error: 500"

Check the API logs for errors. The Ingestion API terminal will show detailed error information.

---

## Comparison: Old vs New Way

### Old Way (Creating Test Files)
```python
# test_my_document.py
import requests

payload = {
    "tenant_id": "mytenant",
    "document_id": "my-doc",
    "content": open("my-doc.md").read(),
    "metadata": {...}
}

response = requests.post("http://localhost:8060/ingest", json=payload)
print(response.json())
```

Then:
```bash
python3 test_my_document.py
```

### New Way (Using CLI)
```bash
./Tools/ingestion-cli ingest --file my-doc.md --tenant mytenant --doc-id my-doc
```

**Benefits:**
- ✅ No need to create new Python files
- ✅ Simple command-line interface
- ✅ Automatic file reading
- ✅ Built-in error handling
- ✅ Color-coded output
- ✅ Confirmation for dangerous operations
- ✅ Reusable across all documents

---

## Examples

### Example 1: Ingest Multiple Documents

```bash
# Ingest several documents for the same tenant
./Tools/ingestion-cli ingest --file doc1.md --tenant acme --doc-id doc1
./Tools/ingestion-cli ingest --file doc2.md --tenant acme --doc-id doc2
./Tools/ingestion-cli ingest --file doc3.md --tenant acme --doc-id doc3
```

### Example 2: Test Different Tenants

```bash
# Same document for different tenants
./Tools/ingestion-cli ingest --file test.md --tenant tenant1
./Tools/ingestion-cli ingest --file test.md --tenant tenant2
./Tools/ingestion-cli ingest --file test.md --tenant tenant3
```

### Example 3: Clean Development Environment

```bash
# Remove test data after development
./Tools/ingestion-cli delete-tenant --tenant dev-test
./Tools/ingestion-cli delete-tenant --tenant staging-test
```

---

## Integration with Pipeline Manager

The CLI works seamlessly with pipeline-manager:

```bash
# 1. Start services
./Tools/pipeline-manager start-ingestion

# 2. Use CLI for operations
./Tools/ingestion-cli ingest --file document.md

# 3. Check status
./Tools/pipeline-manager status

# 4. Stop services when done
./Tools/pipeline-manager stop
```

---

## Future Enhancements

Planned features:
- [ ] Batch ingestion (multiple files at once)
- [ ] List tenants from Milvus
- [ ] List documents for a tenant
- [ ] Export/backup tenant data
- [ ] Progress bars for large files
- [ ] JSON output mode for scripting
- [ ] Configuration file support

---

## Support

For issues or questions:
1. Check if Ingestion API is running: `./Tools/pipeline-manager status`
2. Check API logs in the terminal where you started the API
3. Verify file paths and permissions
4. Check the `--help` output: `./Tools/ingestion-cli --help`

---

## Summary

The `ingestion-cli` is your one-stop tool for all ingestion operations:

- **Ingest**: `./Tools/ingestion-cli ingest --file <file> --tenant <tenant>`
- **Delete Doc**: `./Tools/ingestion-cli delete-doc --tenant <tenant> --doc-id <id>`
- **Delete Tenant**: `./Tools/ingestion-cli delete-tenant --tenant <tenant>`
- **Delete All**: `./Tools/ingestion-cli delete-all --confirm`
- **Status**: `./Tools/ingestion-cli status --tenant <tenant>`

**No more creating test files - just use one unified CLI tool!**
