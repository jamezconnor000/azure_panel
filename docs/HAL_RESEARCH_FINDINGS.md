# HAL Research Findings & Implementation Status
## Azure Panel Deep Dive Analysis
## March 2026

---

## Executive Summary

This document compiles research findings from the Azure Access Technology SDK documentation, libosdp open-source library, and the existing HAL codebase to identify implementation status and refinement opportunities.

---

## Research Sources Analyzed

### 1. Azure Access Technology Wiki (PDF Documentation)
- **Location:** `/Research/Azure_Wiki_PDFs/` (101 PDF files)
- **Key Files Analyzed:**
  - `common _ Azure Access Technology Wiki.pdf` - SDK types, LPA addressing
  - `Card _ Azure Access Technology Wiki.pdf` - Card management API
  - `AccGrantEvent _ Azure Access Technology Wiki.pdf` - Access grant events
  - `AccDenyEvent _ Azure Access Technology Wiki.pdf` - Access deny events
  - `AccessPointEvent _ Azure Access Technology Wiki.pdf` - Door events
  - `EventSubscription _ Azure Access Technology Wiki.pdf` - Event subscription
  - `EventBufferDefinition _ Azure Access Technology Wiki.pdf` - Buffer config
  - `ErrorCode _ Azure Access Technology Wiki.pdf` - Error codes
  - `FieldDefinition _ Azure Access Technology Wiki.pdf` - Card fields
  - `CmdType _ Azure Access Technology Wiki.pdf` - Command types
  - `DeviceInfo _ Azure Access Technology Wiki.pdf` - Device information

### 2. Azure Access Technology Website
- BLU-IC2 specifications: 1GHz CPU, 512MB Flash, 256MB RAM
- 1M+ card capacity, 10K cards/second download speed
- 2 RS-485 ports, up to 8 OSDP readers per port
- SDK available in C++, C#, Java, Python (proprietary)

### 3. LibOSDP Open Source Library
- **Repository:** https://github.com/goToMain/libosdp
- **Documentation:** https://doc.osdp.dev/
- **License:** Apache-2.0
- Complete OSDP v2.2 implementation with AES-128 Secure Channel

### 4. Existing HAL Documentation
- `HAL_OSDP_Implementation_Guide.txt`
- `HAL_OSDP_Secure_Channel_Guide.txt`
- `HAL_Complete_System_Guide.txt`

---

## Implementation Status Matrix

### HAL Core Components

| Component | Status | Files | Notes |
|-----------|--------|-------|-------|
| Event Buffer | COMPLETE | `hal.c`, `event_manager.c` | 100K circular buffer |
| Card Database | COMPLETE | `card_database.c`, `hal_core_api.py` | 1M+ capacity SQLite |
| Access Logic | COMPLETE | `access_logic.c`, `access_logic_sdk.c` | Permission checking |
| OSDP Reader | COMPLETE | `osdp_reader.c` | RS-485 communication |
| OSDP Secure Channel | COMPLETE | `osdp_secure_channel.c` | AES-128 encryption, 53 tests passing |
| JSON Config | COMPLETE | `json_config.c` | Configuration parsing |
| Event Exporter | COMPLETE | `event_exporter.c` | Event export daemon |
| Diagnostic Logger | COMPLETE | `diagnostic_logger.c` | Logging infrastructure |

### SDK Module Wrappers

| Module | Status | File | Notes |
|--------|--------|------|-------|
| Timezones | COMPLETE | `sdk_modules/timezones/timezone.c` | Full implementation |
| Permissions | COMPLETE | `sdk_modules/permissions/permission.c` | Access levels |
| Holidays | COMPLETE | `sdk_modules/holidays/holiday.c` | Holiday calendar |
| Relays | COMPLETE | `sdk_modules/relays/relay.c` | Output control |
| Readers | COMPLETE | `sdk_modules/readers/reader.c` | Wiegand + OSDP |
| Access Points | COMPLETE | `sdk_modules/access_points/access_point.c` | Door config |
| Areas | COMPLETE | `sdk_modules/areas/area.c` | Area management |
| Card Formats | COMPLETE | `sdk_modules/card_formats/card_format.c` | Format parsing |

