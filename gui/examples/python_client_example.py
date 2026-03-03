#!/usr/bin/env python3
"""
HAL GUI API - Python Client Example
Demonstrates how to integrate with the Aether_Access Control Panel API
"""

import requests
import json
from typing import Dict, List, Optional
from datetime import datetime

class AetherAccessClient:
    """Python client for Aether_Access Control Panel API"""

    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api/v1"

    # =============================================================================
    # Azure Panel I/O Monitoring
    # =============================================================================

    def get_panel_io(self, panel_id: int) -> Dict:
        """Get complete I/O status for an Azure panel"""
        response = requests.get(f"{self.api_base}/panels/{panel_id}/io")
        response.raise_for_status()
        return response.json()

    def get_panel_health(self, panel_id: int) -> Dict:
        """Get panel health metrics"""
        response = requests.get(f"{self.api_base}/panels/{panel_id}/health")
        response.raise_for_status()
        return response.json()

    # =============================================================================
    # Reader Health Monitoring
    # =============================================================================

    def get_reader_health(self, reader_id: int) -> Dict:
        """Get comprehensive reader health assessment"""
        response = requests.get(f"{self.api_base}/readers/{reader_id}/health")
        response.raise_for_status()
        return response.json()

    def get_all_readers_health(self) -> Dict:
        """Get health summary for all readers"""
        response = requests.get(f"{self.api_base}/readers/health/summary")
        response.raise_for_status()
        return response.json()

    # =============================================================================
    # Door Control
    # =============================================================================

    def unlock_door(self, door_id: int, duration_seconds: Optional[int] = None,
                    reason: Optional[str] = None) -> Dict:
        """Unlock a door (momentary or indefinite)"""
        params = {}
        if duration_seconds:
            params["duration_seconds"] = duration_seconds
        if reason:
            params["reason"] = reason

        response = requests.post(
            f"{self.api_base}/doors/{door_id}/unlock",
            params=params
        )
        response.raise_for_status()
        return response.json()

    def lock_door(self, door_id: int, reason: Optional[str] = None) -> Dict:
        """Lock a door"""
        params = {}
        if reason:
            params["reason"] = reason

        response = requests.post(
            f"{self.api_base}/doors/{door_id}/lock",
            params=params
        )
        response.raise_for_status()
        return response.json()

    def lockdown_door(self, door_id: int, reason: str) -> Dict:
        """Put door in lockdown mode"""
        response = requests.post(
            f"{self.api_base}/doors/{door_id}/lockdown",
            json={"reason": reason}
        )
        response.raise_for_status()
        return response.json()

    def release_door(self, door_id: int) -> Dict:
        """Release door lockdown/unlock - return to normal"""
        response = requests.post(f"{self.api_base}/doors/{door_id}/release")
        response.raise_for_status()
        return response.json()

    # =============================================================================
    # Output Control
    # =============================================================================

    def activate_output(self, output_id: int, duration_ms: Optional[int] = None) -> Dict:
        """Activate an output (with optional pulse duration)"""
        params = {}
        if duration_ms:
            params["duration_ms"] = duration_ms

        response = requests.post(
            f"{self.api_base}/outputs/{output_id}/activate",
            params=params
        )
        response.raise_for_status()
        return response.json()

    def deactivate_output(self, output_id: int) -> Dict:
        """Deactivate an output"""
        response = requests.post(f"{self.api_base}/outputs/{output_id}/deactivate")
        response.raise_for_status()
        return response.json()

    def pulse_output(self, output_id: int, duration_ms: int = 1000) -> Dict:
        """Pulse an output for specified duration"""
        response = requests.post(
            f"{self.api_base}/outputs/{output_id}/pulse",
            params={"duration_ms": duration_ms}
        )
        response.raise_for_status()
        return response.json()

    def toggle_output(self, output_id: int) -> Dict:
        """Toggle output state"""
        response = requests.post(f"{self.api_base}/outputs/{output_id}/toggle")
        response.raise_for_status()
        return response.json()

    # =============================================================================
    # Relay Control
    # =============================================================================

    def activate_relay(self, relay_id: int, duration_ms: Optional[int] = None) -> Dict:
        """Activate a relay"""
        params = {}
        if duration_ms:
            params["duration_ms"] = duration_ms

        response = requests.post(
            f"{self.api_base}/relays/{relay_id}/activate",
            params=params
        )
        response.raise_for_status()
        return response.json()

    def deactivate_relay(self, relay_id: int) -> Dict:
        """Deactivate a relay"""
        response = requests.post(f"{self.api_base}/relays/{relay_id}/deactivate")
        response.raise_for_status()
        return response.json()

    # =============================================================================
    # Mass Control (Emergency Operations)
    # =============================================================================

    def emergency_lockdown(self, reason: str, initiated_by: str = "Python Client") -> Dict:
        """EMERGENCY LOCKDOWN - Lock all doors"""
        response = requests.post(
            f"{self.api_base}/control/lockdown",
            json={"reason": reason, "initiated_by": initiated_by}
        )
        response.raise_for_status()
        return response.json()

    def emergency_unlock_all(self, reason: str, initiated_by: str = "Python Client") -> Dict:
        """EMERGENCY UNLOCK ALL - Unlock all doors for evacuation"""
        response = requests.post(
            f"{self.api_base}/control/unlock-all",
            json={"reason": reason, "initiated_by": initiated_by}
        )
        response.raise_for_status()
        return response.json()

    def return_to_normal(self, initiated_by: str = "Python Client") -> Dict:
        """Return all systems to normal operation"""
        response = requests.post(
            f"{self.api_base}/control/normal",
            json={"initiated_by": initiated_by}
        )
        response.raise_for_status()
        return response.json()

    # =============================================================================
    # Control Macros
    # =============================================================================

    def list_macros(self) -> Dict:
        """List all available control macros"""
        response = requests.get(f"{self.api_base}/macros")
        response.raise_for_status()
        return response.json()

    def execute_macro(self, macro_id: int, initiated_by: str = "Python Client") -> Dict:
        """Execute a control macro"""
        response = requests.post(
            f"{self.api_base}/macros/{macro_id}/execute",
            json={"initiated_by": initiated_by}
        )
        response.raise_for_status()
        return response.json()

    # =============================================================================
    # Override Management
    # =============================================================================

    def get_active_overrides(self) -> List[Dict]:
        """Get all active I/O overrides"""
        response = requests.get(f"{self.api_base}/overrides")
        response.raise_for_status()
        return response.json()

    def clear_override(self, override_id: int) -> Dict:
        """Clear an I/O override"""
        response = requests.delete(f"{self.api_base}/overrides/{override_id}")
        response.raise_for_status()
        return response.json()


