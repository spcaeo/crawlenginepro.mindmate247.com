#!/bin/bash
# ==============================================================================
# CrawlEnginePro Multi-Environment Service Manager
# ==============================================================================
# Manages services across 3 environments: development, staging, production
# Server: reku631@89.169.108.8
# Location: ~/crawlenginepro/code
# ==============================================================================

set -e

# Colors
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m'

# ==============================================================================
# Configuration
# ==============================================================================

# Determine base directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CODE_DIR="$(dirname "$SCRIPT_DIR")"

# Environment validation
validate_environment() {
    local env=$1
    if [[ ! "$env" =~ ^(dev|development|staging|prod|production)$ ]]; then
        echo -e "${RED}✗ Invalid environment: $env${NC}"
        echo -e "  Valid: dev, staging, prod"
        exit 1
    fi

    # Normalize environment name
    case "$env" in
        dev|development) echo "development" ;;
        staging) echo "staging" ;;
        prod|production) echo "production" ;;
    esac
}

# Get environment paths
get_env_paths() {
    local env=$1
    local base_dir=$(dirname "$CODE_DIR")

    echo "BASE_DIR=$base_dir/$env"
    echo "VENV_DIR=$base_dir/$env/venv"
    echo "LOGS_DIR=$base_dir/$env/logs"
    echo "ENV_FILE=$CODE_DIR/shared/.env.$env"
}

# ==============================================================================
# Service Definitions
# ==============================================================================

declare -A INGESTION_SERVICES=(
    ["storage"]="Ingestion/services/storage/v1.0.0/storage_api.py"
    ["embeddings"]="Ingestion/services/embeddings/v1.0.0/embeddings_api.py"
    ["metadata"]="Ingestion/services/metadata/v1.0.0/metadata_api.py"
    ["chunking"]="Ingestion/services/chunking/v1.0.0/chunking_orchestrator.py"
    ["llm_gateway"]="Ingestion/services/llm_gateway/v1.0.0/llm_gateway.py"
    ["ingestion"]="Ingestion/v1.0.0/main_ingestion_api.py"
)

declare -A RETRIEVAL_SERVICES=(
    ["search"]="Retrieval/services/search/v1.0.0/search_api.py"
    ["reranking"]="Retrieval/services/reranking/v1.0.0/reranking_api.py"
    ["compression"]="Retrieval/services/compression/v1.0.0/compression_api.py"
    ["answer_generation"]="Retrieval/services/answer_generation/v1.0.0/answer_api.py"
    ["intent"]="Retrieval/services/intent/v1.0.0/intent_api.py"
    ["retrieval"]="Retrieval/v1.0.0/main_retrieval_api.py"
)

# ==============================================================================
# Helper Functions
# ==============================================================================

print_header() {
    echo -e "\n${BOLD}${CYAN}=== $1 ===${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${CYAN}ℹ${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# ==============================================================================
# Core Functions
# ==============================================================================

# Start a single service
start_service() {
    local env=$1
    local service_name=$2
    local script_path=$3

    eval $(get_env_paths "$env")

    local venv_python="$VENV_DIR/bin/python"
    local log_file="$LOGS_DIR/${service_name}.log"
    local pid_file="$LOGS_DIR/${service_name}.pid"

    # Check if already running
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p $pid > /dev/null 2>&1; then
            print_warning "$service_name already running (PID: $pid)"
            return 0
        fi
    fi

    # Ensure logs directory exists
    mkdir -p "$LOGS_DIR"

    # Load environment file
    export $(grep -v '^#' "$ENV_FILE" | xargs)

    # Start service
    cd "$CODE_DIR"
    nohup "$venv_python" "$script_path" > "$log_file" 2>&1 &
    local pid=$!
    echo $pid > "$pid_file"

    # Wait a moment and check if it's still running
    sleep 2
    if ps -p $pid > /dev/null 2>&1; then
        print_success "$service_name started (PID: $pid)"
        return 0
    else
        print_error "$service_name failed to start (check $log_file)"
        return 1
    fi
}

# Stop a single service
stop_service() {
    local env=$1
    local service_name=$2

    eval $(get_env_paths "$env")

    local pid_file="$LOGS_DIR/${service_name}.pid"

    if [ ! -f "$pid_file" ]; then
        print_info "$service_name not running"
        return 0
    fi

    local pid=$(cat "$pid_file")
    if ps -p $pid > /dev/null 2>&1; then
        kill $pid
        sleep 1
        if ps -p $pid > /dev/null 2>&1; then
            kill -9 $pid
        fi
        print_success "$service_name stopped"
    else
        print_info "$service_name was not running"
    fi

    rm -f "$pid_file"
}

# Check service status
check_service_status() {
    local env=$1
    local service_name=$2

    eval $(get_env_paths "$env")

    local pid_file="$LOGS_DIR/${service_name}.pid"

    if [ ! -f "$pid_file" ]; then
        echo -e "  ${RED}○${NC} $service_name: not running"
        return 1
    fi

    local pid=$(cat "$pid_file")
    if ps -p $pid > /dev/null 2>&1; then
        # Get port from process
        local port=$(lsof -Pan -p $pid -i 2>/dev/null | grep LISTEN | awk '{print $9}' | cut -d':' -f2 | head -1)
        echo -e "  ${GREEN}●${NC} $service_name: running (PID: $pid, Port: $port)"
        return 0
    else
        echo -e "  ${RED}○${NC} $service_name: dead (stale PID file)"
        rm -f "$pid_file"
        return 1
    fi
}

# ==============================================================================
# Command Handlers
# ==============================================================================

cmd_start() {
    local env=$(validate_environment "$1")
    local pipeline=${2:-all}

    print_header "Starting Services: $env environment"

    eval $(get_env_paths "$env")

    # Check if venv exists
    if [ ! -d "$VENV_DIR" ]; then
        print_error "Virtual environment not found: $VENV_DIR"
        print_info "Please run setup first on the server"
        exit 1
    fi

    # Start services based on pipeline
    case "$pipeline" in
        ingestion)
            for service in storage embeddings metadata chunking llm_gateway ingestion; do
                start_service "$env" "$service" "${INGESTION_SERVICES[$service]}"
            done
            ;;
        retrieval)
            for service in search reranking compression answer_generation intent retrieval; do
                start_service "$env" "$service" "${RETRIEVAL_SERVICES[$service]}"
            done
            ;;
        all)
            # Start ingestion first
            for service in storage embeddings metadata chunking llm_gateway ingestion; do
                start_service "$env" "$service" "${INGESTION_SERVICES[$service]}"
            done
            # Then retrieval
            for service in search reranking compression answer_generation intent retrieval; do
                start_service "$env" "$service" "${RETRIEVAL_SERVICES[$service]}"
            done
            ;;
        *)
            print_error "Invalid pipeline: $pipeline"
            print_info "Valid: ingestion, retrieval, all"
            exit 1
            ;;
    esac
}

