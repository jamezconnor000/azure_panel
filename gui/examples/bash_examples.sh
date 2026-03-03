#!/bin/bash
################################################################################
# HAL GUI API - Bash/curl Examples
# Demonstrates command-line integration with the HAL Control Panel API
################################################################################

API_BASE="http://localhost:8080/api/v1"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "================================================================================"
echo "                    HAL Control Panel - Bash/curl Examples"
echo "================================================================================"
echo ""

# =============================================================================
# Azure Panel I/O Monitoring
# =============================================================================

echo -e "${BLUE}1. Getting Panel I/O Status...${NC}"
curl -s "$API_BASE/panels/1/io" | python3 -m json.tool
echo ""

echo -e "${BLUE}2. Getting Panel Health...${NC}"
curl -s "$API_BASE/panels/1/health" | python3 -m json.tool
echo ""

# =============================================================================
# Reader Health Monitoring
# =============================================================================

echo -e "${BLUE}3. Getting Reader Health...${NC}"
curl -s "$API_BASE/readers/1/health" | python3 -m json.tool
echo ""

echo -e "${BLUE}4. Getting All Readers Health Summary...${NC}"
curl -s "$API_BASE/readers/health/summary" | python3 -m json.tool
echo ""

# =============================================================================
# Door Control
# =============================================================================

echo -e "${BLUE}5. Unlocking Door (indefinitely)...${NC}"
curl -s -X POST "$API_BASE/doors/1/unlock" | python3 -m json.tool
echo ""

echo -e "${BLUE}6. Unlocking Door (5 seconds - momentary)...${NC}"
curl -s -X POST "$API_BASE/doors/1/unlock?duration_seconds=5" | python3 -m json.tool
echo ""

echo -e "${BLUE}7. Unlocking Door (with reason)...${NC}"
curl -s -X POST "$API_BASE/doors/1/unlock?duration_seconds=5&reason=VIP+visitor" | python3 -m json.tool
echo ""

echo -e "${BLUE}8. Locking Door...${NC}"
curl -s -X POST "$API_BASE/doors/1/lock" | python3 -m json.tool
echo ""

echo -e "${BLUE}9. Door Lockdown...${NC}"
curl -s -X POST "$API_BASE/doors/1/lockdown" \
  -H "Content-Type: application/json" \
  -d '{"reason": "Emergency lockdown test"}' | python3 -m json.tool
echo ""

echo -e "${BLUE}10. Release Door (return to normal)...${NC}"
curl -s -X POST "$API_BASE/doors/1/release" | python3 -m json.tool
echo ""

# =============================================================================
# Output Control
# =============================================================================

echo -e "${BLUE}11. Activating Output (indefinitely)...${NC}"
curl -s -X POST "$API_BASE/outputs/1/activate" | python3 -m json.tool
echo ""

echo -e "${BLUE}12. Pulsing Output (2 seconds)...${NC}"
curl -s -X POST "$API_BASE/outputs/1/pulse?duration_ms=2000" | python3 -m json.tool
echo ""

echo -e "${BLUE}13. Deactivating Output...${NC}"
curl -s -X POST "$API_BASE/outputs/1/deactivate" | python3 -m json.tool
echo ""

echo -e "${BLUE}14. Toggling Output...${NC}"
curl -s -X POST "$API_BASE/outputs/1/toggle" | python3 -m json.tool
echo ""

# =============================================================================
# Relay Control
# =============================================================================

echo -e "${BLUE}15. Activating Relay...${NC}"
curl -s -X POST "$API_BASE/relays/1/activate" | python3 -m json.tool
echo ""

echo -e "${BLUE}16. Activating Relay (2 second pulse)...${NC}"
curl -s -X POST "$API_BASE/relays/1/activate?duration_ms=2000" | python3 -m json.tool
echo ""

echo -e "${BLUE}17. Deactivating Relay...${NC}"
curl -s -X POST "$API_BASE/relays/1/deactivate" | python3 -m json.tool
echo ""

# =============================================================================
# Mass Control (Emergency Operations)
# =============================================================================

echo -e "${YELLOW}18. Emergency Lockdown (ALL DOORS)...${NC}"
curl -s -X POST "$API_BASE/control/lockdown" \
  -H "Content-Type: application/json" \
  -d '{"reason": "Active shooter drill", "initiated_by": "Security Director"}' | python3 -m json.tool
echo ""

echo -e "${YELLOW}19. Emergency Unlock All (Evacuation)...${NC}"
curl -s -X POST "$API_BASE/control/unlock-all" \
  -H "Content-Type: application/json" \
  -d '{"reason": "Fire evacuation drill", "initiated_by": "Fire Marshal"}' | python3 -m json.tool
echo ""

echo -e "${GREEN}20. Return to Normal Operation...${NC}"
curl -s -X POST "$API_BASE/control/normal" \
  -H "Content-Type: application/json" \
  -d '{"initiated_by": "Security Director"}' | python3 -m json.tool
echo ""

# =============================================================================
# Control Macros
# =============================================================================

echo -e "${BLUE}21. Listing Available Macros...${NC}"
curl -s "$API_BASE/macros" | python3 -m json.tool
echo ""

echo -e "${BLUE}22. Executing Macro (Emergency Lockdown)...${NC}"
curl -s -X POST "$API_BASE/macros/1/execute" \
  -H "Content-Type: application/json" \
  -d '{"initiated_by": "Admin"}' | python3 -m json.tool
echo ""

echo -e "${BLUE}23. Executing Macro (Morning Unlock)...${NC}"
curl -s -X POST "$API_BASE/macros/4/execute" \
  -H "Content-Type: application/json" \
  -d '{"initiated_by": "Admin"}' | python3 -m json.tool
echo ""

# =============================================================================
# Override Management
# =============================================================================

echo -e "${BLUE}24. Getting Active Overrides...${NC}"
curl -s "$API_BASE/overrides" | python3 -m json.tool
echo ""

# Uncomment to clear an override
# echo -e "${BLUE}25. Clearing Override...${NC}"
# curl -s -X DELETE "$API_BASE/overrides/1" | python3 -m json.tool
# echo ""

echo "================================================================================"
echo "                              Examples Complete"
echo "================================================================================"
