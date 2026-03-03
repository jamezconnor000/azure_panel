# Ambient.ai Integration - Cloud Event Forwarding

**Version:** 1.0.0
**Language:** C + Python
**Status:** Proof of Concept / Development

---

## Overview

The Ambient.ai Integration module provides real-time event forwarding from the Azure Panel access control system to Ambient.ai's Generic Cloud API. This enables cloud-based video analytics and access control correlation.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    AZURE PANEL SYSTEM                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────┐         ┌─────────────────────────┐   │
│  │    Badge Reader     │         │      HAL Core           │   │
│  │    (Wiegand/OSDP)   │────────►│  (Access Logic Engine)  │   │
│  └─────────────────────┘         └───────────┬─────────────┘   │
│                                              │                  │
│                                              │ Events           │
│                                              ▼                  │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │                    IPC EVENT BUS                          │ │
│  │               (Unix Domain Socket)                        │ │
│  │                /tmp/hal_events.sock                       │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                              │                  │
│                                              │ Subscribe        │
│                                              ▼                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              AMBIENT FORWARDER DAEMON                    │   │
│  │                                                          │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │   │
│  │  │    Event     │  │    JSON      │  │    HTTP      │   │   │
│  │  │  Transform   │──►│  Serialize   │──►│    POST     │   │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘   │   │
│  │                                              │          │   │
│  │  ┌──────────────┐                           │          │   │
│  │  │  Retry Queue │◄──────────(on failure)────┘          │   │
│  │  │  (SQLite)    │                                       │   │
│  │  └──────────────┘                                       │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                              │                  │
└──────────────────────────────────────────────┼──────────────────┘
                                               │ HTTPS
                                               ▼
                          ┌─────────────────────────────────────┐
                          │         AMBIENT.AI CLOUD            │
                          │                                     │
                          │  POST https://api.ambient.ai/v1/    │
                          │       generic-cloud/events          │
                          │                                     │
                          │  - Access event correlation         │
                          │  - Video analytics                  │
                          │  - Anomaly detection                │
                          └─────────────────────────────────────┘
```

---

## Components

### App 1: HAL Access Engine
**Location:** `poc/app1_hal_engine/`
**Purpose:** Core access control daemon

```
app1_hal_engine/
├── hal_engine.c/h        # Main daemon
├── wiegand_handler.c/h   # Wiegand protocol parsing
├── card_database.c/h     # SQLite card lookup
├── access_logic.c/h      # Access decisions
├── event_producer.c/h    # Event generation
├── ipc_publisher.c/h     # Unix socket publishing
└── main.c                # Entry point
```

**Features:**
- Wiegand protocol decoding
- Card database lookup
- Access grant/deny decisions
- Event generation and publishing
- IPC event bus publisher

### App 2: Ambient Forwarder
**Location:** `poc/app2_ambient_forwarder/`
**Purpose:** Event forwarding daemon

```
app2_ambient_forwarder/
├── forwarder.c/h         # Main daemon
├── ipc_subscriber.c/h    # Unix socket subscriber
├── ambient_client.c/h    # HTTP POST client
├── retry_queue.c/h       # Failed event queue
├── uuid_registry.c/h     # UUID deduplication
├── config.c/h            # Configuration
└── main.c                # Entry point
```

**Features:**
- IPC event bus subscriber
- Event transformation to Ambient format
- HTTP POST to Ambient.ai API
- Retry queue for failed deliveries
- UUID tracking for deduplication

### Shared Components
**Location:** `poc/shared/`

```
shared/
├── event_types.h         # Event structure definitions
├── json_serializer.c/h   # JSON encoding/decoding
└── uuid_utils.c/h        # UUID generation
```

### Developer Tools
**Location:** `poc/tools/`

```
tools/
├── simulate_badge.c      # Badge read simulator
├── monitor_events.c      # Event stream monitor
├── test_ambient.c        # Ambient API connectivity test
├── hal_logs.c            # Log viewer
└── hal_status.c          # System status dashboard
```

---

## Event Format

### Internal Event Structure
```c
typedef struct {
    char event_id[64];        // UUID
    uint32_t timestamp;       // Unix timestamp
    EventType_t type;         // Event type enum
    uint32_t card_number;     // Card number
    uint8_t door_id;          // Door/reader ID
    char door_name[64];       // Door name
    bool granted;             // Access decision
    char reason[128];         // Decision reason
} AccessEvent_t;
```

### Ambient.ai Event Format
```json
{
  "event_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2026-03-03T10:30:00.000Z",
  "event_type": "access_granted",
  "source": "azure_panel",
  "site_id": "site_001",
  "data": {
    "card_number": "12345678",
    "card_holder": "John Doe",
    "door_id": 1,
    "door_name": "Front Door",
    "granted": true,
    "decision_reason": "Valid card, within schedule"
  },
  "metadata": {
    "panel_id": "azure_001",
    "firmware_version": "2.0.0",
    "reader_type": "osdp"
  }
}
```

---

## Configuration

### ambient_config.json
```json
{
  "ambient_api": {
    "endpoint": "https://api.ambient.ai/v1/generic-cloud/events",
    "api_key": "${AMBIENT_API_KEY}",
    "site_id": "site_001",
    "timeout_ms": 5000,
    "retry_count": 3,
    "retry_delay_ms": 1000
  },
  "ipc": {
    "socket_path": "/tmp/hal_events.sock",
    "buffer_size": 65536
  },
  "retry_queue": {
    "database_path": "/var/lib/hal/retry_queue.db",
    "max_age_hours": 24,
    "batch_size": 100
  },
  "logging": {
    "level": "info",
    "file": "/var/log/hal/ambient_forwarder.log"
  }
}
```

---

## Build Instructions

### Build All
```bash
cd Source/poc
make all
```

### Build Individual Components
```bash
make hal_engine         # Build HAL engine
make ambient_forwarder  # Build forwarder
make tools              # Build dev tools
```

### Clean
```bash
make clean
```

### Run
```bash
# Start HAL engine (background)
./app1_hal_engine/hal_engine -c /etc/hal/hal_config.json &

