#!/bin/bash
# Clear all caches from services that have caching enabled

echo "=========================================="
echo "🧹 Clearing All Service Caches"
echo "=========================================="
echo ""

cleared=0
failed=0

# LLM Gateway (8065)
echo "📦 LLM Gateway (Port 8065)..."
if lsof -ti:8065 >/dev/null 2>&1; then
    result=$(curl -s -X POST http://localhost:8065/cache/clear)
    if echo "$result" | grep -q "ok"; then
        echo "  ✅ Cache cleared"
        ((cleared++))
    else
        echo "  ❌ Failed to clear cache"
        ((failed++))
    fi
else
    echo "  ⚠️  Service not running"
fi
echo ""

# Answer Generation (8074)
echo "💬 Answer Generation Service (Port 8074)..."
if lsof -ti:8074 >/dev/null 2>&1; then
    result=$(curl -s -X POST http://localhost:8074/v1/cache/clear)
    if echo "$result" | grep -q "success"; then
        entries=$(echo "$result" | jq -r '.message' 2>/dev/null || echo "Cache cleared")
        echo "  ✅ $entries"
        ((cleared++))
    else
        echo "  ❌ Failed to clear cache"
        ((failed++))
    fi
else
    echo "  ⚠️  Service not running"
fi
echo ""

echo "=========================================="
echo "Summary:"
echo "  ✅ Cleared: $cleared service(s)"
if [ $failed -gt 0 ]; then
    echo "  ❌ Failed: $failed service(s)"
fi
echo "=========================================="
echo ""
echo "Note: Only 2 services have caching:"
echo "  - LLM Gateway (8065)"
echo "  - Answer Generation (8074)"
echo ""
echo "Other services (Search, Reranking, Compression, Intent)"
echo "do NOT have caching and are not affected."
