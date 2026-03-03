# Aether Access - Ambient.ai Integration
## Proof of Concept Development Plan
## Version 1.0 | February 10, 2026

> "The machines answer to US."

---

## Executive Summary

This document defines the development plan for a **Proof of Concept (PoC)** demonstrating:

1. **Wiegand badge read** on a BLU-IC2 controller
2. **Access granted event generation** in the HAL
3. **Real-time event forwarding** to Ambient.ai Generic Cloud API

This implements the "Horizon 3 Disaggregated Model" from the CST Azure Intelligent Controller Software Scope, with focus on the event export pipeline.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          BLU-IC2 Controller                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌───────────────────┐    IPC Event Bus    ┌───────────────────────┐  │
│  │                   │◄───────────────────►│                       │  │
│  │   APP 1: HAL      │    (Unix Socket)    │  APP 2: Ambient.ai    │  │
│  │   Access Engine   │                     │  Event Forwarder      │  │
│  │                   │                     │                       │  │
│  │  - Wiegand Reader │                     │  - Event Subscriber   │  │
│  │  - Card Database  │                     │  - HTTP POST Client   │  │
│  │  - Access Logic   │                     │  - Retry Queue        │  │
│  │  - Event Producer │                     │  - UUID Management    │  │
│  │                   │                     │                       │  │
│  └─────────┬─────────┘                     └───────────┬───────────┘  │
│            │                                           │               │
└────────────┼───────────────────────────────────────────┼───────────────┘
             │ Wiegand                                   │ HTTPS
             │                                           │
      ┌──────▼──────┐                           ┌────────▼────────┐
      │   Reader    │                           │   Ambient.ai    │
      │  (26-bit)   │                           │  Generic Cloud  │
      └─────────────┘                           │  pacs-ingestion │
                                                └─────────────────┘
```

---

## Ambient.ai API Requirements

Based on the Generic Cloud Event Ingestion spec:

### Endpoint
```
POST https://pacs-ingestion.ambient.ai/v1/api/event
```

### Required Headers
```
x-api-key: <your-api-key>
Content-Type: application/json
User-Agent: AetherAccess/1.0
```

### Event Payload (Access Granted)
```json
{
  "sourceSystemUid": "UUID - identifies our BLU-IC2 installation",
  "deviceUid": "UUID - identifies the reader that generated the event",
  "deviceName": "Front Door Reader",
  "deviceType": "Reader",
  "eventUid": "UUID - unique per event instance",
  "alarmName": "Access Granted",
  "alarmUid": "UUID - identifies the 'Access Granted' alarm type",
  "eventOccuredAtTimestamp": 1707580800,
  "eventPublishedAtTimestamp": 1707580801,
  "personUid": "UUID - optional, if we have cardholder mapping",
  "accessItemKey": "12345678"
}
```

### Key Insight from Spec
> "Fields in orange do not appear in the Ambient.ai product at the moment"

This means `personUid`, `personFirstName`, `personLastName` may not be visible yet. The critical fields are:
- `deviceUid` - MUST be sent
- `alarmName` - What shows in Ambient.ai
- `accessItemKey` - The card number

---

## Component Design

### APP 1: HAL Access Engine (hal_engine)

**Purpose**: Simulate/handle Wiegand badge reads and generate events

**Files**:
```
poc/
├── app1_hal_engine/
│   ├── hal_engine.c              # Main daemon
│   ├── wiegand_handler.c/.h      # Wiegand protocol parser
│   ├── card_database.c/.h        # SQLite card lookup
│   ├── access_logic.c/.h         # Access decision
│   ├── event_producer.c/.h       # Event generation
│   ├── ipc_publisher.c/.h        # Unix socket publisher
│   ├── config.c/.h               # Configuration loader
│   └── logger.c/.h               # Diagnostic logging
```

**Key Functions**:
```c
// Wiegand handler
void wiegand_on_card_read(uint32_t facility_code, uint32_t card_number);

// Access logic
access_result_t check_access(uint32_t card_number, time_t timestamp);

// Event generation
hal_event_t* create_access_event(access_result_t result, card_info_t* card);

