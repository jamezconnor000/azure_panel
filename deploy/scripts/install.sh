#!/bin/bash
#===============================================================================
# Aether Access - Azure Panel Installation Script
# Version: 2.0.0
# Target: Azure BLU-IC2 Controllers (ARM64 Linux)
#===============================================================================
#
# This script installs the Aether Access system on an Azure Panel.
#
# Usage:
#   sudo ./install.sh [OPTIONS]
#
# Options:
#   --unattended    Run without prompts (use defaults)
#   --dev           Install in development mode (with hot-reload)
#   --no-service    Don't install systemd services
#   --data-dir DIR  Custom data directory (default: /var/lib/aether)
#   --help          Show this help message
#
#===============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
INSTALL_DIR="/opt/aether-access"
DATA_DIR="/var/lib/aether"
LOG_DIR="/var/log/aether"
CONFIG_DIR="/etc/aether"
SERVICE_USER="aether"
SERVICE_GROUP="aether"

# Defaults
UNATTENDED=false
DEV_MODE=false
INSTALL_SERVICES=true
API_PORT=8080

#===============================================================================
# Helper Functions
#===============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root (use sudo)"
        exit 1
    fi
}

check_architecture() {
    ARCH=$(uname -m)
    log_info "Detected architecture: $ARCH"

    case $ARCH in
        aarch64|arm64)
            log_success "ARM64 architecture supported"
            ;;
        x86_64)
            log_warn "x86_64 detected - this is typically for development/testing"
            ;;
        *)
            log_error "Unsupported architecture: $ARCH"
            exit 1
            ;;
    esac
}

check_os() {
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        log_info "Detected OS: $NAME $VERSION_ID"
    else
        log_warn "Could not detect OS version"
    fi
}

show_banner() {
    echo ""
    echo "==============================================================================="
    echo "                    AETHER ACCESS - INSTALLATION"
    echo "                    Azure Panel Deployment v2.0.0"
    echo "==============================================================================="
    echo ""
}

show_help() {
    cat << EOF
Aether Access - Azure Panel Installation Script

Usage:
  sudo ./install.sh [OPTIONS]

Options:
  --unattended    Run without prompts (use defaults)
  --dev           Install in development mode (with hot-reload)
  --no-service    Don't install systemd services
  --data-dir DIR  Custom data directory (default: /var/lib/aether)
  --port PORT     API server port (default: 8080)
  --help          Show this help message

Examples:
  sudo ./install.sh                    # Interactive installation
  sudo ./install.sh --unattended       # Automated installation
  sudo ./install.sh --dev --no-service # Development setup

EOF
    exit 0
}

#===============================================================================
# Parse Arguments
#===============================================================================

while [[ $# -gt 0 ]]; do
    case $1 in
        --unattended)
            UNATTENDED=true
            shift
            ;;
        --dev)
            DEV_MODE=true
            shift
            ;;
        --no-service)
            INSTALL_SERVICES=false
            shift
            ;;
        --data-dir)
            DATA_DIR="$2"
            shift 2
            ;;
        --port)
            API_PORT="$2"
            shift 2
            ;;
        --help|-h)
            show_help
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            ;;
    esac
done

#===============================================================================
# Pre-Installation Checks
#===============================================================================

pre_install_checks() {
    log_info "Running pre-installation checks..."

    check_root
    check_architecture
    check_os

    # Check for Python 3.9+
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
        log_info "Python version: $PYTHON_VERSION"

        if [[ $(echo "$PYTHON_VERSION >= 3.9" | bc -l) -eq 0 ]]; then
            log_error "Python 3.9 or higher is required (found $PYTHON_VERSION)"
            exit 1
        fi
        log_success "Python version OK"
    else
        log_error "Python 3 is not installed"
        exit 1
    fi

    # Check for pip
    if ! command -v pip3 &> /dev/null; then
        log_warn "pip3 not found, will attempt to install"
    fi

    # Check disk space (need at least 500MB)
    AVAILABLE_SPACE=$(df -m /opt 2>/dev/null | tail -1 | awk '{print $4}')
    if [[ -n "$AVAILABLE_SPACE" ]] && [[ "$AVAILABLE_SPACE" -lt 500 ]]; then
        log_error "Insufficient disk space. Need at least 500MB, have ${AVAILABLE_SPACE}MB"
        exit 1
    fi
    log_success "Disk space OK"

    log_success "Pre-installation checks passed"
}

#===============================================================================
# Installation Steps
#===============================================================================

