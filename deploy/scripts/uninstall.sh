#!/bin/bash
#===============================================================================
# Aether Access - Uninstallation Script
# Version: 2.0.0
#===============================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

INSTALL_DIR="/opt/aether-access"
DATA_DIR="/var/lib/aether"
LOG_DIR="/var/log/aether"
CONFIG_DIR="/etc/aether"
SERVICE_USER="aether"

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check root
if [[ $EUID -ne 0 ]]; then
    log_error "This script must be run as root"
    exit 1
fi

echo ""
echo "==============================================================================="
echo "                    AETHER ACCESS - UNINSTALLATION"
echo "==============================================================================="
echo ""

# Confirm
read -p "This will remove Aether Access. Are you sure? [y/N] " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Uninstallation cancelled."
    exit 0
fi

# Ask about data
REMOVE_DATA=false
read -p "Remove data directory ($DATA_DIR)? [y/N] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    REMOVE_DATA=true
fi

# Stop and disable service
log_info "Stopping services..."
systemctl stop aether-access.service 2>/dev/null || true
systemctl disable aether-access.service 2>/dev/null || true

# Remove systemd service
log_info "Removing systemd service..."
rm -f /etc/systemd/system/aether-access.service
systemctl daemon-reload

# Remove installation directory
log_info "Removing installation directory..."
rm -rf "$INSTALL_DIR"

# Remove configuration
log_info "Removing configuration..."
rm -rf "$CONFIG_DIR"

# Remove logs
log_info "Removing logs..."
rm -rf "$LOG_DIR"

# Remove data if requested
if [[ "$REMOVE_DATA" == "true" ]]; then
    log_info "Removing data directory..."
    rm -rf "$DATA_DIR"
else
    log_warn "Data directory preserved at: $DATA_DIR"
fi

# Remove service user
if id "$SERVICE_USER" &>/dev/null; then
    log_info "Removing service user..."
    userdel "$SERVICE_USER" 2>/dev/null || true
fi

echo ""
echo "==============================================================================="
echo "                    UNINSTALLATION COMPLETE"
echo "==============================================================================="
echo ""
log_info "Aether Access has been removed."
if [[ "$REMOVE_DATA" != "true" ]]; then
    echo "Note: Data preserved at $DATA_DIR - remove manually if not needed."
fi
echo ""
