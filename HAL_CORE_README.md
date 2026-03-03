# HAL Core - Hardware Abstraction Layer

**Version:** 2.0.0
**Language:** C (C11)
**Status:** Production Ready

---

## Overview

HAL Core is the foundational C library that provides hardware abstraction for Azure BLU-IC2 access control panels. It handles all low-level communication, event processing, and access control logic.

---

## Features

- **Event-Driven Architecture** - 100K event circular buffer
- **OSDP Secure Channel** - AES-128 encryption for reader communication
- **Card Database** - SQLite-backed, 1M+ card capacity
- **Access Logic** - Permission evaluation with timezone support
- **Offline Operation** - Full functionality without network
- **SDK Integration** - Advanced features via modular SDK

---

## Directory Structure

```
src/
├── hal_core/              # Core HAL implementation
│   ├── hal.c/h            # Main HAL interface
│   ├── event_manager.c/h  # Event buffer management
│   ├── event_database.c/h # Event persistence
│   ├── event_exporter.c/h # Event export daemon
│   ├── card_database.c/h  # Card lookup
│   ├── access_logic.c/h   # Basic access decisions
│   ├── access_logic_sdk.c/h # SDK-enhanced access logic
│   ├── config.c/h         # Configuration management
│   ├── json_config.c/h    # JSON config loading
│   ├── diagnostic_logger.c/h # Diagnostics
│   ├── osdp_reader.c/h    # OSDP protocol
│   ├── osdp_secure_channel.c/h # OSDP SC (AES-128)
│   └── osdp_sc_logging.c/h # SC diagnostics
│
├── sdk_modules/           # Advanced SDK features
│   ├── common/            # Shared types and DB schema
│   ├── permissions/       # Permission rules
│   ├── timezones/         # Schedule management
│   ├── holidays/          # Holiday handling
│   ├── readers/           # Reader configuration
│   ├── relays/            # Relay control
│   ├── events/            # Event structures
│   ├── areas/             # Area management
│   ├── access_points/     # Door/access point config
│   ├── card_formats/      # Card format definitions
│   └── group_lists/       # Cardholder groups
│
├── sdk_wrapper/           # Command interface
│   ├── sdk_interface.c    # Command dispatch
│   └── command_handler.c  # Command execution
│
└── utils/                 # Utilities
    ├── cJSON.c/h          # JSON parsing
    ├── logging.c          # Unified logging
    ├── queue.c            # Queue management
    └── timestamp.c        # Time utilities

include/
├── hal_public.h           # Public API header
└── hal_types.h            # Type definitions

tests/
├── test_hal_unit.c        # Unit tests
├── test_hal_integration.c # Integration tests
├── test_osdp_reader.c     # OSDP tests
├── test_osdp_secure_channel.c # OSDP SC tests
├── test_timezone.c        # Timezone tests
├── test_sdk_integration.c # SDK tests
└── test_sdk_database.c    # Database tests

examples/
├── basic_access.c         # Simple access check
├── complete_sdk_demo.c    # Full SDK demo
├── event_subscription.c   # Event handling
└── osdp_secure_demo.c     # OSDP SC demo
```

---

## Public API

### Initialization
```c
#include "hal_public.h"

// Initialize HAL with configuration
HAL_RuntimeConfig_t config = {
    .event_buffer_size = 100000,
    .max_events_before_ack = 1000,
    .connection_timeout_ms = 5000,
    .log_level = LOG_INFO
};

ErrorCode_t result = HAL_Initialize(&config);
```

### Access Control
```c
// Process card read
AccessLogicResult_t decision = HAL_ProcessCardRead(card_number, door_id);

if (decision.granted) {
    printf("Access granted: %s\n", decision.reason);
    // Door unlocked automatically
} else {
    printf("Access denied: %s\n", decision.reason);
}
```

### Event Handling
```c
// Subscribe to events
void my_event_handler(AccessEvent_t* event) {
    printf("Event: %s at door %d\n", event->eventType, event->doorNumber);
}

HAL_SubscribeEvents(my_event_handler);

// Or poll for events
AccessEvent_t* event;
while ((event = HAL_GetNextEvent()) != NULL) {
    process_event(event);
    HAL_AcknowledgeEvent(event);
}
```

### Reader Control
```c
// Set reader mode
LPA_t reader = {.type = LPAType_Reader, .id = 1, .node_id = 0};

HAL_SetReaderMode(reader, ReaderMode_CardOnly);
HAL_SetReaderMode(reader, ReaderMode_CardAndPin);
HAL_SetReaderMode(reader, ReaderMode_Locked);
HAL_SetReaderMode(reader, ReaderMode_Unlocked);
```

### OSDP Secure Channel
```c
// Enable OSDP SC on reader
uint8_t scbk[16] = {0x01, 0x02, ...}; // 16-byte key
OSDP_SecureChannel_Enable(reader_address, scbk);

// Check status
OSDP_SCStatus_t status = OSDP_SecureChannel_GetStatus(reader_address);
printf("SC Status: %s\n", status.secure ? "Active" : "Inactive");
```

---

## Build Instructions

### Prerequisites
- CMake 3.15+
- GCC or Clang
- SQLite3 development libraries
- OpenSSL development libraries (for OSDP SC)

### Build
```bash
mkdir build && cd build
cmake ..
make

# Run tests
make test

# Or run tests individually
./test_hal_unit
./test_hal_integration
./test_osdp_secure_channel
```

### Build Output
```
libhal_core.a       # Core HAL library
libsdk_wrapper.a    # SDK interface
libhal_utils.a      # Utilities
libevent_database.a # Event persistence
libconfig.a         # Configuration
```

---

## Configuration

### hal_config.json
```json
{
  "database": {
    "card_db_path": "/var/lib/hal/cards.db",
    "event_db_path": "/var/lib/hal/events.db"
  },
  "readers": [
    {
      "id": 1,
      "name": "Front Door",
      "type": "osdp",
      "address": 0,
      "osdp_secure": true
    }
  ],
  "event_buffer": {
    "size": 100000,
    "ack_threshold": 1000
  },
  "logging": {
    "level": "info",
    "file": "/var/log/hal/hal.log"
  }
}
```

---

## Integration with Other Components

### Python Backend
The Python backend uses CFFI/ctypes to call HAL functions:
```python
from hal_interface import HAL

hal = HAL()
hal.initialize("/etc/hal/hal_config.json")

result = hal.process_card_read(card_number=12345, door_id=1)
print(f"Access: {'granted' if result.granted else 'denied'}")
```

### Ambient.ai Integration
HAL publishes events to an IPC bus for the Ambient forwarder:
```c
// Events are automatically published when access decisions are made
// Ambient forwarder subscribes via Unix domain socket
```

---

## Error Codes

| Code | Name | Description |
|------|------|-------------|
| 0 | ErrorCode_OK | Success |
| 1 | ErrorCode_Error | General error |
| 2 | ErrorCode_BadParams | Invalid parameters |
| 3 | ErrorCode_NotFound | Resource not found |
| 4 | ErrorCode_OutOfMemory | Memory allocation failed |
| 5 | ErrorCode_Timeout | Operation timed out |
| 6 | ErrorCode_Busy | Resource busy |

---

## Thread Safety

- Event manager is thread-safe with mutex protection
- Card database uses SQLite serialized mode
- OSDP operations should be called from single thread

---

## Memory Management

- HAL_Initialize allocates global state
- HAL_Shutdown frees all resources
- Events are reference counted
- Use HAL_AcknowledgeEvent to release event memory

---

*HAL Core - The foundation of Azure Panel access control*