install_system_dependencies() {
    log_info "Installing system dependencies..."

    # Detect package manager
    if command -v apt-get &> /dev/null; then
        apt-get update -qq
        apt-get install -y -qq \
            python3-pip \
            python3-venv \
            python3-dev \
            build-essential \
            sqlite3 \
            libsqlite3-dev \
            curl \
            jq
    elif command -v yum &> /dev/null; then
        yum install -y -q \
            python3-pip \
            python3-devel \
            gcc \
            sqlite \
            sqlite-devel \
            curl \
            jq
    elif command -v apk &> /dev/null; then
        apk add --no-cache \
            python3 \
            py3-pip \
            python3-dev \
            build-base \
            sqlite \
            sqlite-dev \
            curl \
            jq
    else
        log_warn "Unknown package manager, skipping system dependencies"
    fi

    log_success "System dependencies installed"
}

create_user_and_directories() {
    log_info "Creating service user and directories..."

    # Create service user if it doesn't exist
    if ! id "$SERVICE_USER" &>/dev/null; then
        useradd --system --no-create-home --shell /sbin/nologin "$SERVICE_USER"
        log_success "Created service user: $SERVICE_USER"
    else
        log_info "Service user already exists: $SERVICE_USER"
    fi

    # Create directories
    mkdir -p "$INSTALL_DIR"
    mkdir -p "$DATA_DIR"
    mkdir -p "$LOG_DIR"
    mkdir -p "$CONFIG_DIR"

    # Set ownership
    chown -R "$SERVICE_USER:$SERVICE_GROUP" "$DATA_DIR"
    chown -R "$SERVICE_USER:$SERVICE_GROUP" "$LOG_DIR"

    log_success "Directories created"
}

install_application() {
    log_info "Installing Aether Access application..."

    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    SOURCE_DIR="$(dirname "$SCRIPT_DIR")"

    # If running from deploy/scripts, go up to Source
    if [[ -d "$SOURCE_DIR/../api" ]]; then
        SOURCE_DIR="$SOURCE_DIR/.."
    fi

    # Copy application files
    log_info "Copying application files from $SOURCE_DIR..."

    # Copy API server and modules
    cp -r "$SOURCE_DIR/api" "$INSTALL_DIR/"
    cp -r "$SOURCE_DIR/python" "$INSTALL_DIR/"
    cp "$SOURCE_DIR/requirements.txt" "$INSTALL_DIR/"

    # Copy HAL libraries if they exist
    if [[ -f "$SOURCE_DIR/libhal_core.a" ]]; then
        mkdir -p "$INSTALL_DIR/lib"
        cp "$SOURCE_DIR"/lib*.a "$INSTALL_DIR/lib/" 2>/dev/null || true
    fi

    # Copy configuration templates
    if [[ -d "$SOURCE_DIR/config" ]]; then
        cp -r "$SOURCE_DIR/config/"* "$CONFIG_DIR/" 2>/dev/null || true
    fi

    log_success "Application files copied"

    # Create Python virtual environment
    log_info "Creating Python virtual environment..."
    python3 -m venv "$INSTALL_DIR/venv"

    # Install Python dependencies
    log_info "Installing Python dependencies..."
    "$INSTALL_DIR/venv/bin/pip" install --upgrade pip wheel
    "$INSTALL_DIR/venv/bin/pip" install -r "$INSTALL_DIR/requirements.txt"

    log_success "Python dependencies installed"

    # Set ownership
    chown -R "$SERVICE_USER:$SERVICE_GROUP" "$INSTALL_DIR"

    log_success "Application installed"
}

create_configuration() {
    log_info "Creating configuration files..."

    # Create main configuration file
    cat > "$CONFIG_DIR/aether.conf" << EOF
# Aether Access Configuration
# Generated by installer on $(date)

[server]
host = 0.0.0.0
port = $API_PORT
workers = 2
debug = false

[database]
path = $DATA_DIR/hal_database.db
backup_dir = $DATA_DIR/backups

[logging]
level = INFO
file = $LOG_DIR/aether.log
max_size = 10M
backup_count = 5

[security]
# IMPORTANT: Change this in production!
secret_key = $(openssl rand -hex 32)
token_expire_minutes = 480
allowed_origins = *

[hal]
mode = auto  # auto, native, simulation
library_path = $INSTALL_DIR/lib/libhal_core.so
EOF

    chmod 600 "$CONFIG_DIR/aether.conf"
    chown "$SERVICE_USER:$SERVICE_GROUP" "$CONFIG_DIR/aether.conf"

    # Create environment file for systemd
    cat > "$CONFIG_DIR/aether.env" << EOF
# Aether Access Environment Variables
API_PORT=$API_PORT
HAL_DATABASE_PATH=$DATA_DIR/hal_database.db
HAL_LOG_LEVEL=INFO
PYTHONPATH=$INSTALL_DIR/python:$INSTALL_DIR/api
EOF

    chmod 600 "$CONFIG_DIR/aether.env"
    chown "$SERVICE_USER:$SERVICE_GROUP" "$CONFIG_DIR/aether.env"

    # Create Ambient.ai environment file (optional)
    cat > "$CONFIG_DIR/ambient.env.template" << EOF
# Ambient.ai Export Daemon Configuration
# Copy this file to ambient.env and configure your API key
# To enable: sudo systemctl enable aether-ambient-export

# Ambient.ai API Key (REQUIRED)
AMBIENT_API_KEY=your-api-key-here

# Ambient.ai API URL (optional, defaults to production)
AMBIENT_API_URL=https://pacs-ingestion.ambient.ai/v1/api

# Export settings (optional)
AMBIENT_BATCH_SIZE=100
AMBIENT_POLL_INTERVAL=5
AMBIENT_MAX_RETRIES=3
EOF

    chmod 600 "$CONFIG_DIR/ambient.env.template"

    log_success "Configuration files created"
}

