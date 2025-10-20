#!/bin/bash

# Start all CrawlEnginePro services in development mode
# All services use ports 8070-8079 (development range)

VENV="/Users/rakesh/Desktop/crawlenginepro.mindmate247.com/local_dev/venv/bin/python"
CODE_DIR="/Users/rakesh/Desktop/crawlenginepro.mindmate247.com/code"
LOG_DIR="/Users/rakesh/Desktop/crawlenginepro.mindmate247.com/local_dev"

echo "=== Clearing Ingestion Pipeline Ports (8070-8079) ==="
for port in 8070 8071 8072 8073 8074 8075 8076 8077 8078 8079; do
  pid=$(lsof -ti :$port 2>/dev/null)
  if [ -n "$pid" ]; then
    echo "  Killing process on port $port (PID: $pid)"
    kill -9 $pid 2>/dev/null
  fi
done
sleep 2
echo ""

echo "=== Starting CrawlEnginePro Services (Development) ==="
echo "Port Range: 8070-8079"
echo ""

# Set environment
export PYTHONPATH="$CODE_DIR"

# Helper function to start a service
start_service() {
    local port=$1
    local script_path=$2
    local service_name=$3
    local log_file="$LOG_DIR/${service_name}.log"

    cd "$(dirname "$CODE_DIR/$script_path")"
    PORT=$port $VENV "$CODE_DIR/$script_path" > "$log_file" 2>&1 &
    local pid=$!
    echo "✓ Started $service_name on port $port (PID: $pid)"
    sleep 1
}

# Start services in dependency order
start_service 8075 "Ingestion/services/llm_gateway/v1.0.0/llm_gateway.py" "llm_gateway"
sleep 2  # LLM Gateway needs to be fully ready

start_service 8074 "Ingestion/services/storage/v1.0.0/storage_api.py" "storage"
start_service 8073 "Ingestion/services/embeddings/v1.0.0/embeddings_api.py" "embeddings"
start_service 8072 "Ingestion/services/metadata/v1.0.0/metadata_api.py" "metadata"
start_service 8071 "Ingestion/services/chunking/v1.0.0/chunking_orchestrator.py" "chunking"
sleep 3  # Wait for all internal services to be ready

start_service 8070 "Ingestion/v1.0.0/main_ingestion_api.py" "ingestion"

echo ""
echo "=== Waiting for services to initialize ==="
sleep 5

echo ""
echo "=== Health Check ==="
curl -s http://localhost:8070/health | python3 -m json.tool

echo ""
echo "=== Services Started Successfully ==="
echo "Ingestion API: http://localhost:8070"
echo "Logs directory: $LOG_DIR"
