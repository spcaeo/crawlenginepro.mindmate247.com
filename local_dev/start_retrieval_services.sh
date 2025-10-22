#!/bin/bash

# Start all Retrieval services in development mode
# All services use ports 8090-8099 (development range)

VENV="/Users/rakesh/Desktop/crawlenginepro.mindmate247.com/local_dev/venv/bin/python"
CODE_DIR="/Users/rakesh/Desktop/crawlenginepro.mindmate247.com/code"
LOG_DIR="/Users/rakesh/Desktop/crawlenginepro.mindmate247.com/local_dev"

echo "=== Clearing Retrieval Pipeline Ports (8090-8099) ==="
for port in 8090 8091 8092 8093 8094 8095; do
  pid=$(lsof -ti :$port 2>/dev/null)
  if [ -n "$pid" ]; then
    echo "  Killing process on port $port (PID: $pid)"
    kill -9 $pid 2>/dev/null
  fi
done
sleep 2
echo ""

echo "=== Starting Retrieval Services (Development) ==="
echo "Port Range: 8090-8099"
echo ""

# Set environment
export PYTHONPATH="$CODE_DIR:$CODE_DIR/shared"
export ENVIRONMENT="development"
export PIPELINE_ENV="dev"
export LLM_GATEWAY_URL_DEVELOPMENT="http://localhost:8075"

# Helper function to start a service
start_service() {
    local port=$1
    local script_path=$2
    local service_name=$3
    local log_file="$LOG_DIR/${service_name}.log"

    cd "$(dirname "$CODE_DIR/$script_path")"
    PORT=$port ENVIRONMENT=development LLM_GATEWAY_URL_DEVELOPMENT=http://localhost:8075 $VENV "$CODE_DIR/$script_path" > "$log_file" 2>&1 &
    local pid=$!
    echo "✓ Started $service_name on port $port (PID: $pid)"
    sleep 1
}

# Start services in dependency order
start_service 8095 "Retrieval/services/intent/v1.0.0/intent_api.py" "intent"
start_service 8091 "Retrieval/services/search/v1.0.0/search_api.py" "search"
start_service 8092 "Retrieval/services/reranking/v1.0.0/reranking_api.py" "reranking"
start_service 8093 "Retrieval/services/compression/v1.0.0/compression_api.py" "compression"
start_service 8094 "Retrieval/services/answer_generation/v1.0.0/answer_api.py" "answer"
sleep 3  # Wait for all internal services to be ready

start_service 8090 "Retrieval/v1.0.0/main_retrieval_api.py" "retrieval"

echo ""
echo "=== Waiting for services to initialize ==="
sleep 5

echo ""
echo "=== Health Check ==="
curl -s http://localhost:8090/health | python3 -m json.tool

echo ""
echo "=== Services Started Successfully ==="
echo "Retrieval API: http://localhost:8090"
echo "Logs directory: $LOG_DIR"