install_systemd_services() {
    if [[ "$INSTALL_SERVICES" != "true" ]]; then
        log_info "Skipping systemd service installation (--no-service)"
        return
    fi

    log_info "Installing systemd services..."

    # Main API service
    cat > /etc/systemd/system/aether-access.service << EOF
[Unit]
Description=Aether Access Control Panel API
Documentation=https://github.com/your-org/aether-access
After=network.target
Wants=network-online.target

[Service]
Type=exec
User=$SERVICE_USER
Group=$SERVICE_GROUP
EnvironmentFile=$CONFIG_DIR/aether.env
WorkingDirectory=$INSTALL_DIR/api
ExecStart=$INSTALL_DIR/venv/bin/python -m uvicorn unified_api_server:app --host 0.0.0.0 --port \${API_PORT} --workers 2
ExecReload=/bin/kill -HUP \$MAINPID
Restart=always
RestartSec=5
StandardOutput=append:$LOG_DIR/aether.log
StandardError=append:$LOG_DIR/aether-error.log

# Security hardening
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$DATA_DIR $LOG_DIR
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF

    # Ambient.ai Export Daemon service (optional)
    cat > /etc/systemd/system/aether-ambient-export.service << EOF
[Unit]
Description=Aether Access Ambient.ai Event Export Daemon
Documentation=https://docs.ambient.ai/pacs-integration
After=network.target aether-access.service
BindsTo=aether-access.service
PartOf=aether-access.service

[Service]
Type=exec
User=$SERVICE_USER
Group=$SERVICE_GROUP
EnvironmentFile=$CONFIG_DIR/aether.env
EnvironmentFile=-$CONFIG_DIR/ambient.env
WorkingDirectory=$INSTALL_DIR/api
ExecStart=$INSTALL_DIR/venv/bin/python ambient_export_daemon.py --api-key \${AMBIENT_API_KEY} --db-path \${HAL_DATABASE_PATH}
Restart=always
RestartSec=10
StandardOutput=append:$LOG_DIR/ambient_export.log
StandardError=append:$LOG_DIR/ambient_export-error.log

# Security hardening
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$DATA_DIR $LOG_DIR
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF

    # Reload systemd
    systemctl daemon-reload

    # Enable main service (Ambient.ai export daemon is optional - enable manually)
    systemctl enable aether-access.service

    log_success "Systemd services installed"
    log_info "Note: To enable Ambient.ai export, configure $CONFIG_DIR/ambient.env and run:"
    log_info "  sudo systemctl enable aether-ambient-export"
    log_info "  sudo systemctl start aether-ambient-export"
}