# Start Ambient forwarder (background)
./app2_ambient_forwarder/forwarder -c /etc/hal/ambient_config.json &

# Monitor events (foreground)
./tools/monitor_events
```

---

## IPC Protocol

### Socket Path
```
/tmp/hal_events.sock (Unix domain socket, SOCK_STREAM)
```

### Message Format
```
[4 bytes: message length][JSON payload]
```

### Publisher (HAL Engine)
```c
int sock = socket(AF_UNIX, SOCK_STREAM, 0);
connect(sock, &addr, sizeof(addr));

char* json = serialize_event(event);
uint32_t len = strlen(json);

send(sock, &len, sizeof(len), 0);
send(sock, json, len, 0);
```

### Subscriber (Forwarder)
```c
int sock = socket(AF_UNIX, SOCK_STREAM, 0);
bind(sock, &addr, sizeof(addr));
listen(sock, 5);

int client = accept(sock, NULL, NULL);

uint32_t len;
recv(client, &len, sizeof(len), 0);

char* json = malloc(len + 1);
recv(client, json, len, 0);
json[len] = '\0';

AccessEvent_t* event = deserialize_event(json);
```

---

## Ambient.ai API Integration

### Authentication
```bash
# API Key in header
Authorization: Bearer ${AMBIENT_API_KEY}
```

### POST Events
```bash
curl -X POST "https://api.ambient.ai/v1/generic-cloud/events" \
  -H "Authorization: Bearer ${AMBIENT_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": "...",
    "timestamp": "2026-03-03T10:30:00Z",
    "event_type": "access_granted",
    "source": "azure_panel",
    "site_id": "site_001",
    "data": {...}
  }'
