#!/bin/bash
#
# HAL Deployment Package Creator
# Creates a complete, ready-to-deploy package for Azure Panel
#

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PACKAGE_NAME="hal_azure_panel_deployment_$(date +%Y%m%d_%H%M%S)"
PACKAGE_DIR="/tmp/${PACKAGE_NAME}"
ARCHIVE_PATH="${HOME}/Desktop/${PACKAGE_NAME}.tar.gz"

echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                              ║"
echo "║              HAL DEPLOYMENT PACKAGE CREATOR                                  ║"
echo "║                                                                              ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""

echo "Creating deployment package: ${PACKAGE_NAME}"
echo ""

# Create package directory
echo "Step 1: Creating package directory..."
mkdir -p "${PACKAGE_DIR}"

# Copy entire hal_project
echo "Step 2: Copying HAL project files..."
cp -r "${SCRIPT_DIR}"/* "${PACKAGE_DIR}/" 2>/dev/null || true

# Remove build artifacts
echo "Step 3: Cleaning build artifacts..."
rm -rf "${PACKAGE_DIR}/build"
rm -rf "${PACKAGE_DIR}/CMakeFiles"
rm -f "${PACKAGE_DIR}/CMakeCache.txt"
rm -f "${PACKAGE_DIR}"/cmake_install.cmake
rm -f "${PACKAGE_DIR}"/Makefile
rm -f "${PACKAGE_DIR}"/*.a
rm -f "${PACKAGE_DIR}"/test_*
rm -f "${PACKAGE_DIR}"/example_*
rm -f "${PACKAGE_DIR}"/complete_sdk_demo
rm -f "${PACKAGE_DIR}"/create_azure_configs
rm -f "${PACKAGE_DIR}"/hal_event_export_daemon
rm -f "${PACKAGE_DIR}"/.hal_*.pid

# Copy documentation from Documents folder
echo "Step 4: Copying documentation..."
mkdir -p "${PACKAGE_DIR}/documentation"
cp ~/Documents/HAL_*.txt "${PACKAGE_DIR}/documentation/" 2>/dev/null || true
cp ~/Documents/HAL_*.json "${PACKAGE_DIR}/documentation/" 2>/dev/null || true

# Create README for the package
echo "Step 5: Creating deployment README..."
cat > "${PACKAGE_DIR}/README_DEPLOYMENT.txt" << 'EOF'
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║                   HAL AZURE PANEL DEPLOYMENT PACKAGE                         ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

PACKAGE CONTENTS
────────────────────────────────────────────────────────────────────────────────

This package contains everything needed to deploy HAL to Azure Access
Technology BLU-IC2 panels.

DIRECTORY STRUCTURE:

hal_azure_panel_deployment_YYYYMMDD_HHMMSS/
├── README_DEPLOYMENT.txt          ← This file
├── QUICK_START.txt                ← 5-minute deployment guide
├── documentation/                 ← Complete documentation
│   ├── HAL_Complete_System_Guide.txt
│   ├── HAL_Deployment_Files.txt
│   ├── HAL_OSDP_Implementation_Guide.txt
│   ├── HAL_Feedback_Loop_Guide.txt
│   ├── HAL_Quick_Start_Azure_Panel.txt
│   ├── HAL_Basic_Config.json
│   ├── HAL_OfficeBuilding_Config.json
│   └── HAL_Warehouse_Config.json
├── include/                       ← Public header files
├── src/                          ← Source code
│   ├── hal_core/                 ← Core HAL implementation
│   ├── sdk_modules/              ← Azure SDK modules
│   └── utils/                    ← Utility functions
├── api/                          ← REST API server (Python)
├── config/                       ← Configuration files
├── schema/                       ← Database schemas
├── tests/                        ← Test programs
├── tools/                        ← Deployment tools
│   └── hal_feedback_loop.py     ← Diagnostic collector
├── systemd/                      ← Systemd service files
├── scripts/                      ← Build/deployment scripts
├── start_hal_system.sh           ← Start script
├── stop_hal_system.sh            ← Stop script
├── status_hal_system.sh          ← Status checker
├── docker-compose.yml            ← Docker deployment
├── Dockerfile.api                ← API server container
├── Dockerfile.export             ← Event export container
└── CMakeLists.txt               ← Build configuration


QUICK DEPLOYMENT (5 MINUTES)
────────────────────────────────────────────────────────────────────────────────

1. COPY TO AZURE PANEL:

   scp -r hal_azure_panel_deployment_*/ azurepanel:/opt/hal/

2. SSH TO PANEL AND BUILD:

   ssh azurepanel
   cd /opt/hal
   cmake .
   make

3. CONFIGURE:

   nano config/hal_config.json
   # Update ambient_ai.api_key with your API key

