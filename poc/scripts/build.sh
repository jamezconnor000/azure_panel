#!/bin/bash
##############################################################################
# Aether Access PoC - Build Script
#
# Builds the complete PoC including all applications and tools.
#
# Author: FAM-HAL-v1.0-001
# Date: February 10, 2026
##############################################################################

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
POC_DIR="$(dirname "$SCRIPT_DIR")"
BUILD_DIR="${POC_DIR}/build"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

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

# Parse arguments
BUILD_TYPE="Debug"
CLEAN=false
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --release)
            BUILD_TYPE="Release"
            shift
            ;;
        --clean)
            CLEAN=true
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --release    Build in Release mode (default: Debug)"
            echo "  --clean      Clean build directory first"
            echo "  --verbose    Verbose output"
            echo "  --help       Show this help"
            echo ""
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Main
main() {
    echo ""
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║          Aether Access PoC - Build Script                    ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo ""

    log_info "Build type: ${BUILD_TYPE}"
    log_info "Build directory: ${BUILD_DIR}"

    # Clean if requested
    if $CLEAN; then
        log_info "Cleaning build directory..."
        rm -rf "${BUILD_DIR}"
    fi

    # Create build directory
    mkdir -p "${BUILD_DIR}"
    cd "${BUILD_DIR}"

    # Run CMake
    log_info "Running CMake..."
    if $VERBOSE; then
        cmake -DCMAKE_BUILD_TYPE="${BUILD_TYPE}" ..
    else
        cmake -DCMAKE_BUILD_TYPE="${BUILD_TYPE}" .. > /dev/null
    fi
    log_success "CMake configuration complete"

    # Build
    log_info "Building..."
    MAKE_OPTS="-j$(sysctl -n hw.ncpu 2>/dev/null || nproc 2>/dev/null || echo 4)"

    if $VERBOSE; then
        make $MAKE_OPTS VERBOSE=1
    else
        make $MAKE_OPTS
    fi

    log_success "Build complete!"

    echo ""
    echo "  Executables:"
    echo "    ${CYAN}hal_engine${NC}         - HAL Access Control Engine"
    echo "    ${CYAN}ambient_forwarder${NC}  - Ambient.ai Event Forwarder"
    echo ""
    echo "  Developer Tools:"
    echo "    ${CYAN}simulate_badge${NC}     - Badge read simulator"
    echo "    ${CYAN}monitor_events${NC}     - Real-time event monitor"
    echo "    ${CYAN}test_ambient${NC}       - Ambient.ai API tester"
    echo "    ${CYAN}hal_logs${NC}           - Log viewer"
    echo "    ${CYAN}hal_status${NC}         - System status"
    echo ""
    echo "  To run tests: ${CYAN}make test${NC}"
    echo "  To start:     ${CYAN}${SCRIPT_DIR}/start_poc.sh${NC}"
    echo ""
}

main "$@"