initialize_database() {
    log_info "Initializing database..."

    # Create database directory
    mkdir -p "$DATA_DIR"
    chown "$SERVICE_USER:$SERVICE_GROUP" "$DATA_DIR"

    # Initialize database with schema
    if [[ -f "$INSTALL_DIR/api/database.py" ]]; then
        cd "$INSTALL_DIR/api"

        # Run database initialization
        sudo -u "$SERVICE_USER" "$INSTALL_DIR/venv/bin/python" << 'PYEOF'
import os
import sys
sys.path.insert(0, os.getcwd())
sys.path.insert(0, '../python')

# Initialize HAL simulation database
from hal_bindings import HAL

db_path = os.environ.get('HAL_DATABASE_PATH', '/var/lib/aether/hal_database.db')
hal = HAL(db_path)

if hal.init():
    print("Database initialized successfully")

    # Add default access levels
    hal.add_access_level(1, "Full Access", description="Unrestricted access to all doors", doors=[1, 2, 3, 4])
    hal.add_access_level(2, "Standard Access", description="Normal employee access", doors=[1, 2])
    hal.add_access_level(3, "Limited Access", description="Visitor/contractor access", doors=[1])

    # Add default doors
    hal.add_door(1, "Main Entrance", strike_time_ms=3000)
    hal.add_door(2, "Side Entrance", strike_time_ms=3000)
    hal.add_door(3, "Back Door", strike_time_ms=5000)
    hal.add_door(4, "Server Room", strike_time_ms=2000)

    print("Default data seeded")
    hal.shutdown()
else:
    print("Database initialization failed")
    sys.exit(1)
PYEOF
    fi

    chown "$SERVICE_USER:$SERVICE_GROUP" "$DATA_DIR"/*

    log_success "Database initialized"
}

start_services() {
    if [[ "$INSTALL_SERVICES" != "true" ]]; then
        return
    fi

    log_info "Starting services..."

    systemctl start aether-access.service

    # Wait for service to start
    sleep 3

    # Check if service is running
    if systemctl is-active --quiet aether-access.service; then
        log_success "Aether Access service is running"
    else
        log_error "Failed to start Aether Access service"
        systemctl status aether-access.service
        exit 1
    fi
}

verify_installation() {
    log_info "Verifying installation..."

    # Check API health
    sleep 2

    if curl -s "http://localhost:$API_PORT/health" | jq -e '.status == "healthy"' > /dev/null 2>&1; then
        log_success "API health check passed"
    else
        log_warn "API health check failed (service may still be starting)"
    fi

    # Show API info
    API_INFO=$(curl -s "http://localhost:$API_PORT/health" 2>/dev/null)
    if [[ -n "$API_INFO" ]]; then
        echo ""
        echo "API Status:"
        echo "$API_INFO" | jq '.'
    fi
}

show_completion_message() {
    echo ""
    echo "==============================================================================="
    echo "                    INSTALLATION COMPLETE"
    echo "==============================================================================="
    echo ""
    echo "Aether Access has been installed successfully!"
    echo ""
    echo "Installation Details:"
    echo "  - Install Directory: $INSTALL_DIR"
    echo "  - Data Directory:    $DATA_DIR"
    echo "  - Config Directory:  $CONFIG_DIR"
    echo "  - Log Directory:     $LOG_DIR"
    echo "  - API Port:          $API_PORT"
    echo ""
    echo "Service Management:"
    echo "  - Start:   sudo systemctl start aether-access"
    echo "  - Stop:    sudo systemctl stop aether-access"
    echo "  - Status:  sudo systemctl status aether-access"
    echo "  - Logs:    sudo journalctl -u aether-access -f"
    echo ""
    echo "Quick Access:"
    echo "  - API Documentation: http://localhost:$API_PORT/docs"
    echo "  - Health Check:      http://localhost:$API_PORT/health"
    echo "  - Dashboard API:     http://localhost:$API_PORT/api/v1/dashboard"
    echo ""
    echo "Configuration:"
    echo "  - Main config: $CONFIG_DIR/aether.conf"
    echo "  - Environment: $CONFIG_DIR/aether.env"
    echo ""
    echo "Ambient.ai Integration (Optional):"
    echo "  1. Copy ambient.env.template to ambient.env"
    echo "  2. Add your AMBIENT_API_KEY"
    echo "  3. Enable: sudo systemctl enable aether-ambient-export"
    echo "  4. Start:  sudo systemctl start aether-ambient-export"
    echo ""
    echo "IMPORTANT: Review and update the secret_key in $CONFIG_DIR/aether.conf"
    echo "==============================================================================="
    echo ""
}

#===============================================================================
# Main Installation
#===============================================================================

main() {
    show_banner

    if [[ "$UNATTENDED" != "true" ]]; then
        echo "This script will install Aether Access on this system."
        echo ""
        echo "Installation options:"
        echo "  - Install Directory: $INSTALL_DIR"
        echo "  - Data Directory:    $DATA_DIR"
        echo "  - API Port:          $API_PORT"
        echo "  - Install Services:  $INSTALL_SERVICES"
        echo "  - Dev Mode:          $DEV_MODE"
        echo ""
        read -p "Continue with installation? [Y/n] " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]] && [[ -n $REPLY ]]; then
            echo "Installation cancelled."
            exit 0
        fi
    fi

    pre_install_checks
    install_system_dependencies
    create_user_and_directories
    install_application
    create_configuration
    install_systemd_services
    initialize_database
    start_services
    verify_installation
    show_completion_message
}

main "$@"