// IPC publishing
void publish_event(hal_event_t* event);
```

**Event Structure**:
```c
typedef struct {
    char event_uid[37];           // UUID string
    char device_uid[37];          // Reader UUID
    char device_name[64];         // "Front Door Reader"
    char device_type[16];         // "Reader"
    char alarm_name[64];          // "Access Granted" or "Access Denied"
    char alarm_uid[37];           // Alarm type UUID
    int64_t occurred_timestamp;   // Unix epoch seconds
    int64_t published_timestamp;  // When we send it
    char person_uid[37];          // Optional cardholder UUID
    char access_item_key[32];     // Card number as string
} hal_event_t;
```

---

### APP 2: Ambient.ai Event Forwarder (ambient_forwarder)

**Purpose**: Subscribe to events and forward to Ambient.ai

**Files**:
```
poc/
├── app2_ambient_forwarder/
│   ├── forwarder.c               # Main daemon
│   ├── ipc_subscriber.c/.h       # Unix socket subscriber
│   ├── ambient_client.c/.h       # HTTP POST to Ambient.ai
│   ├── retry_queue.c/.h          # Failed event retry queue
│   ├── uuid_registry.c/.h        # UUID mapping management
│   ├── config.c/.h               # Configuration (API key, URL)
│   └── logger.c/.h               # Diagnostic logging
```

**Key Functions**:
```c
// IPC subscription
void subscribe_to_events(const char* socket_path);
void on_event_received(hal_event_t* event);

// Ambient.ai client
int post_event_to_ambient(hal_event_t* event, ambient_config_t* config);

// Retry logic
void queue_failed_event(hal_event_t* event);
void process_retry_queue(void);
```

**Configuration**:
```json
{
  "ambient_api": {
    "endpoint": "https://pacs-ingestion.ambient.ai/v1/api/event",
    "api_key": "your-api-key-here",
    "timeout_ms": 5000,
    "max_retries": 3,
    "retry_delay_ms": 1000
  },
  "source_system": {
    "uid": "e22833e4-cfdb-40c1-9b44-490adc053330",
    "name": "Aether Access PoC"
  },
  "ipc": {
    "socket_path": "/tmp/hal_events.sock"
  }
}
```

---

### IPC Event Bus (Shared)

**Purpose**: Real-time event streaming between apps

**Protocol**: Unix Domain Socket with JSON messages

**Files**:
```
poc/
├── shared/
│   ├── ipc_common.h              # Shared IPC definitions
│   ├── event_types.h             # Event structure definitions
│   ├── json_serializer.c/.h      # Event to/from JSON
│   └── uuid_utils.c/.h           # UUID generation
```

**Message Format**:
```json
{
  "msg_type": "EVENT",
  "version": 1,
  "payload": {
    "event_uid": "abc123de-f456-4789-8012-345678901232",
    "device_uid": "62023ea7-3968-4f74-b948-1e3d821dc939",
    "device_name": "Front Door Reader",
    "device_type": "Reader",
    "alarm_name": "Access Granted",
    "alarm_uid": "12634ea7-3968-4f74-b948-1e3d821dc939",
    "occurred_at": 1707580800,
    "published_at": 1707580801,
    "person_uid": null,
    "access_item_key": "39421"
  }
}
```

---

## Developer Tools

### Tool 1: Event Simulator (simulate_badge)

**Purpose**: Simulate Wiegand badge reads without hardware

```bash
# Simulate a badge read
./simulate_badge --card 12345678 --facility 100

# Simulate multiple reads
./simulate_badge --card 12345678 --count 10 --delay 1000

# Simulate unknown card (access denied)
./simulate_badge --card 99999999 --unknown
```

**Implementation**:
```c
// Sends simulated Wiegand data to HAL engine via pipe/signal
void simulate_wiegand_read(uint32_t facility, uint32_t card);
```

---

### Tool 2: Event Monitor (monitor_events)

**Purpose**: Real-time event stream visualization

```bash
# Monitor all events
./monitor_events

# Filter by event type
./monitor_events --filter "Access Granted"

# JSON output for piping
./monitor_events --json | jq .

# Save to file
./monitor_events --output events.log
```

**Output Format**:
```
[2026-02-10 15:30:45] EVENT: Access Granted
  Device: Front Door Reader (62023ea7-3968...)
  Card: 12345678
  Latency: 12ms
  Status: FORWARDED to Ambient.ai (HTTP 200)

[2026-02-10 15:30:47] EVENT: Access Denied
  Device: Front Door Reader (62023ea7-3968...)
  Card: 99999999
  Reason: Unknown card
  Status: FORWARDED to Ambient.ai (HTTP 200)
