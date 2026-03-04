"""
Loom Schema Registry
Defines all data structures for AetherDB with TLV encoding support.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, List, Optional


class FieldType(Enum):
    """Data types supported by AetherDB."""
    UINT8 = "uint8"
    UINT16 = "uint16"
    UINT32 = "uint32"
    UINT64 = "uint64"
    INT8 = "int8"
    INT16 = "int16"
    INT32 = "int32"
    INT64 = "int64"
    FLOAT32 = "float32"
    FLOAT64 = "float64"
    BOOL = "bool"
    STRING = "string"
    BYTES = "bytes"
    TIMESTAMP = "timestamp"
    ARRAY = "array"
    MAP = "map"


@dataclass
class FieldDef:
    """Definition of a field in a table schema."""
    id: int  # TLV tag ID (1-65535)
    name: str
    field_type: FieldType
    required: bool = False
    indexed: bool = False
    unique: bool = False
    default: Any = None
    array_of: Optional[FieldType] = None  # For ARRAY types
    max_length: Optional[int] = None  # For STRING/BYTES
    description: str = ""


@dataclass
class TableDef:
    """Definition of a table schema."""
    name: str
    version: int
    primary_key: str
    fields: List[FieldDef]
    description: str = ""

    def get_field(self, name: str) -> Optional[FieldDef]:
        """Get field definition by name."""
        for f in self.fields:
            if f.name == name:
                return f
        return None

    def get_field_by_id(self, tag_id: int) -> Optional[FieldDef]:
        """Get field definition by TLV tag ID."""
        for f in self.fields:
            if f.id == tag_id:
                return f
        return None

    def get_indexed_fields(self) -> List[FieldDef]:
        """Get all indexed fields."""
        return [f for f in self.fields if f.indexed]

    def get_required_fields(self) -> List[FieldDef]:
        """Get all required fields."""
        return [f for f in self.fields if f.required]


# =============================================================================
# SCHEMA DEFINITIONS
# =============================================================================

CARDHOLDER_SCHEMA = TableDef(
    name="cardholders",
    version=1,
    primary_key="id",
    description="Access control cardholders",
    fields=[
        FieldDef(id=1, name="id", field_type=FieldType.UINT64, required=True,
                 description="Unique cardholder ID"),
        FieldDef(id=2, name="badge_number", field_type=FieldType.STRING, required=True,
                 indexed=True, unique=True, max_length=32,
                 description="Badge/card number"),
        FieldDef(id=3, name="first_name", field_type=FieldType.STRING, max_length=64,
                 description="First name"),
        FieldDef(id=4, name="last_name", field_type=FieldType.STRING, max_length=64,
                 description="Last name"),
        FieldDef(id=5, name="pin_code", field_type=FieldType.STRING, max_length=16,
                 description="PIN code (encrypted)"),
        FieldDef(id=6, name="active", field_type=FieldType.BOOL, default=True,
                 description="Whether cardholder is active"),
        FieldDef(id=7, name="access_levels", field_type=FieldType.ARRAY,
                 array_of=FieldType.UINT32,
                 description="Assigned access level IDs"),
        FieldDef(id=8, name="activation_date", field_type=FieldType.TIMESTAMP,
                 description="When access becomes active"),
        FieldDef(id=9, name="expiration_date", field_type=FieldType.TIMESTAMP,
                 description="When access expires"),
        FieldDef(id=10, name="facility_code", field_type=FieldType.UINT16,
                 description="Facility code for Wiegand"),
        FieldDef(id=11, name="card_data", field_type=FieldType.BYTES, max_length=256,
                 description="Raw card data (DESFire, etc.)"),
        FieldDef(id=12, name="created_at", field_type=FieldType.TIMESTAMP,
                 description="Record creation timestamp"),
        FieldDef(id=13, name="updated_at", field_type=FieldType.TIMESTAMP,
                 description="Last update timestamp"),
        FieldDef(id=14, name="external_id", field_type=FieldType.STRING, max_length=64,
                 indexed=True, description="External system ID (Lenel, etc.)"),
    ]
)

ACCESS_LEVEL_SCHEMA = TableDef(
    name="access_levels",
    version=1,
    primary_key="id",
    description="Access level definitions",
    fields=[
        FieldDef(id=1, name="id", field_type=FieldType.UINT32, required=True,
                 description="Unique access level ID"),
        FieldDef(id=2, name="name", field_type=FieldType.STRING, required=True,
                 max_length=64, description="Access level name"),
        FieldDef(id=3, name="description", field_type=FieldType.STRING, max_length=256,
                 description="Access level description"),
        FieldDef(id=4, name="doors", field_type=FieldType.ARRAY, array_of=FieldType.UINT32,
                 description="Door IDs with access"),
        FieldDef(id=5, name="schedules", field_type=FieldType.ARRAY, array_of=FieldType.UINT32,
                 description="Schedule IDs when access is allowed"),
        FieldDef(id=6, name="active", field_type=FieldType.BOOL, default=True,
                 description="Whether access level is active"),
        FieldDef(id=7, name="priority", field_type=FieldType.UINT16, default=100,
                 description="Priority for conflict resolution"),
        FieldDef(id=8, name="external_id", field_type=FieldType.STRING, max_length=64,
                 indexed=True, description="External system ID"),
    ]
)

DOOR_SCHEMA = TableDef(
    name="doors",
    version=1,
    primary_key="id",
    description="Door/reader definitions",
    fields=[
        FieldDef(id=1, name="id", field_type=FieldType.UINT32, required=True,
                 description="Unique door ID"),
        FieldDef(id=2, name="name", field_type=FieldType.STRING, required=True,
                 max_length=64, description="Door name"),
        FieldDef(id=3, name="description", field_type=FieldType.STRING, max_length=256,
                 description="Door description"),
        FieldDef(id=4, name="reader_address", field_type=FieldType.UINT8, required=True,
                 description="OSDP address or reader number"),
        FieldDef(id=5, name="reader_type", field_type=FieldType.UINT8, default=0,
                 description="0=OSDP, 1=Wiegand, 2=DESFire"),
        FieldDef(id=6, name="unlock_time", field_type=FieldType.UINT16, default=5,
                 description="Unlock duration in seconds"),
        FieldDef(id=7, name="held_open_time", field_type=FieldType.UINT16, default=30,
                 description="Held open alarm delay in seconds"),
        FieldDef(id=8, name="forced_open_enabled", field_type=FieldType.BOOL, default=True,
                 description="Forced open detection enabled"),
        FieldDef(id=9, name="rex_enabled", field_type=FieldType.BOOL, default=True,
                 description="Request-to-exit enabled"),
        FieldDef(id=10, name="active", field_type=FieldType.BOOL, default=True,
                 description="Whether door is active"),
        FieldDef(id=11, name="state", field_type=FieldType.UINT8, default=0,
                 description="Current state: 0=normal, 1=locked, 2=unlocked, 3=alarm"),
        FieldDef(id=12, name="external_id", field_type=FieldType.STRING, max_length=64,
                 indexed=True, description="External system ID"),
    ]
)

EVENT_SCHEMA = TableDef(
    name="events",
    version=1,
    primary_key="id",
    description="Access control events",
    fields=[
        FieldDef(id=1, name="id", field_type=FieldType.UINT64, required=True,
                 description="Unique event ID"),
        FieldDef(id=2, name="timestamp", field_type=FieldType.TIMESTAMP, required=True,
                 indexed=True, description="Event timestamp"),
        FieldDef(id=3, name="event_type", field_type=FieldType.UINT16, required=True,
                 indexed=True, description="Event type code"),
        FieldDef(id=4, name="door_id", field_type=FieldType.UINT32, indexed=True,
                 description="Door ID where event occurred"),
        FieldDef(id=5, name="cardholder_id", field_type=FieldType.UINT64, indexed=True,
                 description="Cardholder ID if applicable"),
        FieldDef(id=6, name="badge_number", field_type=FieldType.STRING, max_length=32,
                 description="Badge number presented"),
        FieldDef(id=7, name="granted", field_type=FieldType.BOOL,
                 description="Whether access was granted"),
        FieldDef(id=8, name="reason_code", field_type=FieldType.UINT16,
                 description="Reason for grant/deny"),
        FieldDef(id=9, name="details", field_type=FieldType.STRING, max_length=256,
                 description="Additional event details"),
        FieldDef(id=10, name="exported", field_type=FieldType.BOOL, default=False,
                 indexed=True, description="Whether exported to central system"),
        FieldDef(id=11, name="exported_at", field_type=FieldType.TIMESTAMP,
                 description="When event was exported"),
    ]
)

SCHEDULE_SCHEMA = TableDef(
    name="schedules",
    version=1,
    primary_key="id",
    description="Time schedules for access control",
    fields=[
        FieldDef(id=1, name="id", field_type=FieldType.UINT32, required=True,
                 description="Unique schedule ID"),
        FieldDef(id=2, name="name", field_type=FieldType.STRING, required=True,
                 max_length=64, description="Schedule name"),
        FieldDef(id=3, name="description", field_type=FieldType.STRING, max_length=256,
                 description="Schedule description"),
        FieldDef(id=4, name="intervals", field_type=FieldType.BYTES,
                 description="Encoded time intervals"),
        FieldDef(id=5, name="holidays", field_type=FieldType.ARRAY, array_of=FieldType.UINT32,
                 description="Holiday IDs to exclude"),
        FieldDef(id=6, name="active", field_type=FieldType.BOOL, default=True,
                 description="Whether schedule is active"),
        FieldDef(id=7, name="external_id", field_type=FieldType.STRING, max_length=64,
                 indexed=True, description="External system ID"),
    ]
)

# Schema registry for lookup
SCHEMA_REGISTRY = {
    "cardholders": CARDHOLDER_SCHEMA,
    "access_levels": ACCESS_LEVEL_SCHEMA,
    "doors": DOOR_SCHEMA,
    "events": EVENT_SCHEMA,
    "schedules": SCHEDULE_SCHEMA,
}


def get_schema(table_name: str) -> Optional[TableDef]:
    """Get schema definition for a table."""
    return SCHEMA_REGISTRY.get(table_name)


def list_tables() -> List[str]:
    """Get list of all registered table names."""
    return list(SCHEMA_REGISTRY.keys())