4. START:

   ./start_hal_system.sh

5. VERIFY:

   ./status_hal_system.sh
   curl http://localhost:8080/


WHAT THIS PACKAGE PROVIDES
────────────────────────────────────────────────────────────────────────────────

✓ REST API Server (port 8080) - Inbound commands from external systems
✓ Event Export Daemon - Outbound events to Ambient.ai/SIEM
✓ OSDP Reader Support - Modern card reader protocol
✓ Diagnostic Logging - Comprehensive error tracking
✓ Feedback Loop Tool - Automated debugging with Claude
✓ JSON Configuration - Ready-to-import access control configs
✓ Complete Documentation - Everything explained


DOCUMENTATION
────────────────────────────────────────────────────────────────────────────────

READ THESE FIRST:

1. documentation/HAL_Quick_Start_Azure_Panel.txt
   - 5-minute deployment guide
   - First-time setup instructions
   - Common issues and fixes

2. documentation/HAL_Complete_System_Guide.txt
   - Complete system overview
   - Architecture details
   - Configuration reference

3. documentation/HAL_Feedback_Loop_Guide.txt
   - How to use diagnostic reporting
   - Send reports to Claude for automated fixes
   - Troubleshooting guide

SPECIALIZED TOPICS:

4. documentation/HAL_OSDP_Implementation_Guide.txt
   - OSDP reader setup
   - Serial port configuration
   - Wiegand to OSDP migration

5. documentation/HAL_Deployment_Files.txt
   - Detailed file manifest
   - Deployment options
   - Production considerations


PRE-BUILT CONFIGURATIONS
────────────────────────────────────────────────────────────────────────────────

Three ready-to-import JSON configurations:

1. HAL_Basic_Config.json
   - 2 doors, 5 cards
   - Good for testing/proof of concept

2. HAL_OfficeBuilding_Config.json
   - 10 doors, 50 cards, 3 floors
   - Production office building setup

3. HAL_Warehouse_Config.json
   - 8 doors, 25 cards
   - Industrial/warehouse setup

Import via: Azure Panel → IntegrationApp → Import JConfig


DEPLOYMENT OPTIONS
────────────────────────────────────────────────────────────────────────────────

OPTION 1: Standalone Scripts (Recommended for First Deployment)
  ./start_hal_system.sh

OPTION 2: Systemd Service (Recommended for Production)
  sudo cp systemd/hal-system.service /etc/systemd/system/
  sudo systemctl enable hal-system
  sudo systemctl start hal-system

OPTION 3: Docker Compose
  docker-compose up -d


TROUBLESHOOTING
────────────────────────────────────────────────────────────────────────────────

If you encounter ANY issues:

1. Collect diagnostic report:
   python3 tools/hal_feedback_loop.py --report /tmp/feedback.txt

2. Copy to your Mac:
   scp azurepanel:/tmp/feedback.txt ~/Desktop/

3. Send to Claude:
   "I deployed HAL and encountered [issue]. Here's the feedback report:
   [paste feedback.txt]
   Please analyze and provide fixes."

4. Claude will provide specific fixes


SYSTEM REQUIREMENTS
────────────────────────────────────────────────────────────────────────────────

Software:
  • Linux (Ubuntu 20.04+, Debian 10+, or similar)
  • Python 3.6+
  • CMake 3.10+
  • GCC/Clang C compiler
  • SQLite3
  • libcurl4
  • 100MB disk space

Hardware:
  • Azure Access Technology BLU-IC2 Panel
  • 256MB RAM minimum
  • Network connectivity


SUPPORT
────────────────────────────────────────────────────────────────────────────────

For issues, questions, or improvements, use the feedback loop tool to
collect diagnostics and send to Claude for analysis.


VERSION INFORMATION
────────────────────────────────────────────────────────────────────────────────

HAL Version: 1.0.0
Package Created: [Automatically timestamped in filename]
Compatible with: Azure Access Technology BLU-IC2

Includes:
  ✓ REST API Server
  ✓ Event Export Daemon
  ✓ OSDP Reader Support
  ✓ Diagnostic Logging
  ✓ Feedback Loop Tool
  ✓ Complete Documentation


NEXT STEPS
────────────────────────────────────────────────────────────────────────────────

1. Read documentation/HAL_Quick_Start_Azure_Panel.txt
2. Copy package to Azure Panel
3. Build and configure
4. Start system
5. Test with provided configurations
6. Deploy to production


═════════════════════════════════════════════════════════════════════════════════
Ready to Deploy - Everything Included
═════════════════════════════════════════════════════════════════════════════════
EOF

# Create quick start guide
echo "Step 6: Creating quick start guide..."
cat > "${PACKAGE_DIR}/QUICK_START.txt" << 'EOF'
HAL AZURE PANEL - 5 MINUTE QUICK START