```

---

### Tool 3: Ambient.ai Test Client (test_ambient)

**Purpose**: Test Ambient.ai API connectivity and send test events

```bash
# Test API connectivity
./test_ambient --ping

# Send a test event
./test_ambient --send-test

# Validate configuration
./test_ambient --validate-config

# Dry run (show what would be sent)
./test_ambient --dry-run --card 12345678
```

**Implementation**:
```c
// Test Ambient.ai endpoint
int test_ambient_connectivity(ambient_config_t* config);

// Send test event
int send_test_event(ambient_config_t* config);
```

---

### Tool 4: Log Viewer (hal_logs)

**Purpose**: Unified log viewing with filtering

```bash
# View all logs
./hal_logs --all

# View HAL engine logs only
./hal_logs --app hal_engine

# View forwarder logs only
./hal_logs --app ambient_forwarder

# Follow mode (like tail -f)
./hal_logs --follow

# Filter by level
./hal_logs --level ERROR

# Time range
./hal_logs --since "5 minutes ago"
```

**Log Format**:
```
[2026-02-10 15:30:45.123] [hal_engine] [INFO] Wiegand card read: FC=100 CN=12345678
[2026-02-10 15:30:45.125] [hal_engine] [INFO] Access check: card=12345678 result=GRANTED
[2026-02-10 15:30:45.126] [hal_engine] [INFO] Event published: event_uid=abc123de...
[2026-02-10 15:30:45.130] [forwarder] [INFO] Event received: abc123de...
[2026-02-10 15:30:45.245] [forwarder] [INFO] Ambient.ai POST: 200 OK (115ms)
```

---

### Tool 5: System Status Dashboard (hal_status)

**Purpose**: Quick system health check

```bash
./hal_status

