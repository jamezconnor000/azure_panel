#!/bin/bash
################################################################################
# Rebrand from Aether_Access to Aether_Access
# This script performs a comprehensive rebranding across all files
################################################################################

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}================================================================================${NC}"
echo -e "${BLUE}        Rebranding from Aether_Access to Aether_Access${NC}"
echo -e "${BLUE}================================================================================${NC}"
echo ""

# Check if servers are running and offer to stop them
echo "Checking for running servers..."
if pgrep -f "aetheraccess_gui_server_v2" > /dev/null || pgrep -f "npm run dev" > /dev/null; then
    echo -e "${YELLOW}Warning: Servers appear to be running.${NC}"
    echo "It's recommended to stop them before rebranding."
    read -p "Stop servers now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Stopping servers..."
        pkill -f "aetheraccess_gui_server_v2" 2>/dev/null || true
        pkill -f "npm run dev" 2>/dev/null || true
        pkill -f "uvicorn.*aetheraccess" 2>/dev/null || true
        sleep 2
        echo -e "${GREEN}✓ Servers stopped${NC}"
    fi
fi

echo ""
echo -e "${GREEN}>>> Step 1: Updating project files${NC}"
echo ""

# Function to update file content
update_file() {
    local file=$1
    if [ -f "$file" ]; then
        # Aether_Access variants
        sed -i.bak 's/Aether_Access/Aether_Access/g' "$file"
        sed -i.bak 's/AetherAccess/AetherAccess/g' "$file"
        sed -i.bak 's/AETHERACCESS/AETHERACCESS/g' "$file"
        sed -i.bak 's/aether_access/aether_access/g' "$file"
        sed -i.bak 's/aetheraccess/aetheraccess/g' "$file"

        # Also update any remaining HAL references
        sed -i.bak 's/HAL Build 2\.0/Aether_Access Build 2.0/g' "$file"
        sed -i.bak 's/HAL 2\.0/Aether_Access 2.0/g' "$file"
        sed -i.bak 's/HAL Control Panel/Aether_Access Control Panel/g' "$file"
        sed -i.bak 's/hal-control-panel/aether-access-control-panel/g' "$file"

        rm "${file}.bak" 2>/dev/null || true
        echo "  Updated: $file"
    fi
}

# Update Python files
echo "Updating Python files..."
find . -type f -name "*.py" ! -path "*/\.*" ! -path "*/node_modules/*" ! -path "*/build/*" | while read file; do
    update_file "$file"
done

# Update Markdown files
echo "Updating Markdown files..."
find . -type f -name "*.md" ! -path "*/\.*" ! -path "*/node_modules/*" | while read file; do
    update_file "$file"
done

# Update Shell scripts
echo "Updating shell scripts..."
find . -type f -name "*.sh" ! -path "*/\.*" | while read file; do
    update_file "$file"
done

# Update JSON files
echo "Updating JSON files..."
find . -type f -name "*.json" ! -path "*/\.*" ! -path "*/node_modules/*" ! -path "*/package-lock.json" | while read file; do
    update_file "$file"
done

# Update CMakeLists.txt
echo "Updating CMakeLists.txt..."
if [ -f "CMakeLists.txt" ]; then
    update_file "CMakeLists.txt"
fi

# Update README
if [ -f "README.md" ]; then
    update_file "README.md"
fi

