#!/bin/bash
#
# Health Check Script for All PipeLineServices
# Tests all Ingestion and Retrieval pipeline health endpoints
#
# Usage: ./check_health_all.sh
#

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check a single service
check_service() {
    local port=$1
    local name=$2
    local url="http://localhost:${port}/health"

    printf "%-30s Port ${BLUE}%-5s${NC} " "$name" "$port"

    # Check if service is listening on port
    if ! nc -z localhost $port 2>/dev/null; then
        echo -e "${RED}❌ Not Running${NC}"
        return 1
    fi

    # Call health endpoint
    response=$(curl -s -w "\n%{http_code}" "$url" 2>/dev/null)
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)

    if [ "$http_code" = "200" ]; then
        status=$(echo "$body" | jq -r '.status // "unknown"' 2>/dev/null)
        version=$(echo "$body" | jq -r '.version // "?"' 2>/dev/null)

        case "$status" in
            "healthy")
                echo -e "${GREEN}✅ Healthy${NC} (v${version})"
                ;;
            "degraded")
                echo -e "${YELLOW}⚠️  Degraded${NC} (v${version})"
                ;;
            *)
                echo -e "${RED}❌ Unhealthy${NC} (v${version})"
                ;;
        esac

        # Show additional info if available
        if command -v jq &> /dev/null; then
            # Check for API connectivity (if field exists)
            api_connected=$(echo "$body" | jq -r '.api_connected // .nebius_connected // .llm_gateway_connected // empty' 2>/dev/null)
            if [ ! -z "$api_connected" ]; then
                if [ "$api_connected" = "true" ]; then
                    echo -e "  ${GREEN}├─ API Connected${NC}"
                else
                    echo -e "  ${RED}├─ API Disconnected${NC}"
                fi
            fi

            # Check for cache stats (if field exists)
            cache_enabled=$(echo "$body" | jq -r '.cache_enabled // empty' 2>/dev/null)
            cache_entries=$(echo "$body" | jq -r '.cache_entries // empty' 2>/dev/null)
            cache_hit_rate=$(echo "$body" | jq -r '.cache_hit_rate // empty' 2>/dev/null)

            if [ ! -z "$cache_enabled" ]; then
                if [ "$cache_enabled" = "true" ]; then
                    echo -e "  ${BLUE}└─ Cache: ${cache_entries} entries, ${cache_hit_rate}% hit rate${NC}"
                fi
            fi
        fi

        return 0
    else
        echo -e "${RED}❌ HTTP ${http_code}${NC}"
        return 1
    fi
}

# Header
echo "================================================================================"
echo "  PipeLineServices Health Check"
echo "================================================================================"
echo ""

# Check if required tools are available
if ! command -v nc &> /dev/null; then
    echo -e "${YELLOW}⚠️  Warning: 'nc' (netcat) not found. Port checks will be skipped.${NC}"
fi

if ! command -v jq &> /dev/null; then
    echo -e "${YELLOW}⚠️  Warning: 'jq' not found. Detailed info will not be shown.${NC}"
    echo -e "   Install with: ${BLUE}brew install jq${NC} (macOS) or ${BLUE}apt-get install jq${NC} (Linux)"
    echo ""
fi

# Ingestion Pipeline (Ports 8060-8069)
echo -e "${BLUE}=== INGESTION PIPELINE (8060-8069) ===${NC}"
echo ""

healthy_count=0
total_count=0

services_ingestion=(
    "8060:Ingestion API (Main)"
    "8061:Chunking Service"
    "8062:Metadata Service"
    "8063:Embeddings Service"
    "8064:Storage Service (Milvus)"
    "8065:LLM Gateway"
)

for service in "${services_ingestion[@]}"; do
    port="${service%%:*}"
    name="${service##*:}"
    total_count=$((total_count + 1))

    if check_service "$port" "$name"; then
        healthy_count=$((healthy_count + 1))
    fi
done

echo ""

# Retrieval Pipeline (Ports 8070-8079)
echo -e "${BLUE}=== RETRIEVAL PIPELINE (8070-8079) ===${NC}"
echo ""

services_retrieval=(
    "8070:Retrieval API (Main)"
    "8071:Search Service"
    "8072:Reranking Service"
    "8073:Compression Service"
    "8074:Answer Generation Service"
    "8075:Intent Service"
)

for service in "${services_retrieval[@]}"; do
    port="${service%%:*}"
    name="${service##*:}"
    total_count=$((total_count + 1))

    if check_service "$port" "$name"; then
        healthy_count=$((healthy_count + 1))
    fi
done

echo ""
echo "================================================================================"
echo -e "  Summary: ${GREEN}${healthy_count}${NC}/${total_count} services healthy"

percentage=$((healthy_count * 100 / total_count))

if [ $healthy_count -eq $total_count ]; then
    echo -e "  Status: ${GREEN}✅ All systems operational${NC}"
    exit 0
elif [ $healthy_count -gt 0 ]; then
    echo -e "  Status: ${YELLOW}⚠️  Some services degraded (${percentage}%)${NC}"
    exit 1
else
    echo -e "  Status: ${RED}❌ All services down${NC}"
    exit 2
fi
