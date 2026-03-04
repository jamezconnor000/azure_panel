"""
Loom Health Monitoring
Real-time health tracking for the translation layer.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any
import threading
import time


class HealthStatus(Enum):
    """Overall health status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class ComponentStatus(Enum):
    """Individual component status."""
    OK = "ok"
    WARNING = "warning"
    ERROR = "error"
    OFFLINE = "offline"


@dataclass
class ComponentHealth:
    """Health status of a single component."""
    name: str
    status: ComponentStatus = ComponentStatus.OK
    message: str = ""
    last_check: datetime = field(default_factory=datetime.utcnow)
    metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HealthReport:
    """Complete health report."""
    status: HealthStatus
    timestamp: datetime
    components: Dict[str, ComponentHealth]
    metrics: Dict[str, Any]
    alerts: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "status": self.status.value,
            "timestamp": self.timestamp.isoformat(),
            "components": {
                name: {
                    "status": comp.status.value,
                    "message": comp.message,
                    "last_check": comp.last_check.isoformat(),
                    "metrics": comp.metrics,
                }
                for name, comp in self.components.items()
            },
            "metrics": self.metrics,
            "alerts": self.alerts,
        }


class LoomHealth:
    """
    Health monitoring for the Loom translation layer.

    Tracks:
    - Sync lag between AetherDB and SQL
    - Error rates
    - Pending sync counts
    - Translation throughput
    - Component connectivity
    """

    def __init__(self):
        self._components: Dict[str, ComponentHealth] = {}
        self._metrics: Dict[str, Any] = {
            "translations_total": 0,
            "translations_succeeded": 0,
            "translations_failed": 0,
            "sync_operations": 0,
            "last_sync": None,
        }
        self._alerts: List[str] = []
        self._lock = threading.Lock()
        self._start_time = datetime.utcnow()

        # Initialize components
        self._init_components()

    def _init_components(self):
        """Initialize monitored components."""
        self._components = {
            "aetherdb": ComponentHealth(name="AetherDB", status=ComponentStatus.OFFLINE),
            "postgresql": ComponentHealth(name="PostgreSQL", status=ComponentStatus.OFFLINE),
            "sqlite": ComponentHealth(name="SQLite", status=ComponentStatus.OFFLINE),
            "translator": ComponentHealth(name="Translator", status=ComponentStatus.OK),
        }

    def update_component(
        self,
        name: str,
        status: ComponentStatus,
        message: str = "",
        metrics: Optional[Dict[str, Any]] = None,
    ):
        """Update a component's health status."""
        with self._lock:
            if name not in self._components:
                self._components[name] = ComponentHealth(name=name)

            comp = self._components[name]
            comp.status = status
            comp.message = message
            comp.last_check = datetime.utcnow()
            if metrics:
                comp.metrics.update(metrics)

            # Generate alerts for errors
            if status == ComponentStatus.ERROR:
                alert = f"Component {name} is in error state: {message}"
                if alert not in self._alerts:
                    self._alerts.append(alert)
                    if len(self._alerts) > 100:
                        self._alerts = self._alerts[-100:]

    def record_translation(self, success: bool, table: str = "", duration_ms: float = 0):
        """Record a translation operation."""
        with self._lock:
            self._metrics["translations_total"] += 1
            if success:
                self._metrics["translations_succeeded"] += 1
            else:
                self._metrics["translations_failed"] += 1

    def record_sync(self, table: str, success: bool, records: int = 0):
        """Record a sync operation."""
        with self._lock:
            self._metrics["sync_operations"] += 1
            self._metrics["last_sync"] = datetime.utcnow().isoformat()

    def get_status(self) -> HealthStatus:
        """Get overall health status."""
        with self._lock:
            error_count = sum(
                1 for c in self._components.values()
                if c.status == ComponentStatus.ERROR
            )
            warning_count = sum(
                1 for c in self._components.values()
                if c.status == ComponentStatus.WARNING
            )
            offline_count = sum(
                1 for c in self._components.values()
                if c.status == ComponentStatus.OFFLINE
            )

            # Calculate error rate
            total = self._metrics.get("translations_total", 0)
            failed = self._metrics.get("translations_failed", 0)
            error_rate = (failed / total * 100) if total > 0 else 0

            if error_count > 0 or error_rate > 10:
                return HealthStatus.UNHEALTHY
            elif warning_count > 0 or offline_count > 1 or error_rate > 1:
                return HealthStatus.DEGRADED
            elif self._components:
                return HealthStatus.HEALTHY
            else:
                return HealthStatus.UNKNOWN

    def get_sync_lag(self, table: str = "") -> Optional[timedelta]:
        """Get time since last sync."""
        last_sync = self._metrics.get("last_sync")
        if last_sync:
            last = datetime.fromisoformat(last_sync)
            return datetime.utcnow() - last
        return None

    def get_error_rate(self, window_minutes: int = 60) -> float:
        """Get error rate as percentage."""
        with self._lock:
            total = self._metrics.get("translations_total", 0)
            failed = self._metrics.get("translations_failed", 0)
            if total == 0:
                return 0.0
            return (failed / total) * 100

    def get_pending_syncs(self) -> int:
        """Get count of pending sync operations."""
        # TODO: Implement actual pending count tracking
        return 0

    def get_throughput(self) -> float:
        """Get translations per second."""
        with self._lock:
            total = self._metrics.get("translations_total", 0)
            uptime = (datetime.utcnow() - self._start_time).total_seconds()
            if uptime == 0:
                return 0.0
            return total / uptime

    def get_report(self) -> HealthReport:
        """Generate complete health report."""
        with self._lock:
            return HealthReport(
                status=self.get_status(),
                timestamp=datetime.utcnow(),
                components=dict(self._components),
                metrics={
                    **self._metrics,
                    "error_rate_percent": self.get_error_rate(),
                    "throughput_per_second": self.get_throughput(),
                    "uptime_seconds": (datetime.utcnow() - self._start_time).total_seconds(),
                },
                alerts=list(self._alerts),
            )

    def clear_alerts(self):
        """Clear all alerts."""
        with self._lock:
            self._alerts = []

    def to_dict(self) -> Dict[str, Any]:
        """Get health status as dictionary."""
        return self.get_report().to_dict()


# Singleton instance
_health_instance: Optional[LoomHealth] = None


def get_health() -> LoomHealth:
    """Get the global health monitor instance."""
    global _health_instance
    if _health_instance is None:
        _health_instance = LoomHealth()
    return _health_instance