# Update TypeScript/JavaScript files
echo "Updating TypeScript/JavaScript files..."
find gui/frontend/src -type f \( -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" \) 2>/dev/null | while read file; do
    update_file "$file"
done

echo ""
echo -e "${GREEN}>>> Step 2: Renaming files${NC}"
echo ""

# Rename Python server file
if [ -f "gui/backend/aetheraccess_gui_server_v2.py" ]; then
    mv gui/backend/aetheraccess_gui_server_v2.py gui/backend/aetheraccess_gui_server_v2.py
    echo "  Renamed: aetheraccess_gui_server_v2.py -> aetheraccess_gui_server_v2.py"
fi

# Rename deployment script
if [ -f "deploy_aetheraccess_2.0.sh" ]; then
    mv deploy_aetheraccess_2.0.sh deploy_aetheraccess_2.0.sh
    echo "  Renamed: deploy_aetheraccess_2.0.sh -> deploy_aetheraccess_2.0.sh"
fi

# Rename installation guide
if [ -f "AETHERACCESS_BUILD_2.0_INSTALLATION_GUIDE.md" ]; then
    mv AETHERACCESS_BUILD_2.0_INSTALLATION_GUIDE.md AETHERACCESS_BUILD_2.0_INSTALLATION_GUIDE.md
    echo "  Renamed: AETHERACCESS_BUILD_2.0_INSTALLATION_GUIDE.md -> AETHERACCESS_BUILD_2.0_INSTALLATION_GUIDE.md"
fi

echo ""
echo -e "${GREEN}>>> Step 3: Updating documentation in /Users/mosley/Documents/${NC}"
echo ""

DOCS_DIR="/Users/mosley/Documents"

# Update and rename documentation files
declare -A doc_files=(
    ["AetherAccess_2.0_USER_GUIDE.md"]="AetherAccess_2.0_USER_GUIDE.md"
    ["AetherAccess_2.0_QUICK_REFERENCE_CARD.md"]="AetherAccess_2.0_QUICK_REFERENCE_CARD.md"
    ["AetherAccess_2.0_DEMO_SCRIPT.md"]="AetherAccess_2.0_DEMO_SCRIPT.md"
    ["AetherAccess_2.0_PRESENTATION_OUTLINE.md"]="AetherAccess_2.0_PRESENTATION_OUTLINE.md"
    ["AetherAccess_BUILD_2.0_TEST_REPORT.md"]="AetherAccess_BUILD_2.0_TEST_REPORT.md"
    ["AetherAccess_GUI_COMPLETE_IMPLEMENTATION.md"]="AetherAccess_GUI_COMPLETE_IMPLEMENTATION.md"
    ["AetherAccess_REBRANDING_SUMMARY.md"]="AetherAccess_REBRANDING_SUMMARY.md"
    ["AetherAccess_TECHNICAL_ANALYSIS.txt"]="AetherAccess_TECHNICAL_ANALYSIS.txt"
    ["AetherAccess_COST_AND_PROPRIETARY_ANALYSIS.txt"]="AetherAccess_COST_AND_PROPRIETARY_ANALYSIS.txt"
    ["AetherAccess_2.0_Presentation.pptx"]="AetherAccess_2.0_Presentation.pptx"
)

for old_name in "${!doc_files[@]}"; do
    new_name="${doc_files[$old_name]}"
    if [ -f "$DOCS_DIR/$old_name" ]; then
        # Update content first
        update_file "$DOCS_DIR/$old_name"
        # Then rename
        mv "$DOCS_DIR/$old_name" "$DOCS_DIR/$new_name"
        echo "  Renamed: $old_name -> $new_name"
    fi
done

echo ""
echo -e "${GREEN}>>> Step 4: Renaming project directory${NC}"
echo ""

cd /Users/mosley/Claude.ai

if [ -d "aetheraccess_project" ]; then
    # If aetheraccess_project already exists, remove it
    if [ -d "aetheraccess_project" ]; then
        echo "  Removing existing aetheraccess_project directory..."
        rm -rf aetheraccess_project
    fi

    echo "  Moving aetheraccess_project -> aetheraccess_project"
    mv aetheraccess_project aetheraccess_project
    echo -e "${GREEN}✓ Project directory renamed${NC}"
fi

echo ""
echo -e "${GREEN}>>> Step 5: Updating references in new location${NC}"
echo ""

cd aetheraccess_project

# Update any remaining file references
find . -type f \( -name "*.py" -o -name "*.md" -o -name "*.sh" -o -name "*.json" \) ! -path "*/\.*" ! -path "*/node_modules/*" ! -path "*/build/*" ! -path "*/package-lock.json" -exec sed -i.bak 's/aetheraccess_project/aetheraccess_project/g' {} \;
find . -name "*.bak" -delete

echo ""
echo -e "${BLUE}================================================================================${NC}"
echo -e "${BLUE}                    Rebranding Complete!${NC}"
echo -e "${BLUE}================================================================================${NC}"
echo ""
echo -e "${GREEN}✓ All files updated${NC}"
echo -e "${GREEN}✓ Files renamed${NC}"
echo -e "${GREEN}✓ Documentation updated${NC}"
echo -e "${GREEN}✓ Project directory renamed${NC}"
echo ""
echo "New locations:"
echo "  Project: /Users/mosley/Claude.ai/aetheraccess_project"
echo "  Server: gui/backend/aetheraccess_gui_server_v2.py"
echo "  Docs: /Users/mosley/Documents/AetherAccess_*.md"
echo ""
echo "To start the system:"
echo "  cd /Users/mosley/Claude.ai/aetheraccess_project/gui/backend"
echo "  python3 -m uvicorn aetheraccess_gui_server_v2:app --host 0.0.0.0 --port 8080"
echo ""
echo "  cd /Users/mosley/Claude.ai/aetheraccess_project/gui/frontend"
echo "  npm run dev"
echo ""