1. COPY TO PANEL:
   scp -r hal_azure_panel_deployment_*/ azurepanel:/opt/hal/

2. BUILD:
   ssh azurepanel
   cd /opt/hal
   cmake . && make

3. CONFIGURE:
   nano config/hal_config.json
   # Set ambient_ai.api_key

4. START:
   ./start_hal_system.sh

5. VERIFY:
   ./status_hal_system.sh
   curl http://localhost:8080/

DONE! See README_DEPLOYMENT.txt for complete documentation.
EOF

# Create deployment checklist
echo "Step 7: Creating deployment checklist..."
cat > "${PACKAGE_DIR}/DEPLOYMENT_CHECKLIST.txt" << 'EOF'
HAL DEPLOYMENT CHECKLIST

PRE-DEPLOYMENT:
☐ Azure Panel accessible via SSH
☐ Panel has Python 3.6+ installed
☐ Panel has CMake and GCC installed
☐ Panel has SQLite3 installed
☐ Ambient.ai API key obtained
☐ Network connectivity verified

DEPLOYMENT:
☐ Package copied to /opt/hal/
☐ CMake configuration successful
☐ Build completed without errors
☐ Configuration file updated
☐ Databases created (hal_sdk.db, hal_cards.db)
☐ Logs directory created
☐ start_hal_system.sh is executable

VERIFICATION:
☐ REST API server running (check with status script)
☐ Event export daemon running
☐ Port 8080 accessible
☐ Can query API: curl http://localhost:8080/
☐ Can view logs: tail -f logs/hal_diagnostic.log
☐ No errors in logs

CONFIGURATION:
☐ Access points configured
☐ Readers configured (Wiegand or OSDP)
☐ Cards imported
☐ Ambient.ai integration tested

POST-DEPLOYMENT:
☐ Test card read generates event
☐ Event exported to Ambient.ai
☐ API can add/query cards
☐ Relays can be controlled
☐ System survives restart

PRODUCTION:
☐ Systemd service installed (optional)
☐ Log rotation configured
☐ Database backups scheduled
☐ Monitoring configured
☐ Documentation reviewed by team
EOF

# Create file manifest
echo "Step 8: Creating file manifest..."
find "${PACKAGE_DIR}" -type f > "${PACKAGE_DIR}/FILE_MANIFEST.txt"

# Create package info
echo "Step 9: Creating package info..."
cat > "${PACKAGE_DIR}/PACKAGE_INFO.txt" << EOF
HAL Azure Panel Deployment Package

Package Name: ${PACKAGE_NAME}
Created: $(date)
Created By: Automated packaging script
Platform: Azure Access Technology BLU-IC2
Version: 1.0.0

Total Files: $(find "${PACKAGE_DIR}" -type f | wc -l)
Total Size: $(du -sh "${PACKAGE_DIR}" | cut -f1)

Components:
  - HAL Core (C library)
  - REST API Server (Python/FastAPI)
  - Event Export Daemon (C binary)
  - OSDP Reader Support
  - Diagnostic Logger
  - Feedback Loop Tool
  - Complete Documentation
  - Pre-built Configurations
  - Deployment Scripts

Ready to deploy to Azure Panel.
EOF

# Create archive
echo "Step 10: Creating compressed archive..."
cd /tmp
tar -czf "${ARCHIVE_PATH}" "${PACKAGE_NAME}"

# Cleanup temporary directory
echo "Step 11: Cleaning up..."
rm -rf "${PACKAGE_DIR}"

# Calculate size
ARCHIVE_SIZE=$(du -h "${ARCHIVE_PATH}" | cut -f1)

echo ""
echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                              ║"
echo "║              DEPLOYMENT PACKAGE CREATED SUCCESSFULLY                         ║"
echo "║                                                                              ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "Package: ${ARCHIVE_PATH}"
echo "Size: ${ARCHIVE_SIZE}"
echo ""
echo "NEXT STEPS:"
echo ""
echo "1. Extract on Azure Panel:"
echo "   scp ${ARCHIVE_PATH} azurepanel:/tmp/"
echo "   ssh azurepanel"
echo "   cd /tmp"
echo "   tar -xzf ${PACKAGE_NAME}.tar.gz"
echo "   sudo mv ${PACKAGE_NAME} /opt/hal"
echo ""
echo "2. Read the documentation:"
echo "   cat /opt/hal/QUICK_START.txt"
echo ""
echo "3. Build and deploy:"
echo "   cd /opt/hal"
echo "   cmake . && make"
echo "   ./start_hal_system.sh"
echo ""
echo "Package is ready for deployment!"
echo ""
