#!/bin/bash

# Aether_Access Rebranding Script
# Renames all HAL references to Aether_Access throughout the project

echo "================================================================"
echo " REBRANDING: HAL → Aether_Access"
echo "================================================================"
echo ""
echo "This script will:"
echo "  1. Rename project directory"
echo "  2. Update all file contents"
echo "  3. Rename files"
echo "  4. Update documentation"
echo "  5. Update code references"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Rebranding cancelled."
    exit 1
fi

echo ""
echo "Starting rebranding process..."
echo ""

# Define base paths
PROJECT_ROOT="/Users/mosley/Claude.ai/hal_project"
DOCS_DIR="/Users/mosley/Documents"

# Step 1: Rename Documents folder files
echo "Step 1: Renaming documentation files..."
cd "$DOCS_DIR"

mv "HAL_2.0_DEMO_SCRIPT.md" "AetherAccess_2.0_DEMO_SCRIPT.md" 2>/dev/null
mv "HAL_2.0_PRESENTATION_OUTLINE.md" "AetherAccess_2.0_PRESENTATION_OUTLINE.md" 2>/dev/null
mv "HAL_2.0_QUICK_REFERENCE_CARD.md" "AetherAccess_2.0_QUICK_REFERENCE_CARD.md" 2>/dev/null
mv "HAL_2.0_USER_GUIDE.md" "AetherAccess_2.0_USER_GUIDE.md" 2>/dev/null
mv "HAL_BUILD_2.0_TEST_REPORT.md" "AetherAccess_BUILD_2.0_TEST_REPORT.md" 2>/dev/null
mv "HAL_GUI_COMPLETE_IMPLEMENTATION.md" "AetherAccess_GUI_COMPLETE_IMPLEMENTATION.md" 2>/dev/null

echo "✓ Documentation files renamed"

# Step 2: Update content in all renamed documentation files
echo ""
echo "Step 2: Updating documentation content..."

# Update AetherAccess files
for file in AetherAccess*.md; do
    if [ -f "$file" ]; then
        echo "  Updating $file..."
        # Replace various forms of HAL
        sed -i '' 's/HAL Build 2\.0/Aether_Access Build 2.0/g' "$file"
        sed -i '' 's/HAL 2\.0/Aether_Access 2.0/g' "$file"
        sed -i '' 's/HAL Build/Aether_Access Build/g' "$file"
        sed -i '' 's/HAL Control Panel/Aether_Access Control Panel/g' "$file"
        sed -i '' 's/HAL_BUILD_2\.0/AETHERACCESS_BUILD_2.0/g' "$file"
        sed -i '' 's/HALClient/AetherAccessClient/g' "$file"
        sed -i '' 's/HALAPIClient/AetherAccessAPIClient/g' "$file"
        sed -i '' 's/HALMonitor/AetherAccessMonitor/g' "$file"
        sed -i '' 's/\bHAL\b/Aether_Access/g' "$file"
        sed -i '' 's/hal_project/aetheraccess_project/g' "$file"
        sed -i '' 's/hal_gui_server/aetheraccess_gui_server/g' "$file"
        sed -i '' 's/hal_core/aetheraccess_core/g' "$file"
        sed -i '' 's/hal\.db/aetheraccess.db/g' "$file"
        sed -i '' 's/libhal_core/libaetheraccess_core/g' "$file"
        sed -i '' 's/hal_server/aetheraccess_server/g' "$file"
        sed -i '' 's/hal_build/aetheraccess_build/g' "$file"
    fi
done

echo "✓ Documentation content updated"

# Step 3: Update project files
echo ""
echo "Step 3: Updating project source files..."
cd "$PROJECT_ROOT"

# Update Python files
echo "  Updating Python files..."
find . -name "*.py" -type f ! -path "*/node_modules/*" ! -path "*/.git/*" -exec sed -i '' \
    -e 's/HAL Control Panel/Aether_Access Control Panel/g' \
    -e 's/HAL Build 2\.0/Aether_Access Build 2.0/g' \
    -e 's/HAL_VERSION/AETHERACCESS_VERSION/g' \
    -e 's/HALClient/AetherAccessClient/g' \
    -e 's/hal_core/aetheraccess_core/g' \
    {} \;

# Update C files
echo "  Updating C files..."
find . \( -name "*.c" -o -name "*.h" \) -type f ! -path "*/.git/*" -exec sed -i '' \
    -e 's/HAL_VERSION/AETHERACCESS_VERSION/g' \
    -e 's/HAL Core/Aether_Access Core/g' \
    -e 's/libhal_core/libaetheraccess_core/g' \
    {} \;

# Update CMakeLists.txt
echo "  Updating CMakeLists.txt..."
if [ -f "CMakeLists.txt" ]; then
    sed -i '' \
        -e 's/HAL_BUILD_2\.0/AETHERACCESS_BUILD_2.0/g' \
        -e 's/HAL_VERSION/AETHERACCESS_VERSION/g' \
        -e 's/libhal_core/libaetheraccess_core/g' \
        "CMakeLists.txt"
fi