# =============================================================================
# Example Usage
# =============================================================================

def main():
    """Demonstrate HAL API usage"""

    client = AetherAccessClient()

    print("="*80)
    print(" Aether_Access Control Panel - Python Client Examples".center(80))
    print("="*80)
    print()

    # Example 1: Check panel I/O status
    print("1. Getting Panel I/O Status...")
    try:
        io_status = client.get_panel_io(panel_id=1)
        print(f"   Panel: {io_status['panel_name']}")
        print(f"   Inputs: {len(io_status['inputs'])}")
        print(f"   Outputs: {len(io_status['outputs'])}")
        print(f"   Relays: {len(io_status['relays'])}")
        print(f"   Total events today: {io_status['total_events_today']}")
        print()
    except Exception as e:
        print(f"   Error: {e}")
        print()

    # Example 2: Get reader health
    print("2. Getting Reader Health...")
    try:
        health = client.get_reader_health(reader_id=1)
        print(f"   Reader: {health['reader_name']}")
        print(f"   Overall Health: {health['overall_health']}")
        print(f"   Health Score: {health['health_score']}/100")
        print(f"   Comm Health: {health['comm_health']}")
        print(f"   SC Health: {health['sc_health']}")
        print(f"   Hardware Health: {health['hardware_health']}")
        print()
    except Exception as e:
        print(f"   Error: {e}")
        print()

    # Example 3: Unlock door (momentary)
    print("3. Unlocking Door (5 seconds)...")
    try:
        result = client.unlock_door(door_id=1, duration_seconds=5, reason="Demo test")
        print(f"   Success: {result['success']}")
        print(f"   Message: {result['message']}")
        print()
    except Exception as e:
        print(f"   Error: {e}")
        print()

    # Example 4: Pulse output
    print("4. Pulsing Output (2 seconds)...")
    try:
        result = client.pulse_output(output_id=1, duration_ms=2000)
        print(f"   Success: {result['success']}")
        print(f"   Message: {result['message']}")
        print()
    except Exception as e:
        print(f"   Error: {e}")
        print()

    # Example 5: List macros
    print("5. Available Control Macros...")
    try:
        macros = client.list_macros()
        for macro in macros['macros']:
            print(f"   [{macro['macro_id']}] {macro['name']}")
            print(f"       {macro['description']}")
        print()
    except Exception as e:
        print(f"   Error: {e}")
        print()

    # Example 6: Get active overrides
    print("6. Active I/O Overrides...")
    try:
        overrides = client.get_active_overrides()
        if overrides:
            for override in overrides:
                print(f"   Override {override['override_id']}: {override['target_name']}")
                print(f"   State: {override['override_state']}")
                print(f"   Reason: {override['reason']}")
        else:
            print("   No active overrides")
        print()
    except Exception as e:
        print(f"   Error: {e}")
        print()

    print("="*80)
    print(" Examples Complete".center(80))
    print("="*80)


if __name__ == "__main__":
    main()
