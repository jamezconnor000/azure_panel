#!/usr/bin/env python3
"""
HAL Feedback Loop Tool

Collects logs, errors, and telemetry from Azure Panel deployment
and generates a comprehensive report for debugging with Claude.

Usage:
    # Collect all logs
    ./hal_feedback_loop.py --collect

    # Collect logs since last hour
    ./hal_feedback_loop.py --collect --since 1h

    # Generate feedback report
    ./hal_feedback_loop.py --report output.txt

    # Auto-analyze and suggest fixes
    ./hal_feedback_loop.py --analyze
"""

import json
import os
import sys
import argparse
import subprocess
import datetime
import re
from pathlib import Path
from typing import List, Dict, Any

class HALFeedbackCollector:
    def __init__(self, hal_root="/opt/hal"):
        self.hal_root = Path(hal_root)
        self.logs_dir = self.hal_root / "logs"
        self.db_path = self.hal_root / "hal_sdk.db"
        self.config_path = self.hal_root / "config" / "hal_config.json"

    def collect_system_info(self) -> Dict[str, Any]:
        """Collect system information"""
        info = {
            "timestamp": datetime.datetime.now().isoformat(),
            "hostname": subprocess.getoutput("hostname"),
            "os": subprocess.getoutput("uname -a"),
            "uptime": subprocess.getoutput("uptime"),
            "disk_usage": subprocess.getoutput("df -h /opt/hal"),
            "memory": subprocess.getoutput("free -h"),
            "cpu": subprocess.getoutput("top -bn1 | head -5"),
        }
        return info

    def collect_hal_logs(self, since_minutes=None) -> List[str]:
        """Collect HAL diagnostic logs"""
        log_files = [
            self.logs_dir / "hal_diagnostic.log",
            self.logs_dir / "api_server.log",
            self.logs_dir / "event_export.log"
        ]

        logs = []
        for log_file in log_files:
            if log_file.exists():
                with open(log_file, 'r') as f:
                    content = f.readlines()

                    if since_minutes:
                        cutoff = datetime.datetime.now() - datetime.timedelta(minutes=since_minutes)
                        content = self._filter_by_time(content, cutoff)

                    logs.extend(content)

        return logs

    def collect_error_logs(self) -> List[Dict[str, Any]]:
        """Extract error messages from logs"""
        logs = self.collect_hal_logs()
        errors = []

        for line in logs:
            if "ERROR" in line or "FATAL" in line or "WARN" in line:
                error_entry = self._parse_log_line(line)
                if error_entry:
                    errors.append(error_entry)

        return errors

    def _parse_log_line(self, line: str) -> Dict[str, Any]:
        """Parse a log line into structured data"""
        # Pattern: [timestamp] [LEVEL] [CATEGORY] [file:line:function] message
        pattern = r'\[(.*?)\] \[(.*?)\] \[(.*?)\] \[(.*?):(.*?):(.*?)\] (.*)'
        match = re.match(pattern, line)

        if match:
            return {
                "timestamp": match.group(1),
                "level": match.group(2),
                "category": match.group(3),
                "file": match.group(4),
                "line": match.group(5),
                "function": match.group(6),
                "message": match.group(7).strip()
            }
        return None

    def collect_reader_status(self) -> List[Dict[str, Any]]:
        """Collect reader connection status"""
        # Check if readers are responding
        readers = []

        # Try to read from diagnostic JSON export
        json_path = self.logs_dir / "diagnostic_export.json"
        if json_path.exists():
            with open(json_path, 'r') as f:
                data = json.load(f)
                # Extract reader-related entries
                for entry in data.get("log_entries", []):
                    if entry.get("category") == "READER" or entry.get("category") == "OSDP":
                        readers.append(entry)

        return readers

    def collect_performance_metrics(self) -> Dict[str, Any]:
        """Collect performance metrics"""
        metrics = {
            "api_response_times": [],
            "database_query_times": [],
            "osdp_poll_times": [],
            "event_export_times": []
        }

        logs = self.collect_hal_logs()
        for line in logs:
            if "PERFORMANCE" in line and "took" in line:
                # Parse performance log: "Operation 'xxx' took NNN ms"
                match = re.search(r"Operation '(.+?)' took (\d+) ms", line)
                if match:
                    operation = match.group(1)
                    duration_ms = int(match.group(2))

                    if "API" in operation:
                        metrics["api_response_times"].append(duration_ms)
                    elif "Database" in operation or "Query" in operation:
                        metrics["database_query_times"].append(duration_ms)
                    elif "OSDP" in operation or "Poll" in operation:
                        metrics["osdp_poll_times"].append(duration_ms)
                    elif "Export" in operation:
                        metrics["event_export_times"].append(duration_ms)

        # Calculate statistics
        for key in metrics:
            if metrics[key]:
                metrics[key] = {
                    "count": len(metrics[key]),
                    "min": min(metrics[key]),
                    "max": max(metrics[key]),
                    "avg": sum(metrics[key]) / len(metrics[key])
                }
            else:
                metrics[key] = {"count": 0}

        return metrics

    def collect_database_info(self) -> Dict[str, Any]:
        """Collect database information"""
        if not self.db_path.exists():
            return {"error": "Database file not found"}

        try:
            import sqlite3
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            info = {}

            # Count tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            info["tables"] = tables

            # Count records in each table
            info["record_counts"] = {}
            for table in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    info["record_counts"][table] = count
                except:
                    info["record_counts"][table] = "ERROR"

            conn.close()
            return info

        except Exception as e:
            return {"error": str(e)}

    def collect_config(self) -> Dict[str, Any]:
        """Collect HAL configuration"""
        if not self.config_path.exists():
            return {"error": "Config file not found"}

        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            return {"error": str(e)}

    def check_services_running(self) -> Dict[str, bool]:
        """Check if HAL services are running"""
        services = {
            "api_server": False,
            "event_export": False
        }

        # Check for PID files
        api_pid = self.hal_root / ".hal_api.pid"
        export_pid = self.hal_root / ".hal_export.pid"

        if api_pid.exists():
            with open(api_pid, 'r') as f:
                pid = f.read().strip()
                # Check if process exists
                try:
                    os.kill(int(pid), 0)
                    services["api_server"] = True
                except:
                    pass

        if export_pid.exists():
            with open(export_pid, 'r') as f:
                pid = f.read().strip()
                try:
                    os.kill(int(pid), 0)
                    services["event_export"] = True
                except:
                    pass

        return services

    def collect_secure_channel_status(self) -> Dict[str, Any]:
        """Collect OSDP Secure Channel diagnostic information"""
        sc_status = {
            "enabled": False,
            "handshakes_completed": 0,
            "handshakes_failed": 0,
            "packets_encrypted": 0,
            "packets_decrypted": 0,
            "mac_failures": 0,
            "cryptogram_failures": 0,
            "errors": []
        }

        logs = self.collect_hal_logs()

        for line in logs:
            # Look for secure channel specific log entries
            if "SECURE CHANNEL" in line.upper() or "OSDP" in line.upper():
                # Handshake events
                if "HANDSHAKE START" in line.upper():
                    sc_status["enabled"] = True
                elif "ESTABLISHED" in line.upper() and "SECURE CHANNEL" in line.upper():
                    sc_status["handshakes_completed"] += 1
                elif "HANDSHAKE" in line.upper() and ("FAILED" in line.upper() or "ERROR" in line.upper()):
                    sc_status["handshakes_failed"] += 1

                # Encryption/Decryption events
                elif "ENCRYPTING PACKET" in line.upper():
                    sc_status["packets_encrypted"] += 1
                elif "DECRYPTING PACKET" in line.upper():
                    sc_status["packets_decrypted"] += 1

                # Security failures
                elif "MAC VERIFICATION FAILED" in line.upper() or "MAC" in line.upper() and "INVALID" in line.upper():
                    sc_status["mac_failures"] += 1
                    sc_status["errors"].append({
                        "type": "MAC_FAILURE",
                        "message": line.strip(),
                        "severity": "CRITICAL"
                    })
                elif "CRYPTOGRAM" in line.upper() and "FAILED" in line.upper():
                    sc_status["cryptogram_failures"] += 1
                    sc_status["errors"].append({
                        "type": "CRYPTOGRAM_FAILURE",
                        "message": line.strip(),
                        "severity": "CRITICAL"
                    })

        # Add health indicators
        if sc_status["handshakes_failed"] > 0:
            failure_rate = sc_status["handshakes_failed"] / max(1, sc_status["handshakes_completed"] + sc_status["handshakes_failed"])
            sc_status["handshake_failure_rate"] = f"{failure_rate * 100:.1f}%"

        if sc_status["mac_failures"] > 0:
            mac_failure_rate = sc_status["mac_failures"] / max(1, sc_status["packets_decrypted"])
            sc_status["mac_failure_rate"] = f"{mac_failure_rate * 100:.1f}%"

        return sc_status

    def analyze_errors(self, errors: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze errors and categorize them"""
        analysis = {
            "total_errors": len(errors),
            "by_category": {},
            "by_severity": {"ERROR": 0, "WARN": 0, "FATAL": 0},
            "common_issues": [],
            "recommendations": []
        }

        for error in errors:
            # Count by category
            cat = error.get("category", "UNKNOWN")
            analysis["by_category"][cat] = analysis["by_category"].get(cat, 0) + 1

            # Count by severity
            level = error.get("level", "UNKNOWN")
            if level in analysis["by_severity"]:
                analysis["by_severity"][level] += 1

        # Detect common issues
        messages = [e.get("message", "") for e in errors]

        # Database connection issues
        db_errors = [m for m in messages if "database" in m.lower() or "sqlite" in m.lower()]
        if len(db_errors) > 5:
            analysis["common_issues"].append({
                "type": "Database Connection",
                "count": len(db_errors),
                "severity": "HIGH"
            })
            analysis["recommendations"].append(
                "Check database file permissions and integrity. "
                "Verify hal_sdk.db and hal_cards.db exist and are readable."
            )

        # OSDP communication issues
        osdp_errors = [m for m in messages if "osdp" in m.lower() or "reader" in m.lower()]
        if len(osdp_errors) > 5:
            analysis["common_issues"].append({
                "type": "OSDP Reader Communication",
                "count": len(osdp_errors),
                "severity": "HIGH"
            })
            analysis["recommendations"].append(
                "Check OSDP reader connections. Verify serial port exists (/dev/ttyUSB0), "
                "check baud rate, and verify reader is powered on."
            )

        # OSDP Secure Channel issues
        sc_errors = [m for m in messages if "secure channel" in m.lower() or "cryptogram" in m.lower()
                     or "scbk" in m.lower() or "mac verification" in m.lower()]
        if len(sc_errors) > 0:
            analysis["common_issues"].append({
                "type": "OSDP Secure Channel",
                "count": len(sc_errors),
                "severity": "CRITICAL"
            })

            # Analyze specific secure channel errors
            if any("cryptogram" in m.lower() and "failed" in m.lower() for m in messages):
                analysis["recommendations"].append(
                    "SECURITY: Cryptogram verification failed! This indicates:\n"
                    "  1. SCBK mismatch between CP and PD - verify both have same 128-bit key\n"
                    "  2. Packet corruption during transmission - check cable integrity\n"
                    "  3. Possible man-in-the-middle attack attempt - investigate immediately"
                )

            if any("mac" in m.lower() and ("failed" in m.lower() or "invalid" in m.lower()) for m in messages):
                analysis["recommendations"].append(
                    "SECURITY: MAC verification failed! This indicates:\n"
                    "  1. Packet tampering or corruption detected\n"
                    "  2. Wrong MAC key in use (S-MAC1/S-MAC2 mismatch)\n"
                    "  3. Session key derivation error - check SCBK provisioning"
                )

            if any("not enabled" in m.lower() for m in messages):
                analysis["recommendations"].append(
                    "Secure Channel not enabled. Set secure_channel=true in OSDP_Config_t and "
                    "provision SCBK before attempting encrypted communication."
                )

            if any("invalid state" in m.lower() for m in messages):
                analysis["recommendations"].append(
                    "Secure Channel state error. Follow handshake sequence:\n"
                    "  INIT → CHALLENGE_SENT → CHALLENGE_RECV → ESTABLISHED\n"
                    "  Reset secure channel and reinitiate handshake."
                )

        # API issues
        api_errors = [m for m in messages if "api" in m.lower() or "network" in m.lower()]
        if len(api_errors) > 5:
            analysis["common_issues"].append({
                "type": "API/Network",
                "count": len(api_errors),
                "severity": "MEDIUM"
            })
            analysis["recommendations"].append(
                "Check if port 8080 is accessible. Verify firewall rules and "
                "check if another process is using the port."
            )

        return analysis

    def generate_feedback_report(self, output_path: str):
        """Generate comprehensive feedback report"""
        print("Collecting HAL system information...")

        report = []
        report.append("=" * 80)
        report.append("HAL AZURE PANEL DEPLOYMENT - FEEDBACK REPORT")
        report.append("=" * 80)
        report.append("")

        # System Info
        report.append("SYSTEM INFORMATION")
        report.append("-" * 80)
        sys_info = self.collect_system_info()
        for key, value in sys_info.items():
            report.append(f"{key}: {value}")
        report.append("")

        # Service Status
        report.append("SERVICE STATUS")
        report.append("-" * 80)
        services = self.check_services_running()
        for service, running in services.items():
            status = "RUNNING" if running else "STOPPED"
            report.append(f"{service}: {status}")
        report.append("")

        # Configuration
        report.append("CONFIGURATION")
        report.append("-" * 80)
        config = self.collect_config()
        report.append(json.dumps(config, indent=2))
        report.append("")

        # Database Info
        report.append("DATABASE INFORMATION")
        report.append("-" * 80)
        db_info = self.collect_database_info()
        report.append(json.dumps(db_info, indent=2))
        report.append("")

        # Error Analysis
        report.append("ERROR ANALYSIS")
        report.append("-" * 80)
        errors = self.collect_error_logs()
        analysis = self.analyze_errors(errors)
        report.append(json.dumps(analysis, indent=2))
        report.append("")

        # Performance Metrics
        report.append("PERFORMANCE METRICS")
        report.append("-" * 80)
        metrics = self.collect_performance_metrics()
        report.append(json.dumps(metrics, indent=2))
        report.append("")

        # Secure Channel Status
        report.append("OSDP SECURE CHANNEL STATUS")
        report.append("-" * 80)
        sc_status = self.collect_secure_channel_status()
        report.append(json.dumps(sc_status, indent=2))
        report.append("")
        if sc_status["errors"]:
            report.append("SECURE CHANNEL ERRORS:")
            for error in sc_status["errors"]:
                report.append(f"  [{error['severity']}] {error['type']}: {error['message']}")
            report.append("")

        # Recent Errors (last 50)
        report.append("RECENT ERRORS (LAST 50)")
        report.append("-" * 80)
        for error in errors[-50:]:
            report.append(json.dumps(error))
        report.append("")

        # Reader Status
        report.append("READER STATUS")
        report.append("-" * 80)
        readers = self.collect_reader_status()
        for reader in readers[-20:]:
            report.append(json.dumps(reader))
        report.append("")

        # Recommendations
        report.append("RECOMMENDATIONS FOR CLAUDE")
        report.append("-" * 80)
        for rec in analysis.get("recommendations", []):
            report.append(f"• {rec}")
        report.append("")

        report.append("=" * 80)
        report.append("END OF REPORT")
        report.append("=" * 80)

        # Write to file
        with open(output_path, 'w') as f:
            f.write("\n".join(report))

        print(f"Feedback report written to: {output_path}")
        print(f"Total errors found: {len(errors)}")
        print(f"Common issues: {len(analysis['common_issues'])}")
        print("\nYou can now share this file with Claude for analysis and fixes.")


def main():
    parser = argparse.ArgumentParser(description="HAL Feedback Loop Tool")
    parser.add_argument("--collect", action="store_true", help="Collect logs and telemetry")
    parser.add_argument("--report", type=str, help="Generate feedback report to file")
    parser.add_argument("--analyze", action="store_true", help="Analyze and suggest fixes")
    parser.add_argument("--since", type=str, help="Collect logs since (e.g., 1h, 30m)")
    parser.add_argument("--hal-root", type=str, default="/opt/hal", help="HAL installation path")

    args = parser.parse_args()

    collector = HALFeedbackCollector(hal_root=args.hal_root)

    if args.report:
        collector.generate_feedback_report(args.report)
    elif args.analyze:
        errors = collector.collect_error_logs()
        analysis = collector.analyze_errors(errors)
        print(json.dumps(analysis, indent=2))
    elif args.collect:
        # Export JSON for Claude analysis
        logs = collector.collect_hal_logs()
        output = {
            "system_info": collector.collect_system_info(),
            "services": collector.check_services_running(),
            "errors": collector.collect_error_logs(),
            "metrics": collector.collect_performance_metrics(),
            "database": collector.collect_database_info(),
            "config": collector.collect_config()
        }
        print(json.dumps(output, indent=2))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
