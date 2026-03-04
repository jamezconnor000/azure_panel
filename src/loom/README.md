# Loom - Translation Layer
## AetherDB Binary to SQL Translation Engine

```
    ╭───────────────────────────────────────╮
    │            L O O M                    │
    │    "Weaving binary into SQL"          │
    ╰───────────────────────────────────────╯
```

---

## Overview

Loom is the translation layer between AetherDB's custom binary format and the SQL databases used by Aether Bifrost (SQLite/PostgreSQL) and Aether Saga (PostgreSQL).

---

## Architecture

```
                      LOOM TRANSLATION LAYER
┌────────────────────────────────────────────────────────────────────┐
│                                                                    │
│  ┌──────────────┐                            ┌──────────────┐     │
│  │   AetherDB   │                            │  PostgreSQL  │     │
│  │   (Binary)   │                            │   (Saga)     │     │
│  └──────┬───────┘                            └──────▲───────┘     │
│         │                                           │              │
│         ▼                                           │              │
│  ┌──────────────┐    ┌──────────────┐    ┌─────────┴────────┐    │
│  │  TLV Codec   │◄──►│   Schema     │───►│  PostgreSQL      │    │
│  │              │    │   Registry   │    │  Adapter         │    │
│  └──────────────┘    └──────┬───────┘    └──────────────────┘    │
│                             │                                     │
│                             ▼                                     │
│                      ┌──────────────┐    ┌──────────────────┐    │
│                      │ Translation  │───►│  SQLite Adapter  │    │
│                      │   Engine     │    └─────────┬────────┘    │
│                      └──────────────┘              │              │
│                                                    ▼              │
│                                            ┌──────────────┐      │
│                                            │    SQLite    │      │
│                                            │  (Bifrost)   │      │
│                                            └──────────────┘      │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

---

## Components

### 1. Schema Registry (`schema_registry.py`)

Defines all data structures with version support:

```python
CARDHOLDER_SCHEMA = TableDef(
    name="cardholders",
    version=1,
    primary_key="id",
    fields=[
        FieldDef(id=1, name="id", field_type=FieldType.UINT64, required=True),
        FieldDef(id=2, name="badge_number", field_type=FieldType.STRING, indexed=True),
        FieldDef(id=3, name="first_name", field_type=FieldType.STRING),
        FieldDef(id=4, name="last_name", field_type=FieldType.STRING),
        FieldDef(id=5, name="pin_code", field_type=FieldType.STRING),
        FieldDef(id=6, name="active", field_type=FieldType.BOOL, default=True),
        FieldDef(id=7, name="access_levels", field_type=FieldType.ARRAY, array_of=FieldType.UINT32),
        FieldDef(id=8, name="activation_date", field_type=FieldType.TIMESTAMP),
        FieldDef(id=9, name="expiration_date", field_type=FieldType.TIMESTAMP),
    ]
)
```

### 2. TLV Codec (`tlv_codec.py`)

Encodes/decodes Tag-Length-Value binary format:

```python
def encode_record(schema: TableDef, data: dict) -> bytes:
    """Encode a dictionary to TLV binary format."""

def decode_record(schema: TableDef, data: bytes) -> dict:
    """Decode TLV binary to dictionary."""
```

### 3. Translation Engine (`translator.py`)

Bidirectional conversion logic:

```python
class LoomTranslator:
    def binary_to_sql(self, table: str, record: bytes) -> dict
    def sql_to_binary(self, table: str, record: dict) -> bytes
    def sync_table(self, table: str, direction: Direction)
    def full_sync(self, direction: Direction)
```

### 4. Database Adapters

**PostgreSQL Adapter** (`adapters/postgresql.py`):
```python
class PostgreSQLAdapter:
    def insert(self, table: str, data: dict)
    def update(self, table: str, id: int, data: dict)
    def delete(self, table: str, id: int)
    def query(self, table: str, filters: dict)
```

**SQLite Adapter** (`adapters/sqlite.py`):
```python
class SQLiteAdapter:
    def insert(self, table: str, data: dict)
    def update(self, table: str, id: int, data: dict)
    def delete(self, table: str, id: int)
    def query(self, table: str, filters: dict)
```

---

## Error Handling

### Translation Error Types

| Error Type | Description |
|------------|-------------|
| `SCHEMA_MISMATCH` | Field type doesn't match schema |
| `MISSING_REQUIRED` | Required field missing |
| `ENCODING_ERROR` | Binary encoding failed |
| `DECODING_ERROR` | Binary decoding failed |
| `CONSTRAINT_VIOLATION` | SQL constraint violated |
| `CONNECTION_ERROR` | Database connection failed |
| `SYNC_CONFLICT` | Conflicting changes detected |

### Error Tracking

```python
@dataclass
class TranslationError:
    id: str
    timestamp: datetime
    severity: ErrorSeverity  # INFO, WARNING, ERROR, CRITICAL
    error_type: TranslationErrorType
    direction: Direction  # BINARY_TO_SQL, SQL_TO_BINARY
    table: str
    record_id: Optional[int]
    message: str
    source_data: Optional[dict]
    suggested_fix: Optional[str]
```

---

## Health Monitoring

### Health Receptor

Loom provides continuous health monitoring:

```python
class LoomHealth:
    def get_status(self) -> HealthStatus
    def get_sync_lag(self) -> timedelta
    def get_error_rate(self) -> float
    def get_pending_syncs(self) -> int
```

### Metrics

| Metric | Description |
|--------|-------------|
| `sync_lag_seconds` | Time since last successful sync |
| `error_rate` | Errors per 1000 translations |
| `pending_count` | Records waiting to be synced |
| `throughput` | Translations per second |

---

## Configuration

```yaml
loom:
  sync_interval: 5  # seconds
  batch_size: 100
  retry_attempts: 3
  retry_delay: 1  # seconds

  aetherdb:
    path: /data/aether.db

  postgresql:
    host: localhost
    port: 5432
    database: aether_saga

  sqlite:
    path: /data/bifrost_cache.db
```

---

## Usage

### Basic Sync

```python
from loom import LoomTranslator, Direction

translator = LoomTranslator()

# Sync AetherDB to PostgreSQL
translator.sync_table("cardholders", Direction.BINARY_TO_SQL)

# Full bidirectional sync
translator.full_sync()
```

### Error Handling

```python
from loom import LoomTranslator, TranslationError

translator = LoomTranslator()

try:
    translator.sync_table("cardholders", Direction.BINARY_TO_SQL)
except TranslationError as e:
    logger.error(f"Translation failed: {e.message}")
    logger.info(f"Suggested fix: {e.suggested_fix}")
```

---

## File Structure

```
src/loom/
├── __init__.py
├── README.md
├── schema_registry.py      # Data structure definitions
├── tlv_codec.py            # Binary encoding/decoding
├── translator.py           # Translation engine
├── health.py               # Health monitoring
├── errors.py               # Error definitions
├── adapters/
│   ├── __init__.py
│   ├── postgresql.py       # PostgreSQL adapter
│   └── sqlite.py           # SQLite adapter
└── tests/
    ├── test_codec.py
    ├── test_translator.py
    └── test_adapters.py
```

---

## Development

### Running Tests

```bash
cd src/loom
pytest tests/
```

### Building

Loom is included in all three Aether apps automatically.

---

*Loom - Weaving binary into SQL*
*Part of Aether Access 3.0*
