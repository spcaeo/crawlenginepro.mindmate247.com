#!/bin/bash
# ==============================================================================
# CrawlEnginePro Server Setup Script
# ==============================================================================
# Sets up environment on server for a specific environment (dev/staging/prod)
# Run this on the SERVER after deploying code
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
# Environment Validation
# ==============================================================================

validate_environment() {
    local env=$1
    if [[ ! "$env" =~ ^(dev|development|staging|prod|production)$ ]]; then
        print_error "Invalid environment: $env"
        echo "  Valid: dev, staging, prod"
        exit 1
    fi

    # Normalize environment name
    case "$env" in
        dev|development) echo "development" ;;
        staging) echo "staging" ;;
        prod|production) echo "production" ;;
    esac
}

# ==============================================================================
# Main Setup
# ==============================================================================

main() {
    if [ $# -lt 1 ]; then
        echo "Usage: $0 <environment>"
        echo "  environment: dev, staging, or prod"
        exit 1
    fi

    local ENV=$(validate_environment "$1")

    print_header "CrawlEnginePro Server Setup - $ENV Environment"

    # Determine paths
    local SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    local CODE_DIR="$(dirname "$SCRIPT_DIR")"
    local BASE_DIR="$(dirname "$CODE_DIR")"
    local ENV_DIR="$BASE_DIR/$ENV"
    local VENV_DIR="$ENV_DIR/venv"
    local LOGS_DIR="$ENV_DIR/logs"

    print_info "Code directory: $CODE_DIR"
    print_info "Environment directory: $ENV_DIR"

    # Create environment directory structure
    print_info "Creating directory structure..."
    mkdir -p "$ENV_DIR"
    mkdir -p "$LOGS_DIR"
    print_success "Directory structure created"

    # Check if Python 3 is installed
    print_info "Checking Python installation..."
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed"
        exit 1
    fi
    local PYTHON_VERSION=$(python3 --version)
    print_success "Python 3 found: $PYTHON_VERSION"

    # Create virtual environment
    if [ -d "$VENV_DIR" ]; then
        print_warning "Virtual environment already exists"
        read -p "Recreate virtual environment? (y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            print_info "Removing existing virtual environment..."
            rm -rf "$VENV_DIR"
            print_info "Creating new virtual environment..."
            python3 -m venv "$VENV_DIR"
            print_success "Virtual environment created"
        else
            print_info "Using existing virtual environment"
        fi
    else
        print_info "Creating virtual environment..."
        python3 -m venv "$VENV_DIR"
        print_success "Virtual environment created"
    fi

    # Install/update dependencies
    print_info "Installing dependencies..."
    source "$VENV_DIR/bin/activate"

    # Upgrade pip
    pip install --upgrade pip > /dev/null 2>&1

    # Install requirements for all services
    local requirements_files=(
        "$CODE_DIR/Ingestion/services/storage/v1.0.0/requirements.txt"
        "$CODE_DIR/Ingestion/services/embeddings/v1.0.0/requirements.txt"
        "$CODE_DIR/Ingestion/services/metadata/v1.0.0/requirements.txt"
        "$CODE_DIR/Ingestion/services/chunking/v1.0.0/requirements.txt"
        "$CODE_DIR/Ingestion/services/llm_gateway/v1.0.0/requirements.txt"
        "$CODE_DIR/Ingestion/v1.0.0/requirements.txt"
        "$CODE_DIR/Retrieval/v1.0.0/requirements.txt"
    )

    for req_file in "${requirements_files[@]}"; do
        if [ -f "$req_file" ]; then
            print_info "Installing from $(basename $(dirname $req_file))..."
            pip install -r "$req_file" > /dev/null 2>&1 || print_warning "Some packages may have failed"
        fi
    done

    deactivate
    print_success "Dependencies installed"

    # Setup Python path for shared modules
    print_info "Configuring Python path for shared modules..."
    local SITE_PACKAGES="$VENV_DIR/lib/python3.*/site-packages"
    cat > "$VENV_DIR"/lib/python3.*/site-packages/sitecustomize.py << EOF
import sys
import os

# Add code directory to Python path
code_dir = "$CODE_DIR"
if code_dir not in sys.path:
    sys.path.insert(0, code_dir)

# Add shared directory to Python path
shared_dir = os.path.join(code_dir, "shared")
if shared_dir not in sys.path:
    sys.path.insert(0, shared_dir)
EOF
    print_success "Python path configured"

    # Create symlinks for environment file
    print_info "Creating environment file symlinks..."
    cd "$CODE_DIR"

    # Link shared/.env to the specific environment
    ln -sf ".env.$ENV" "shared/.env"

    # Link root .env to shared/.env
    ln -sf "shared/.env" ".env"

    print_success "Environment files linked"

    # Verify environment file
    if [ -f "$CODE_DIR/shared/.env.$ENV" ]; then
        print_success "Environment file exists: shared/.env.$ENV"
    else
        print_warning "Environment file not found: shared/.env.$ENV"
        print_info "Please create this file based on .env.example"
    fi

    # Summary
    print_header "Setup Complete"
    print_success "Environment '$ENV' is ready"
    echo ""
    print_info "Directory structure:"
    echo "  Code: $CODE_DIR"
    echo "  Venv: $VENV_DIR"
    echo "  Logs: $LOGS_DIR"
    echo "  Env file: $CODE_DIR/shared/.env.$ENV"
    echo ""
    print_info "Next steps:"
    echo "  1. Verify API keys in: $CODE_DIR/shared/.env.$ENV"
    echo "  2. Start services: cd $CODE_DIR && ./deploy/manage.sh $ENV start"
    echo "  3. Check status: ./deploy/manage.sh $ENV status"
    echo ""
}

main "$@"
