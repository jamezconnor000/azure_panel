#!/usr/bin/env python3
"""
HAL Monitoring Dashboard - Practical Integration Example
Real-time monitoring dashboard using the HAL API
Demonstrates continuous monitoring and alerting
"""

import requests
import time
import json
from datetime import datetime
from typing import Dict, List
import sys

class HALMonitor:
    """Real-time monitoring dashboard for HAL system"""

    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api/v1"
        self.running = False

        # Thresholds for alerts
        self.health_threshold = 75  # Alert if health score below this
        self.comm_uptime_threshold = 95.0  # Alert if uptime below this
        self.response_time_threshold = 100.0  # Alert if avg response > this ms

    def clear_screen(self):
        """Clear terminal screen"""
        print("\033[2J\033[H", end="")

    def print_header(self):
        """Print dashboard header"""
        print("=" * 80)
        print(" HAL MONITORING DASHBOARD".center(80))
        print("=" * 80)
        print(f" Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}".ljust(80))
        print("=" * 80)
        print()

    def get_health_indicator(self, health: str) -> str:
        """Get colored health indicator"""
        indicators = {
            "excellent": "🟢 EXCELLENT",
            "good": "🟡 GOOD",
            "fair": "🟠 FAIR",
            "poor": "🔴 POOR",
            "critical": "🔴 CRITICAL"
        }
        return indicators.get(health.lower(), "⚪ UNKNOWN")

    def monitor_readers(self) -> List[Dict]:
        """Monitor all readers and return alerts"""
        alerts = []

        try:
            # Get reader health summary
            response = requests.get(f"{self.api_base}/readers/health/summary", timeout=5)
            if response.status_code != 200:
                return [{"level": "ERROR", "message": "Failed to fetch reader health"}]

            data = response.json()
            readers = data.get("readers", [])

            print("📡 READER STATUS")
            print("-" * 80)

            for reader in readers:
                reader_id = reader["reader_id"]
                name = reader["reader_name"]
                health = reader["overall_health"]
                score = reader["health_score"]
                issues = reader["issues"]

                # Get detailed health
                try:
                    detail_response = requests.get(
                        f"{self.api_base}/readers/{reader_id}/health",
                        timeout=5
                    )
                    if detail_response.status_code == 200:
                        detail = detail_response.json()

                        # Display reader info
                        print(f"{name:20} | {self.get_health_indicator(health):20} | Score: {score}/100")
                        print(f"  Comm: {detail['comm_uptime_percent']:.1f}% | "
                              f"Response: {detail['avg_response_time_ms']:.1f}ms | "
                              f"SC: {detail['sc_handshake_success_rate']:.1f}%")

                        # Check for alerts
                        if score < self.health_threshold:
                            alerts.append({
                                "level": "WARNING",
                                "message": f"Reader {reader_id} health below threshold ({score}/100)"
                            })

                        if detail['comm_uptime_percent'] < self.comm_uptime_threshold:
                            alerts.append({
                                "level": "WARNING",
                                "message": f"Reader {reader_id} comm uptime low ({detail['comm_uptime_percent']:.1f}%)"
                            })

                        if detail['avg_response_time_ms'] > self.response_time_threshold:
                            alerts.append({
                                "level": "WARNING",
                                "message": f"Reader {reader_id} slow response ({detail['avg_response_time_ms']:.1f}ms)"
                            })

                        if detail['sc_mac_failure_rate'] > 0:
                            alerts.append({
                                "level": "CRITICAL",
                                "message": f"Reader {reader_id} MAC failures detected! Possible security issue!"
                            })

                        if detail['tamper_status'] != "OK":
                            alerts.append({
                                "level": "CRITICAL",
                                "message": f"Reader {reader_id} TAMPER ALERT: {detail['tamper_status']}"
                            })

                        if issues > 0:
                            print(f"  ⚠️  {issues} issue(s) detected")

                        print()

                except Exception as e:
                    print(f"  Error getting details: {e}")
                    print()

        except Exception as e:
            alerts.append({"level": "ERROR", "message": f"Reader monitoring failed: {str(e)}"})

        return alerts

    def monitor_panels(self) -> List[Dict]:
        """Monitor all panels and return alerts"""
        alerts = []

        try:
            print("🖥️  PANEL STATUS")
            print("-" * 80)

            # Monitor panels 1-3 (adjust as needed)
            for panel_id in [1]:
                try:
                    # Get panel health
                    response = requests.get(
                        f"{self.api_base}/panels/{panel_id}/health",
                        timeout=5
                    )

                    if response.status_code == 200:
                        panel = response.json()

                        print(f"Panel {panel_id}: {panel['panel_name']}")
                        print(f"  Status: {'🟢 ONLINE' if panel['online'] else '🔴 OFFLINE'} | "
                              f"Uptime: {panel['uptime_hours']:.1f}h | "
                              f"Health: {self.get_health_indicator(panel['overall_health'])}")
                        print(f"  Power: {'AC OK' if panel['main_power'] else 'AC FAIL'} | "
                              f"Battery: {panel.get('battery_charge_percent', 0):.0f}% "
                              f"({panel.get('battery_voltage', 0):.1f}V)")
                        print(f"  I/O: {panel['inputs_ok']} inputs OK, "
                              f"{panel['outputs_ok']} outputs OK, "
                              f"{panel['relays_ok']} relays OK")

                        if panel['inputs_fault'] > 0 or panel['outputs_fault'] > 0:
                            print(f"  ⚠️  Faults: {panel['inputs_fault']} inputs, "
                                  f"{panel['outputs_fault']} outputs")
                            alerts.append({
                                "level": "WARNING",
                                "message": f"Panel {panel_id} has I/O faults"
                            })

                        if not panel['main_power']:
                            alerts.append({
                                "level": "CRITICAL",
                                "message": f"Panel {panel_id} AC POWER FAILURE - running on battery"
                            })

                        if panel.get('battery_charge_percent', 100) < 50:
                            alerts.append({
                                "level": "WARNING",
                                "message": f"Panel {panel_id} battery low ({panel['battery_charge_percent']:.0f}%)"
                            })

                        if panel['errors_last_24h'] > 0:
                            print(f"  ⚠️  {panel['errors_last_24h']} errors in last 24h")

                        print()

                except Exception as e:
                    print(f"Panel {panel_id}: Error - {e}")
                    print()

        except Exception as e:
            alerts.append({"level": "ERROR", "message": f"Panel monitoring failed: {str(e)}"})

        return alerts

    def monitor_io_status(self) -> List[Dict]:
        """Monitor I/O status"""
        alerts = []

        try:
            print("🔌 I/O STATUS")
            print("-" * 80)

            for panel_id in [1]:
                try:
                    response = requests.get(
                        f"{self.api_base}/panels/{panel_id}/io",
                        timeout=5
                    )

                    if response.status_code == 200:
                        io_status = response.json()

                        # Check inputs
                        active_inputs = [i for i in io_status['inputs'] if i['state'] == 'ACTIVE']
                        if active_inputs:
                            print(f"Active Inputs:")
                            for inp in active_inputs:
                                print(f"  • {inp['name']} ({inp['type']})")

                        # Check for faulted inputs
                        faulted = [i for i in io_status['inputs'] if i['state'] == 'FAULT']
                        if faulted:
                            for inp in faulted:
                                print(f"  ⚠️  FAULT: {inp['name']}")
                                alerts.append({
                                    "level": "WARNING",
                                    "message": f"Input fault: {inp['name']}"
                                })

                        # Check active outputs
                        active_outputs = [o for o in io_status['outputs'] if o['state'] == 'ACTIVE']
                        if active_outputs:
                            print(f"Active Outputs:")
                            for out in active_outputs:
                                print(f"  • {out['name']} ({out['type']})")

                        # Show event count
                        print(f"Total events today: {io_status['total_events_today']}")
                        print()

                except Exception as e:
                    print(f"Panel {panel_id} I/O: Error - {e}")
                    print()

        except Exception as e:
            alerts.append({"level": "ERROR", "message": f"I/O monitoring failed: {str(e)}"})

        return alerts

    def check_overrides(self) -> List[Dict]:
        """Check for active overrides"""
        alerts = []

        try:
            response = requests.get(f"{self.api_base}/overrides", timeout=5)

            if response.status_code == 200:
                overrides = response.json()

                if overrides:
                    print("⚙️  ACTIVE OVERRIDES")
                    print("-" * 80)

                    for override in overrides:
                        print(f"Override {override['override_id']}: {override['target_name']}")
                        print(f"  State: {override['override_state']} | "
                              f"Reason: {override['reason']}")
                        print(f"  Since: {override['override_since']} | "
                              f"By: {override['override_by']}")

                        if override.get('auto_release'):
                            print(f"  Auto-release: {override['auto_release']}")

                        print()

                        alerts.append({
                            "level": "INFO",
                            "message": f"Active override on {override['target_name']}"
                        })

        except Exception as e:
            alerts.append({"level": "ERROR", "message": f"Override check failed: {str(e)}"})

        return alerts

    def display_alerts(self, all_alerts: List[Dict]):
        """Display alerts"""
        if not all_alerts:
            return

        print("🚨 ALERTS")
        print("-" * 80)

        # Sort by level
        critical = [a for a in all_alerts if a["level"] == "CRITICAL"]
        warnings = [a for a in all_alerts if a["level"] == "WARNING"]
        errors = [a for a in all_alerts if a["level"] == "ERROR"]
        info = [a for a in all_alerts if a["level"] == "INFO"]

        for alert in critical:
            print(f"🔴 CRITICAL: {alert['message']}")

        for alert in errors:
            print(f"🔴 ERROR: {alert['message']}")

        for alert in warnings:
            print(f"🟡 WARNING: {alert['message']}")

        for alert in info:
            print(f"🔵 INFO: {alert['message']}")

        print()

    def run(self, refresh_interval: int = 5):
        """Run monitoring dashboard"""
        self.running = True

        print("Starting HAL Monitoring Dashboard...")
        print(f"Refresh interval: {refresh_interval} seconds")
        print("Press Ctrl+C to exit")
        print()
        time.sleep(2)

        try:
            while self.running:
                self.clear_screen()
                self.print_header()

                # Collect all alerts
                all_alerts = []

                # Monitor readers
                all_alerts.extend(self.monitor_readers())

                # Monitor panels
                all_alerts.extend(self.monitor_panels())

                # Monitor I/O
                all_alerts.extend(self.monitor_io_status())

                # Check overrides
                all_alerts.extend(self.check_overrides())

                # Display alerts
                self.display_alerts(all_alerts)

                print("=" * 80)
                print(f" Next refresh in {refresh_interval} seconds... (Ctrl+C to exit)".ljust(80))
                print("=" * 80)

                # Wait for next refresh
                time.sleep(refresh_interval)

        except KeyboardInterrupt:
            print("\n\nStopping monitoring dashboard...")
            self.running = False


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="HAL Monitoring Dashboard")
    parser.add_argument("--url", default="http://localhost:8080",
                        help="HAL API base URL (default: http://localhost:8080)")
    parser.add_argument("--interval", type=int, default=5,
                        help="Refresh interval in seconds (default: 5)")

    args = parser.parse_args()

    monitor = HALMonitor(base_url=args.url)
    monitor.run(refresh_interval=args.interval)


if __name__ == "__main__":
    main()