cmd_stop() {
    local env=$(validate_environment "$1")
    local pipeline=${2:-all}

    print_header "Stopping Services: $env environment"

    case "$pipeline" in
        ingestion)
            for service in ingestion llm_gateway chunking metadata embeddings storage; do
                stop_service "$env" "$service"
            done
            ;;
        retrieval)
            for service in retrieval intent answer_generation compression reranking search; do
                stop_service "$env" "$service"
            done
            ;;
        all)
            # Stop in reverse order
            for service in retrieval intent answer_generation compression reranking search; do
                stop_service "$env" "$service"
            done
            for service in ingestion llm_gateway chunking metadata embeddings storage; do
                stop_service "$env" "$service"
            done
            ;;
        *)
            print_error "Invalid pipeline: $pipeline"
            exit 1
            ;;
    esac
}

cmd_restart() {
    local env=$(validate_environment "$1")
    local pipeline=${2:-all}

    cmd_stop "$env" "$pipeline"
    sleep 2
    cmd_start "$env" "$pipeline"
}

cmd_status() {
    local env=$(validate_environment "$1")

    print_header "Service Status: $env environment"

    echo -e "${BOLD}Ingestion Pipeline:${NC}"
    local ingestion_running=0
    local ingestion_total=0
    for service in storage embeddings metadata chunking llm_gateway ingestion; do
        ((ingestion_total++))
        if check_service_status "$env" "$service"; then
            ((ingestion_running++))
        fi
    done

    echo ""
    echo -e "${BOLD}Retrieval Pipeline:${NC}"
    local retrieval_running=0
    local retrieval_total=0
    for service in search reranking compression answer_generation intent retrieval; do
        ((retrieval_total++))
        if check_service_status "$env" "$service"; then
            ((retrieval_running++))
        fi
    done

    echo ""
    echo -e "${BOLD}Summary:${NC}"
    echo -e "  Ingestion: ${GREEN}$ingestion_running${NC}/$ingestion_total running"
    echo -e "  Retrieval: ${GREEN}$retrieval_running${NC}/$retrieval_total running"
}

cmd_logs() {
    local env=$(validate_environment "$1")
    local service=${2:-all}

    eval $(get_env_paths "$env")

    if [ "$service" = "all" ]; then
        print_header "All Service Logs: $env environment"
        tail -n 50 "$LOGS_DIR"/*.log
    else
        local log_file="$LOGS_DIR/${service}.log"
        if [ -f "$log_file" ]; then
            print_header "Logs for $service: $env environment"
            tail -f "$log_file"
        else
            print_error "Log file not found: $log_file"
            exit 1
        fi
    fi
}

# ==============================================================================
# Main
# ==============================================================================

show_usage() {
    cat << EOF
${BOLD}CrawlEnginePro Multi-Environment Service Manager${NC}

${BOLD}Usage:${NC}
  $0 <environment> <command> [options]

${BOLD}Environments:${NC}
  dev, development    Development environment (ports 8070-8099)
  staging             Staging environment (ports 8080-8109)
  prod, production    Production environment (ports 8060-8069, 8110-8119)

${BOLD}Commands:${NC}
  start [pipeline]    Start services (pipeline: ingestion|retrieval|all)
  stop [pipeline]     Stop services
  restart [pipeline]  Restart services
  status              Show service status
  logs [service]      Show logs (service name or 'all')

${BOLD}Examples:${NC}
  $0 dev start                    # Start all services in development
  $0 dev start ingestion          # Start only ingestion pipeline
  $0 staging restart              # Restart all staging services
  $0 prod status                  # Check production status
  $0 dev logs storage             # Follow storage service logs

${BOLD}Service Structure:${NC}
  Ingestion: storage, embeddings, metadata, chunking, llm_gateway, ingestion
  Retrieval: search, reranking, compression, answer_generation, intent, retrieval

EOF
}

# Main command dispatcher
main() {
    if [ $# -lt 2 ]; then
        show_usage
        exit 1
    fi

    local environment=$1
    local command=$2
    shift 2

    case "$command" in
        start)
            cmd_start "$environment" "${1:-all}"
            ;;
        stop)
            cmd_stop "$environment" "${1:-all}"
            ;;
        restart)
            cmd_restart "$environment" "${1:-all}"
            ;;
        status)
            cmd_status "$environment"
            ;;
        logs)
            cmd_logs "$environment" "${1:-all}"
            ;;
        *)
            print_error "Unknown command: $command"
            show_usage
            exit 1
            ;;
    esac
}

main "$@"