```

### Response
```json
{
  "status": "accepted",
  "event_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Error Handling
| Status | Action |
|--------|--------|
| 200/202 | Success, remove from queue |
| 400 | Invalid event, log and discard |
| 401/403 | Auth error, check API key |
| 429 | Rate limited, retry with backoff |
| 500/503 | Server error, add to retry queue |

---

## Retry Queue

### Schema
```sql
CREATE TABLE retry_queue (
    id INTEGER PRIMARY KEY,
    event_id TEXT UNIQUE,
    event_json TEXT,
    created_at INTEGER,
    retry_count INTEGER DEFAULT 0,
    last_error TEXT,
    next_retry_at INTEGER
);
```

### Retry Logic
```c
// Exponential backoff
int delay_ms = 1000 * pow(2, retry_count);  // 1s, 2s, 4s, 8s...
int max_delay_ms = 60000;  // Cap at 1 minute

if (delay_ms > max_delay_ms) {
    delay_ms = max_delay_ms;
}
```

### Queue Processing
```c
// Process retry queue every 10 seconds
while (running) {
    Event_t* events = get_pending_retries(100);  // Batch of 100

    for (int i = 0; i < count; i++) {
        if (send_to_ambient(events[i]) == SUCCESS) {
            remove_from_queue(events[i].id);
        } else {
            increment_retry_count(events[i].id);
        }
    }

    sleep(10);
}
```

---

## Python Alternative

### Python Forwarder
```python
# integration/ambient_forwarder.py
import asyncio
import httpx
from event_service import EventSubscriber

class AmbientForwarder:
    def __init__(self, config):
        self.api_url = config["ambient_api"]["endpoint"]
        self.api_key = config["ambient_api"]["api_key"]
        self.site_id = config["ambient_api"]["site_id"]
        self.client = httpx.AsyncClient()

    async def forward_event(self, event):
        payload = self.transform_event(event)

        response = await self.client.post(
            self.api_url,
            json=payload,
            headers={"Authorization": f"Bearer {self.api_key}"}
        )

        if response.status_code not in [200, 202]:
            await self.add_to_retry_queue(event)

    def transform_event(self, event):
        return {
            "event_id": event.id,
            "timestamp": event.timestamp.isoformat(),
            "event_type": event.type,
            "source": "azure_panel",
            "site_id": self.site_id,
            "data": {
                "card_number": event.card_number,
                "door_id": event.door_id,
                "door_name": event.door_name,
                "granted": event.granted
            }
        }

async def main():
    forwarder = AmbientForwarder(load_config())
    subscriber = EventSubscriber("/tmp/hal_events.sock")

    async for event in subscriber.stream():
        await forwarder.forward_event(event)
```

---

## Developer Tools

### Simulate Badge Read
```bash
./tools/simulate_badge -c 12345678 -d 1

# Options:
#   -c  Card number
#   -d  Door ID
#   -g  Force grant
#   -r  Force deny
```

### Monitor Events
```bash
./tools/monitor_events

# Output:
# [10:30:00] ACCESS_GRANTED card=12345678 door=1 "Front Door"
# [10:30:05] ACCESS_DENIED card=99999999 door=1 "Front Door" (unknown card)
```

### Test Ambient Connectivity
```bash
./tools/test_ambient -c /etc/hal/ambient_config.json

# Output:
# Testing Ambient.ai API connectivity...
# Endpoint: https://api.ambient.ai/v1/generic-cloud/events
# Status: OK (response time: 120ms)
```

### View System Status
```bash
./tools/hal_status

# Output:
# HAL Access Engine:    RUNNING (PID 1234)
# Ambient Forwarder:    RUNNING (PID 1235)
# Events Today:         1,234
# Events Pending Retry: 5
# Last Event:           10 seconds ago
```

---

## Systemd Services

### hal-engine.service
```ini
[Unit]
Description=HAL Access Engine
After=network.target

[Service]
ExecStart=/opt/hal/bin/hal_engine -c /etc/hal/hal_config.json
Restart=always
User=hal

[Install]
WantedBy=multi-user.target
```

### hal-ambient-forwarder.service
```ini
[Unit]
Description=HAL Ambient Forwarder
After=network.target hal-engine.service

[Service]
ExecStart=/opt/hal/bin/forwarder -c /etc/hal/ambient_config.json
Restart=always
User=hal
Environment=AMBIENT_API_KEY=your-api-key

[Install]
WantedBy=multi-user.target
```

---

## Security Considerations

1. **API Key Protection:** Store API key in environment variable or secrets manager
2. **TLS:** All Ambient API calls use HTTPS
3. **IPC Security:** Unix socket permissions (0600, hal user only)
4. **Event Sanitization:** Remove sensitive data before forwarding
5. **Audit Logging:** Log all forwarding attempts and failures

---

*Ambient.ai Integration - Connecting physical access to intelligent cloud analytics*