### API Layer

| Component | Status | Port | File | Notes |
|-----------|--------|------|------|-------|
| HAL Core API | COMPLETE | 8081 | `api/hal_core_api.py` | Standalone panel brain |
| Aether Access API | COMPLETE | 8080 | `gui/backend/api_aether.py` | Management interface |
| Event Reporting | COMPLETE | - | `gui/backend/event_reporting.py` | Human-readable events |
| HAL Client | COMPLETE | - | `gui/backend/hal_client.py` | API client library |

### Planned Components

| Component | Status | Notes |
|-----------|--------|-------|
| Ambient.ai Forwarder | PLANNED | Event streaming daemon |
| React Frontend | PLANNED | Browser UI |
| JWT Authentication | PLANNED | Security hardening |
| HTTPS/TLS | PLANNED | Encrypted connections |

---

## Key Findings from SDK Documentation

### 1. Event Buffer Specifications

From Azure SDK documentation:
```
EventBufferConsts_MinSize         = 1,000
EventBufferConsts_DefaultCacheSize = 10,000
EventBufferConsts_DefaultSize     = 100,000
EventBufferConsts_MaxSize         = 500,000
```

**HAL Implementation:** Uses 100,000 (default) - ALIGNED

**Warning from docs:** Flushing events too frequently wears out flash storage.

### 2. Card Database Architecture

From Azure SDK:
- Card Id is always first field
- Variable permission count per card
- Dynamic field support
- Permission entries and exclusion entries

**HAL Implementation:** SQLite with:
- Card number (unique)
- Facility code
- Permission/access level reference
- Holder name
- Active status and validity dates

### 3. Event Structure Alignment

**Azure SDK AccGrantEvent fields:**
- SerialNumber, EventDateTime
- Node, Type, SubType
- Source (Reader LPA)
- Card, Flags, Flags2
- Strike, FormatId
- TransactionId
- FieldList

**HAL Event Structure:** Simplified version with essential fields.

### 4. OSDP Secure Channel

**LibOSDP Key Hierarchy:**
1. **SCBK** (Secure Channel Base Key) - Per-device 128-bit key
2. **Master Key** - Optional, deprecated by spec
3. **Session Keys** - S-ENC, S-MAC1, S-MAC2 derived from SCBK

**HAL Implementation:** Complete with:
- AES-128 CBC encryption
- Session key derivation
- Cryptogram generation/verification
- MAC authentication
- 53 passing tests

### 5. Error Code Alignment

**Azure SDK Error Codes (partial):**
- ErrorCode_OK = 0
- ErrorCode_BadParams = 21
- ErrorCode_ObjectNotfound = 22
- ErrorCode_CommunicationError = 25
- ErrorCode_ExecuteTimeout = 29

**HAL Implementation:** Uses subset with crypto extensions (27-30).

---

## Refinement Recommendations

### High Priority

1. **Event Structure Enrichment**
   - Add TransactionId for PACS matching
   - Add FieldList for dynamic card fields
   - Add SubType for detailed event classification

2. **Card Database Enhancement**
   - Support multiple permissions per card
   - Add exclusion entry support
   - Implement dynamic field storage

3. **Ambient.ai Forwarder**
   - Poll HAL events via REST API
   - Transform to Ambient.ai format
   - Implement retry queue
   - Mark events as exported

### Medium Priority

4. **Permission Flags Implementation**
   - HostGrant, HostDeny
   - SoftAPB, APBExempt
   - Visitor/Escort flags
   - UnlockReader authority

5. **Access Point State Machine**
   - Door contact states (KCMFTA)
   - EPB (Exit Push Button) states
   - Force/Held open tracking
   - Mode transitions