# Output:
╔══════════════════════════════════════════════════════════════════╗
║                    AETHER ACCESS - SYSTEM STATUS                 ║
╠══════════════════════════════════════════════════════════════════╣
║ HAL Engine:           ✓ RUNNING (PID: 1234)                      ║
║ Ambient Forwarder:    ✓ RUNNING (PID: 1235)                      ║
║ IPC Socket:           ✓ CONNECTED                                ║
║ Ambient.ai API:       ✓ REACHABLE (45ms latency)                 ║
╠══════════════════════════════════════════════════════════════════╣
║ Events Today:         127 (125 granted, 2 denied)                ║
║ Events Forwarded:     127 (100%)                                 ║
║ Failed Forwards:      0                                          ║
║ Retry Queue:          0 pending                                  ║
╠══════════════════════════════════════════════════════════════════╣
║ Cards in Database:    50                                         ║
║ Last Event:           15:30:45 (2 seconds ago)                   ║
║ Uptime:               4h 32m 15s                                 ║
╚══════════════════════════════════════════════════════════════════╝
```

---

## Development Phases

### Phase 1: Foundation (Day 1-2)

**Goal**: Basic infrastructure and IPC

**Tasks**:
1. [ ] Create `poc/` directory structure
2. [ ] Implement shared event types (`event_types.h`)
3. [ ] Implement JSON serializer (`json_serializer.c`)
4. [ ] Implement UUID utilities (`uuid_utils.c`)
5. [ ] Implement IPC publisher (`ipc_publisher.c`)
6. [ ] Implement IPC subscriber (`ipc_subscriber.c`)
7. [ ] Create basic logging framework (`logger.c`)
8. [ ] Write unit tests for IPC

**Deliverable**: Working IPC event bus

---

### Phase 2: HAL Engine (Day 2-3)

**Goal**: Event generation and card lookup

**Tasks**:
1. [ ] Implement Wiegand parser (26-bit)
2. [ ] Implement card database (SQLite)
3. [ ] Implement access logic
4. [ ] Implement event producer
5. [ ] Create main daemon (`hal_engine.c`)
6. [ ] Implement badge simulator tool
7. [ ] Write unit tests

**Deliverable**: HAL generating events on badge reads

---

### Phase 3: Ambient Forwarder (Day 3-4)

**Goal**: HTTP POST to Ambient.ai

**Tasks**:
1. [ ] Implement Ambient.ai HTTP client (libcurl)
2. [ ] Implement UUID registry (device/alarm mappings)
3. [ ] Implement retry queue (SQLite)
4. [ ] Create main daemon (`forwarder.c`)
5. [ ] Implement test client tool
6. [ ] Write unit tests

**Deliverable**: Events forwarding to Ambient.ai

---

### Phase 4: Developer Tools (Day 4-5)

**Goal**: Complete troubleshooting toolkit

**Tasks**:
1. [ ] Implement event monitor tool
2. [ ] Implement log viewer tool
3. [ ] Implement status dashboard tool
4. [ ] Create comprehensive logging
5. [ ] Add metrics collection
6. [ ] Write tool documentation

**Deliverable**: Full developer toolkit

---

### Phase 5: Integration & Testing (Day 5-6)

**Goal**: End-to-end validation

**Tasks**:
1. [ ] Integration test: badge → event → Ambient.ai
2. [ ] Test retry logic (network failure simulation)
3. [ ] Test multiple concurrent events
4. [ ] Performance testing (events/second)
5. [ ] Error handling validation
6. [ ] Documentation updates

**Deliverable**: Validated PoC ready for demo

---

## File Structure

```
poc/
├── PROOF_OF_CONCEPT_PLAN.md          # This document
├── CMakeLists.txt                     # Build configuration
├── Makefile                           # Alternative build
│
├── shared/                            # Shared components
│   ├── ipc_common.h
│   ├── event_types.h
│   ├── json_serializer.c
│   ├── json_serializer.h
│   ├── uuid_utils.c
│   ├── uuid_utils.h
│   └── cJSON.c/.h                    # JSON library
│
├── app1_hal_engine/                   # Application 1
│   ├── main.c
│   ├── hal_engine.c
│   ├── hal_engine.h
│   ├── wiegand_handler.c
│   ├── wiegand_handler.h
│   ├── card_database.c
│   ├── card_database.h
│   ├── access_logic.c
│   ├── access_logic.h
│   ├── event_producer.c
│   ├── event_producer.h
│   ├── ipc_publisher.c
│   ├── ipc_publisher.h
│   ├── config.c
│   ├── config.h
│   ├── logger.c
│   └── logger.h
│
├── app2_ambient_forwarder/            # Application 2
│   ├── main.c
│   ├── forwarder.c
│   ├── forwarder.h
│   ├── ipc_subscriber.c
│   ├── ipc_subscriber.h
│   ├── ambient_client.c
│   ├── ambient_client.h
│   ├── retry_queue.c
│   ├── retry_queue.h
│   ├── uuid_registry.c
│   ├── uuid_registry.h
│   ├── config.c
│   ├── config.h
│   ├── logger.c
│   └── logger.h
│
├── tools/                             # Developer tools
│   ├── simulate_badge.c
│   ├── monitor_events.c
│   ├── test_ambient.c
│   ├── hal_logs.c
│   └── hal_status.c
│
├── config/                            # Configuration files
│   ├── hal_engine.json
│   ├── ambient_forwarder.json
│   └── devices.json                  # Device UUID mappings
│
├── data/                              # Runtime data
│   ├── cards.db                      # Card database
│   ├── retry_queue.db               # Failed event queue
│   └── uuid_registry.db             # UUID mappings
│
├── logs/                              # Log files
│   ├── hal_engine.log
│   ├── ambient_forwarder.log
│   └── system.log
│
├── tests/                             # Unit tests
│   ├── test_ipc.c
│   ├── test_wiegand.c
│   ├── test_access_logic.c
│   ├── test_ambient_client.c
│   └── test_json.c
│
└── scripts/                           # Management scripts
    ├── start_poc.sh
    ├── stop_poc.sh
    ├── status_poc.sh
    ├── seed_database.sh
    └── run_tests.sh
