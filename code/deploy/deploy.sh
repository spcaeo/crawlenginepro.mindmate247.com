#!/bin/bash
# ==============================================================================
# CrawlEnginePro Server Deployment Script
# ==============================================================================
# Deploys code from local machine to server
# Server: reku631@89.169.108.8
# ==============================================================================

set -e

# Colors
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m'

# Configuration
SERVER_USER="reku631"
SERVER_HOST="89.169.108.8"
SSH_KEY="$HOME/reku631_nebius"
REMOTE_DIR="~/crawlenginepro/code"
LOCAL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

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
# Main Deployment
# ==============================================================================

print_header "CrawlEnginePro Deployment"

# Verify SSH key exists
if [ ! -f "$SSH_KEY" ]; then
    print_error "SSH key not found: $SSH_KEY"
    exit 1
fi

# Verify local directory
if [ ! -d "$LOCAL_DIR" ]; then
    print_error "Local directory not found: $LOCAL_DIR"
    exit 1
fi

print_info "Local directory: $LOCAL_DIR"
print_info "Server: $SERVER_USER@$SERVER_HOST"
print_info "Remote directory: $REMOTE_DIR"
echo ""

# Test SSH connection
print_info "Testing SSH connection..."
if ! ssh -i "$SSH_KEY" -o ConnectTimeout=10 "$SERVER_USER@$SERVER_HOST" "echo 'SSH connection successful'" > /dev/null 2>&1; then
    print_error "SSH connection failed"
    exit 1
fi
print_success "SSH connection successful"

# Create remote directory if it doesn't exist
print_info "Ensuring remote directory exists..."
ssh -i "$SSH_KEY" "$SERVER_USER@$SERVER_HOST" "mkdir -p $REMOTE_DIR"
print_success "Remote directory ready"

# Sync code to server (excluding unnecessary files)
print_info "Syncing code to server..."
rsync -avz --progress \
    -e "ssh -i $SSH_KEY" \
    --exclude '.git' \
    --exclude '__pycache__' \
    --exclude '*.pyc' \
    --exclude '.DS_Store' \
    --exclude 'venv' \
    --exclude 'node_modules' \
    --exclude '*.log' \
    --exclude 'archives' \
    --delete \
    "$LOCAL_DIR/" "$SERVER_USER@$SERVER_HOST:$REMOTE_DIR/"

print_success "Code synced successfully"

# Set executable permissions on scripts
print_info "Setting executable permissions..."
ssh -i "$SSH_KEY" "$SERVER_USER@$SERVER_HOST" "chmod +x $REMOTE_DIR/deploy/*.sh"
ssh -i "$SSH_KEY" "$SERVER_USER@$SERVER_HOST" "chmod +x $REMOTE_DIR/Tools/*"
print_success "Permissions set"

# Show deployment summary
print_header "Deployment Complete"
print_success "Code deployed to server successfully"
echo ""
print_info "Next steps:"
echo "  1. SSH to server: ssh -i $SSH_KEY $SERVER_USER@$SERVER_HOST"
echo "  2. Run server setup (first time only): cd $REMOTE_DIR && ./deploy/server_setup.sh dev"
echo "  3. Start services: cd $REMOTE_DIR && ./deploy/manage.sh dev start"
echo "  4. Check status: ./deploy/manage.sh dev status"
echo ""
print_warning "Remember to update API keys in .env files if this is first deployment!"