# Update README.md
echo "  Updating README.md..."
if [ -f "README.md" ]; then
    sed -i '' \
        -e 's/# HAL Build 2\.0/# Aether_Access Build 2.0/g' \
        -e 's/HAL Build 2\.0/Aether_Access Build 2.0/g' \
        -e 's/HAL 2\.0/Aether_Access 2.0/g' \
        -e 's/\*\*HAL Build 2\.0\*\*/\*\*Aether_Access Build 2.0\*\*/g' \
        -e 's/hal_project/aetheraccess_project/g' \
        -e 's/hal_build/aetheraccess_build/g' \
        "README.md"
fi

# Update package.json (frontend)
echo "  Updating frontend package.json..."
if [ -f "gui/frontend/package.json" ]; then
    sed -i '' \
        -e 's/"name": "hal-control-panel"/"name": "aetheraccess-control-panel"/g' \
        -e 's/"HAL Control Panel"/"Aether_Access Control Panel"/g' \
        "gui/frontend/package.json"
fi

# Update TypeScript files
echo "  Updating TypeScript files..."
find gui/frontend/src -name "*.ts" -o -name "*.tsx" -type f -exec sed -i '' \
    -e 's/HAL Control Panel/Aether_Access Control Panel/g' \
    -e 's/HAL API/Aether_Access API/g' \
    -e 's/HALAPIClient/AetherAccessAPIClient/g' \
    {} \;

# Update deployment script
echo "  Updating deployment script..."
if [ -f "deploy_hal_2.0.sh" ]; then
    mv "deploy_hal_2.0.sh" "deploy_aetheraccess_2.0.sh"
    sed -i '' \
        -e 's/HAL Build 2\.0/Aether_Access Build 2.0/g' \
        -e 's/HAL_VERSION/AETHERACCESS_VERSION/g' \
        -e 's/hal_build_2\.0/aetheraccess_build_2.0/g' \
        -e 's/HAL deployment/Aether_Access deployment/g' \
        "deploy_aetheraccess_2.0.sh"
fi

# Update installation guide
echo "  Updating installation guide..."
if [ -f "HAL_BUILD_2.0_INSTALLATION_GUIDE.md" ]; then
    mv "HAL_BUILD_2.0_INSTALLATION_GUIDE.md" "AETHERACCESS_BUILD_2.0_INSTALLATION_GUIDE.md"
    sed -i '' \
        -e 's/HAL Build 2\.0/Aether_Access Build 2.0/g' \
        -e 's/HAL 2\.0/Aether_Access 2.0/g' \
        -e 's/hal_project/aetheraccess_project/g' \
        -e 's/hal_build/aetheraccess_build/g' \
        "AETHERACCESS_BUILD_2.0_INSTALLATION_GUIDE.md"
fi

echo "✓ Project files updated"

# Step 4: Rename project directory
echo ""
echo "Step 4: Renaming project directory..."
cd /Users/mosley/Claude.ai
if [ -d "hal_project" ]; then
    mv "hal_project" "aetheraccess_project"
    echo "✓ Project directory renamed: hal_project → aetheraccess_project"
fi

# Step 5: Update file names in project
echo ""
echo "Step 5: Renaming project files..."
cd "/Users/mosley/Claude.ai/aetheraccess_project"

# Rename Python server file
if [ -f "gui/backend/hal_gui_server_v2.py" ]; then
    mv "gui/backend/hal_gui_server_v2.py" "gui/backend/aetheraccess_gui_server_v2.py"
    echo "✓ Renamed: hal_gui_server_v2.py → aetheraccess_gui_server_v2.py"
fi

# Rename example files
if [ -f "gui/examples/python_client_example.py" ]; then
    # Update imports in example file
    sed -i '' 's/hal_gui_server_v2/aetheraccess_gui_server_v2/g' "gui/examples/python_client_example.py"
fi

# Update startup scripts if they exist
find . -name "start_*.sh" -type f -exec sed -i '' \
    -e 's/hal_gui_server/aetheraccess_gui_server/g' \
    -e 's/HAL Build/Aether_Access Build/g' \
    {} \;

echo "✓ Project files renamed"

# Step 6: Summary
echo ""
echo "================================================================"
echo " REBRANDING COMPLETE!"
echo "================================================================"
echo ""
echo "Changes made:"
echo "  ✓ Project directory: hal_project → aetheraccess_project"
echo "  ✓ Server file: hal_gui_server_v2.py → aetheraccess_gui_server_v2.py"
echo "  ✓ All 'HAL' references → 'Aether_Access'"
echo "  ✓ Documentation files renamed and updated"
echo "  ✓ Source code updated"
echo "  ✓ Configuration files updated"
echo ""
echo "New locations:"
echo "  Project: /Users/mosley/Claude.ai/aetheraccess_project"
echo "  Docs: /Users/mosley/Documents/AetherAccess_*.md"
echo "  Server: gui/backend/aetheraccess_gui_server_v2.py"
echo ""
echo "To start Aether_Access Build 2.0:"
echo "  cd /Users/mosley/Claude.ai/aetheraccess_project/gui/backend"
echo "  python3 aetheraccess_gui_server_v2.py"
echo ""
echo "To start frontend:"
echo "  cd /Users/mosley/Claude.ai/aetheraccess_project/gui/frontend"
echo "  npm run dev"
echo ""
echo "================================================================"
