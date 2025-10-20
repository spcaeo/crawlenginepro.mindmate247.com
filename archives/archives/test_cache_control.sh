#!/bin/bash
# Test script to verify cache control works

echo "=========================================="
echo "Cache Control Test"
echo "=========================================="
echo ""

# Check current setting
echo "1. Checking current ENABLE_CACHE setting:"
grep "^ENABLE_CACHE=" .env
echo ""

# Test LLM Gateway cache stats
echo "2. Testing LLM Gateway cache stats:"
curl -s http://localhost:8065/cache/stats | jq . || echo "LLM Gateway not running on port 8065"
echo ""

# Test Answer Generation health
echo "3. Testing Answer Generation cache status:"
curl -s http://localhost:8074/health | jq '.dependencies.cache' || echo "Answer Generation not running on port 8074"
echo ""

echo "=========================================="
echo "To disable cache:"
echo "  1. Edit .env: ENABLE_CACHE=false"
echo "  2. Restart services"
echo "  3. Run this script again to verify"
echo "=========================================="
