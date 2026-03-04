"""
Loom - Translation Layer for Aether Access 3.0
Converts between AetherDB binary format and SQL databases.
"""

from .schema_registry import (
    FieldType,
    FieldDef,
    TableDef,
    CARDHOLDER_SCHEMA,
    ACCESS_LEVEL_SCHEMA,
    DOOR_SCHEMA,
    EVENT_SCHEMA,
)
from .tlv_codec import TLVCodec
from .translator import LoomTranslator, Direction
from .errors import (
    TranslationError,
    TranslationErrorType,
    ErrorSeverity,
)
from .health import LoomHealth, HealthStatus

__version__ = "1.0.0"
__all__ = [
    # Schema
    "FieldType",
    "FieldDef",
    "TableDef",
    "CARDHOLDER_SCHEMA",
    "ACCESS_LEVEL_SCHEMA",
    "DOOR_SCHEMA",
    "EVENT_SCHEMA",
    # Codec
    "TLVCodec",
    # Translator
    "LoomTranslator",
    "Direction",
    # Errors
    "TranslationError",
    "TranslationErrorType",
    "ErrorSeverity",
    # Health
    "LoomHealth",
    "HealthStatus",
]