6. **Device Info Endpoint**
   - Return device model (HC2)
   - Card counts (current/max)
   - RAM/Flash availability
   - Version information

### Lower Priority

7. **Command Type System**
   - Implement CmdType enumeration
   - Add subtype handling
   - Protocol command support

8. **Multi-Node Support**
   - Node addressing
   - Cluster-wide operations
   - LPA routing

---

## LibOSDP Integration Notes

### Current HAL OSDP Implementation

The HAL includes a custom OSDP implementation in `osdp_reader.c` and `osdp_secure_channel.c`. This provides:

- Complete OSDP packet building/parsing
- CRC-16 calculation
- RS-485 serial communication
- AES-128 secure channel
- LED/buzzer control
- Card read event handling

### LibOSDP Comparison

| Feature | HAL Implementation | LibOSDP |
|---------|-------------------|---------|
| Language | C | C (with Python/Rust bindings) |
| Secure Channel | AES-128 CBC | AES-128 |
| Memory Model | Static allocation | Zero runtime allocation |
| Threading | pthread-based | Non-blocking async |
| Refresh Rate | Configurable | 50ms minimum |
| License | Proprietary | Apache-2.0 |

### Integration Options

1. **Keep Custom Implementation**
   - Full control over behavior
   - Already integrated with HAL types
   - Tested and working

2. **Migrate to LibOSDP**
   - Active community maintenance
   - Better spec compliance
   - Additional features (file transfer)

**Recommendation:** Keep custom implementation for now. Consider LibOSDP for future OSDP v3 support.

---

## Test Coverage

### Existing Test Files

| Test | Status | Description |
|------|--------|-------------|
| `test_osdp_secure_channel.c` | 53/53 PASS | Secure channel encryption |
| `test_osdp_reader.c` | ALL PASS | OSDP reader protocol |
| `test_sdk_database.c` | ALL PASS | Database operations |
| `test_sdk_integration.c` | ALL PASS | Module integration |
| `test_hal_integration.c` | ALL PASS | HAL API tests |
| `test_timezone.c` | ALL PASS | Timezone logic |
| `test_sdk_permissions.c` | ALL PASS | Permission checks |
| `test_sdk_holidays.c` | ALL PASS | Holiday calendar |

### Recommended Additional Tests

1. Event buffer overflow handling
2. Card database stress test (1M cards)
3. Multi-reader OSDP polling
4. Secure channel key rotation
5. API endpoint integration tests

---

## File Locations Quick Reference

### Core C Library
```
src/hal_core/
├── hal.c                    # Main HAL implementation
├── event_manager.c          # Event buffer management
├── card_database.c          # Card storage
├── access_logic.c           # Access decision engine
├── osdp_reader.c            # OSDP protocol
├── osdp_secure_channel.c    # AES-128 encryption
├── diagnostic_logger.c      # Logging
└── json_config.c            # Configuration
```

### Python API
```
api/
├── hal_core_api.py          # HAL Core REST API (8081)
└── hal_api_server.py        # Legacy API

gui/backend/
├── api_aether.py            # Aether Access API (8080)
├── hal_client.py            # HAL API client
└── event_reporting.py       # Event formatting
```

### Documentation
```
docs/
├── AZURE_SDK_REFERENCE.md   # SDK documentation
├── HAL_RESEARCH_FINDINGS.md # This document
└── (other guides)
```

---

## Next Steps

1. **Implement Ambient.ai Forwarder** (Phase 4 of project plan)
   - Create `ambient/forwarder.py`
   - Add event polling from HAL
   - Implement Ambient.ai REST client
   - Add retry queue with backoff

2. **Build React Frontend** (Phase 5)
   - Dashboard with statistics
   - Event log viewer
   - Cardholder management
   - Access level configuration

3. **Security Hardening** (Phase 6)
   - JWT authentication
   - Role-based access control
   - HTTPS/TLS support
   - Rate limiting

---

*Research conducted by Final_Axiom | March 2026*
*Azure Panel Project - Aether Access*