```

---

## Configuration Files

### hal_engine.json
```json
{
  "database": {
    "path": "./data/cards.db"
  },
  "ipc": {
    "socket_path": "/tmp/hal_events.sock",
    "buffer_size": 4096
  },
  "reader": {
    "device_uid": "62023ea7-3968-4f74-b948-1e3d821dc939",
    "device_name": "Front Door Reader",
    "device_type": "Reader"
  },
  "logging": {
    "level": "DEBUG",
    "file": "./logs/hal_engine.log",
    "console": true,
    "max_size_mb": 10,
    "rotation": 5
  }
}
```

### ambient_forwarder.json
```json
{
  "ambient_api": {
    "endpoint": "https://pacs-ingestion.ambient.ai/v1/api/event",
    "api_key": "YOUR_API_KEY_HERE",
    "timeout_ms": 5000,
    "user_agent": "AetherAccess/1.0"
  },
  "source_system": {
    "uid": "e22833e4-cfdb-40c1-9b44-490adc053330",
    "name": "Aether Access PoC"
  },
  "alarm_definitions": {
    "access_granted": {
      "uid": "12634ea7-3968-4f74-b948-1e3d821dc939",
      "name": "Access Granted"
    },
    "access_denied": {
      "uid": "22634ea7-3968-4f74-b948-1e3d821dc939",
      "name": "Access Denied"
    },
    "door_forced_open": {
      "uid": "32634ea7-3968-4f74-b948-1e3d821dc939",
      "name": "Door Forced Open"
    },
    "door_held_open": {
      "uid": "42634ea7-3968-4f74-b948-1e3d821dc939",
      "name": "Door Held Open"
    }
  },
  "ipc": {
    "socket_path": "/tmp/hal_events.sock"
  },
  "retry": {
    "max_attempts": 3,
    "initial_delay_ms": 1000,
    "max_delay_ms": 30000,
    "queue_path": "./data/retry_queue.db"
  },
  "logging": {
    "level": "DEBUG",
    "file": "./logs/ambient_forwarder.log",
    "console": true
  }
}
```

### devices.json (Device Registry)
```json
{
  "source_system": {
    "uid": "e22833e4-cfdb-40c1-9b44-490adc053330",
    "name": "Aether Access PoC",
    "type": "Panel"
  },
  "devices": [
    {
      "uid": "62023ea7-3968-4f74-b948-1e3d821dc939",
      "name": "Front Door Reader",
      "type": "Reader",
      "port": 1
    },
    {
      "uid": "72023ea7-3968-4f74-b948-1e3d821dc939",
      "name": "Back Door Reader",
      "type": "Reader",
      "port": 2
    }
  ]
}
```

---

## Success Criteria

### Functional Requirements

| Requirement | Test | Pass Criteria |
|-------------|------|---------------|
| Badge read detection | Simulate 26-bit Wiegand | Event generated within 100ms |
| Card lookup | Query test database | Correct access decision |
| Event generation | Check event structure | All required fields populated |
| IPC delivery | Monitor subscriber | Event received within 10ms |
| Ambient.ai POST | Check HTTP response | HTTP 200 within 2 seconds |
| Retry on failure | Simulate network error | Event queued and retried |
| Logging | Check log files | All operations logged |

### Non-Functional Requirements

| Requirement | Target |
|-------------|--------|
| Event latency (badge → Ambient.ai) | < 2 seconds |
| Memory footprint (each app) | < 10 MB |
| CPU usage (idle) | < 1% |
| Events per second | > 10/s sustained |
| Retry queue capacity | 10,000 events |
| Log rotation | 5 files × 10 MB |

---

## Demo Script

### Setup
```bash
# 1. Build the PoC
cd poc && make

# 2. Seed the card database
./scripts/seed_database.sh

# 3. Configure Ambient.ai API key
nano config/ambient_forwarder.json

# 4. Start the system
./scripts/start_poc.sh
```

### Demo Walkthrough
```bash
# Terminal 1: Monitor events
./tools/monitor_events

# Terminal 2: Check system status
./tools/hal_status

# Terminal 3: Simulate badge reads
./tools/simulate_badge --card 12345678
./tools/simulate_badge --card 99999999 --unknown
./tools/simulate_badge --card 12345678 --count 5 --delay 500
```

### Expected Output in Ambient.ai
- Events appear in Ambient.ai dashboard
- "Access Granted" events linked to device
- Event timestamps match real time
- No duplicate events

---

## Next Steps After PoC

1. **Hardware Integration**: Connect real Wiegand reader to BLU-IC2
2. **Initial Device Sync**: Send device definitions to Ambient.ai
3. **Cardholder Mapping**: Link cards to person UIDs
4. **Additional Event Types**: Door forced, door held open
5. **PIAM Integration**: Add CloudGate API service
6. **Docker Containerization**: Package for BLU-IC2 deployment

---

*Document Created: February 10, 2026*
*Familiar: FAM-HAL-v1.0-001*
*Master: Final_Axiom*

*"Aether Access - Where hardware meets abstraction."*
