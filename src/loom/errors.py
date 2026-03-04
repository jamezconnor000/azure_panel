"""
Loom Error Definitions
Translation error types and tracking for Aether Access 3.0.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
import uuid


class ErrorSeverity(Enum):
    """Severity levels for translation errors."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class TranslationErrorType(Enum):
    """Types of translation errors."""
    SCHEMA_MISMATCH = "schema_mismatch"
    MISSING_REQUIRED = "missing_required"
    ENCODING_ERROR = "encoding_error"
    DECODING_ERROR = "decoding_error"
    CONSTRAINT_VIOLATION = "constraint_violation"
    CONNECTION_ERROR = "connection_error"
    SYNC_CONFLICT = "sync_conflict"
    UNKNOWN = "unknown"


class Direction(Enum):
    """Translation direction."""
    BINARY_TO_SQL = "binary_to_sql"
    SQL_TO_BINARY = "sql_to_binary"


@dataclass
class TranslationError(Exception):
    """
    Detailed translation error with context and suggested fixes.

    Attributes:
        id: Unique error identifier
        timestamp: When the error occurred
        severity: Error severity level
        error_type: Classification of the error
        direction: Which direction the translation was going
        operation: The operation being performed
        table: The table being translated
        record_id: The record ID if applicable
        message: Human-readable error message
        field_name: The field that caused the error if applicable
        source_data: The data that failed translation
        root_cause: Underlying exception or cause
        suggested_fix: Suggested remediation action
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    timestamp: datetime = field(default_factory=datetime.utcnow)
    severity: ErrorSeverity = ErrorSeverity.ERROR
    error_type: TranslationErrorType = TranslationErrorType.UNKNOWN
    direction: Direction = Direction.BINARY_TO_SQL
    operation: str = ""
    table: str = ""
    record_id: Optional[int] = None
    message: str = ""
    field_name: Optional[str] = None
    source_data: Optional[Dict[str, Any]] = None
    root_cause: Optional[str] = None
    suggested_fix: Optional[str] = None

    def __str__(self) -> str:
        return f"[{self.severity.value.upper()}] {self.error_type.value}: {self.message}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for logging/display."""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "severity": self.severity.value,
            "error_type": self.error_type.value,
            "direction": self.direction.value,
            "operation": self.operation,
            "table": self.table,
            "record_id": self.record_id,
            "message": self.message,
            "field_name": self.field_name,
            "source_data": self.source_data,
            "root_cause": self.root_cause,
            "suggested_fix": self.suggested_fix,
        }


@dataclass
class TranslationErrorLog:
    """Collection of translation errors with management."""
    errors: list = field(default_factory=list)
    max_errors: int = 1000

    def add(self, error: TranslationError):
        """Add an error to the log."""
        self.errors.append(error)
        if len(self.errors) > self.max_errors:
            self.errors = self.errors[-self.max_errors:]

    def get_recent(self, count: int = 50) -> list:
        """Get most recent errors."""
        return self.errors[-count:]

    def get_by_severity(self, severity: ErrorSeverity) -> list:
        """Get errors of a specific severity."""
        return [e for e in self.errors if e.severity == severity]

    def get_by_table(self, table: str) -> list:
        """Get errors for a specific table."""
        return [e for e in self.errors if e.table == table]

    def get_critical(self) -> list:
        """Get critical errors requiring immediate attention."""
        return self.get_by_severity(ErrorSeverity.CRITICAL)

    def clear(self):
        """Clear all errors."""
        self.errors = []

    def error_rate(self, window_seconds: int = 3600) -> float:
        """Calculate error rate over a time window."""
        cutoff = datetime.utcnow().timestamp() - window_seconds
        recent = [e for e in self.errors if e.timestamp.timestamp() > cutoff]
        return len(recent) / (window_seconds / 60)  # errors per minute
