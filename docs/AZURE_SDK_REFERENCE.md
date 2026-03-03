# Azure Access Technology SDK Reference
## HAL Integration Documentation
## Compiled: March 2026

---

## Table of Contents

1. [Hardware Overview](#hardware-overview)
2. [SDK Architecture](#sdk-architecture)
3. [Core Types and Constants](#core-types-and-constants)
4. [Card Management](#card-management)
5. [Event System](#event-system)
6. [Access Control Events](#access-control-events)
7. [OSDP Protocol](#osdp-protocol)
8. [Error Codes](#error-codes)
9. [LibOSDP Integration](#libosdp-integration)

---

## Hardware Overview

### BLU-IC2 Controller Specifications

| Specification | Value |
|---------------|-------|
| **CPU** | 1GHz ARM Processor |
| **Flash Storage** | 512MB |
| **RAM** | 256MB |
| **Card Capacity** | 1,000,000+ cards |
| **Card Download Speed** | 10,000 cards/second |
| **RS-485 Ports** | 2 |
| **OSDP Readers per Port** | Up to 8 |
| **OS** | Linux-based |

### Communication Protocols

- **OSDP** - Open Supervised Device Protocol (SIA OSDP v2.2)
- **Wiegand** - Legacy reader support
- **DESFire** - Contactless smart card
- **TLS 1.3** - Network encryption
- **OSDP Secure Channel** - AES-128 encrypted serial communication

---

## SDK Architecture

### SDK Library: `libaspsdkcore.so`

The Azure Access SDK is a proprietary, multi-lingual SDK available in:
- C/C++
- C#
- Java
- Python

### Required Files

```
lib/linux/arm/libaspsdkcore.so.1.0.*   # ARM library
lib/linux/x86/libaspsdkcore.so.1.0.*   # x86 library
aspsdkcore.config                       # SDK configuration
certs/                                  # TLS certificates
aspsdk.lic                              # License file
```

### Logical Point Address (LPA)

The LPA is a 4-byte identifier for objects within a cluster:

**Format 1 (Node Specific):**
| Field | Range | Description |
|-------|-------|-------------|
| Node | 0-32 | Node within cluster (0 = this node) |
| LDA | 0-255 | Logical Device Address |
| Instance | 0-255 | Instance of device type |

**Format 2 (Cluster Wide):**
| Field | Value | Description |
|-------|-------|-------------|
| Node | 0xFF | NODEID_CLUSTER_WIDE |
| Id | 0-65535 | Object Id |

### Pre-defined LDA Addresses (BLU-IC2)

| LDA | Connection |
|-----|------------|
| 0 | Base Board / Logical Device |
| 1 | Device Block 1 |
| 2 | Device Block 2 |

---

## Core Types and Constants

### Include File: `sdk_types.h`

```c
// Constants
#define NODEID_CLUSTER_WIDE     0xFF
#define SHA1_THUMBPRINT_SIZE    20
```

### LPA Types

```c
typedef enum {
    LPAType_SerialPort,     // Serial port
    LPAType_Relay,          // Relay/output
    LPAType_Input,          // Input point
    LPAType_Reader,         // Card reader
    LPAType_AccessPoint,    // Access point (door)
    // ... additional types
} LPAType_t;
```

### Pre-defined Input Addresses

| LPA | Description |
|-----|-------------|
| `LPAType_Input.<node>.0.0` | TMP (Tamper input) |
| `LPAType_Input.<node>.0.1` | Power Fail input |
| `LPAType_Input.<node>.0.3` | SSH Enabled input |
| `LPAType_Input.<node>.0.4` | Factory reset input |
| `LPAType_Input.<node>.0.5` | RTC Battery Fault input |
| `LPAType_Input.<node>.<1>.0` | Device Tamper |
| `LPAType_Input.<node>.<1>.1` | Device Power Fail |
| `LPAType_Input.<node>.<1>.2` | IN1 (IC-4) / RDR1 DC |
| `LPAType_Input.<node>.<1>.3` | IN2 (IC-4) / RDR1 EPB |

---

## Card Management

### Include File: `Card.h`

### Card Structure

```c
struct Card_t {
    uint32_t CardId;     // Card Id
    Vector_t* Fields;    // Card fields
};
```

### Card Database Configuration

```c
struct CardDatabaseConfig_t {
    uint8_t PermissionCount;        // Number of Access Levels per card
    uint16_t PermissionEntryCount;  // Permission entries per card
    uint16_t ExclusionEntryCount;   // Exclusion entries per card
    Vector_t* FieldIdList;          // Field list
};
```

**WARNING:** Reconfiguring the card database erases all existing cardholder data.

### Card Functions

```c
// Create/Destroy
Card_t_Create();
Card_t_Destroy();

// Conversion
Card_t_ToCommand();
Command_ToCard_t();

// Dynamic Fields
bool CardCommand_GetUpdateDynField(CardCommand* apCmd, uint8_t aFieldId);
void CardCommand_SetUpdateDynField(CardCommand* apCmd, uint8_t aFieldId, bool aUpdate);
```

### Card Flags

```c
typedef enum {
    CardFlags_UseLongTimes = 0x00000001  // Use long Strike/Held open times
} CardFlags_t;
```

### Permission Flags

```c
typedef enum {
    PermissionFlags_HostGrant          = 0x0001,  // Host grant
    PermissionFlags_HostDeny           = 0x0002,  // Host deny
    PermissionFlags_SoftAPB            = 0x0004,  // Soft APB
    PermissionFlags_APBExempt          = 0x0008,  // APB exempt
    PermissionFlags_EnterClosedArea    = 0x0010,  // Enter closed area
    PermissionFlags_Visitor            = 0x0020,  // Is visitor
    PermissionFlags_Escort             = 0x0040,  // Is escort
    PermissionFlags_RestrictedEscort   = 0x0080,  // Restricted escort
    PermissionFlags_UnlockReader       = 0x0100,  // Can unlock reader
    PermissionFlags_PinCommandAuthority = 0x0200, // PIN+10/PIN+20 events
    PermissionFlags_EscortAPBExempt    = 0x0400,  // Escort APB exempt
    PermissionFlags_Deny               = 0x0800,  // Deny by timezone
    PermissionFlags_InvertTZ           = 0x1000   // Invert timezone
} PermissionFlags_t;
```

---

## Event System

### Include File: `EventSubscription.h`, `EventBufferDefinition.h`

### Event Buffer Constants

```c
typedef enum {
    EventBufferConsts_MinSize         = 1000,    // Minimum events
    EventBufferConsts_DefaultCacheSize = 10000,  // Default cache
    EventBufferConsts_DefaultSize     = 100000,  // Default buffer
    EventBufferConsts_MaxSize         = 500000   // Maximum buffer
} EventBufferConsts_t;
```

### Event Buffer Definition

```c
struct EventBufferDefinition_t {
    uint32_t EventsNumber;   // Max events to store (default: 100,000)
    uint32_t CacheSize;      // Memory cache before flash write (default: 10,000)
    uint32_t FlushTimeout;   // Seconds before cache flush (0 = on capacity)
};
```

**WARNING:** Flushing events too frequently will wear out flash storage.

### Event Subscription

```c
typedef enum {
    EventSubscriptionFlags_StartFromLastAck = 0x80  // Continue from last ack
} EventSubscriptionFlags_t;

struct EventSubscription_t {
    uint8_t Flags;                    // See EventSubscriptionFlags_t
    uint8_t MaxEventsBeforeAck;       // Events before requiring ack
    uint8_t SrcNode;                  // Source node (use sdk_GetHostId)
    uint32_t StartEventSerialNumber;  // Starting serial number
};
```

---

## Access Control Events

### Access Grant Event

**Include:** `AccGrantEvent.h`

```c
typedef enum {
    AccEventFlags_AreaOffline = 0x01,  // Area offline
    AccEventFlags_APB         = 0x02,  // Anti passback violation
    AccEventFlags_EntryMade   = 0x04,  // Entry was made
    AccEventFlags_HostReq     = 0x08,  // Host access request
    AccEventFlags_Escort      = 0x10,  // Access by escort
    AccEventFlags_Visitor     = 0x20,  // Access by visitor
    AccEventFlags_HostGrant   = 0x40,  // Host granted access
    AccEventFlags_Duress      = 0x80   // Request under duress
} AccEventFlags_t;

typedef enum {
    AccEventFlags2_ReaderUnlocked = 0x01,  // Reader in unlocked mode
    AccEventFlags2_ReaderLocked   = 0x02,  // Reader in locked mode
    AccEventFlags2_EntryAssumed   = 0x04,  // Entry was assumed
    AccEventFlags2_IsOffline      = 0x08   // Is offline
} AccEventFlags2_t;

struct AccGrantEvent_t {
    uint32_t SerialNumber;     // Event serial number
    uint32_t EventDateTime;    // Event UTC timestamp
    uint8_t Node;              // Source node Id
    uint8_t Type;              // EventType_AccGrant
    uint8_t SubType;           // See etAccGrant_t
    LPA_t Dest;                // Reserved
    LPA_t Source;              // Reader LPA
    uint32_t Card;             // Card Id
    uint8_t Flags2;            // See AccEventFlags2_t
    uint8_t Flags;             // See AccEventFlags_t
    uint8_t Strike;            // Strike number used
    uint8_t FormatId;          // Card format Id
    int32_t TransactionId;     // Transaction Id for matching
    Vector_t* FieldList;       // Card fields
};
```

### Access Deny Event

**Include:** `AccDenyEvent.h`

```c
struct AccDenyEvent_t {
    uint32_t SerialNumber;     // Event serial number
    uint32_t EventDateTime;    // Event UTC timestamp
    uint8_t Node;              // Source node Id
    uint8_t Type;              // EventType_AccDeny
    uint8_t SubType;           // See etAccDeny_t
    LPA_t Dest;                // Reserved
    LPA_t Source;              // Reader LPA
    uint32_t Card;             // Card Id
    uint8_t DenyCount;         // Consecutive denial count
    uint8_t Flags;             // See AccEventFlags_t
    uint8_t Flags2;            // See AccEventFlags2_t
    uint8_t FieldId;           // Affecting field Id
    int32_t TransactionId;     // Transaction Id
    uint8_t FormatId;          // Card format Id
    CardField_t Field;         // Influencing field
    Vector_t* FieldList;       // Card fields
};
```

### Access Point Event

**Include:** `AccessPointEvent.h`

```c
typedef enum {
    AccessPointEventFlags_EntryMade = 0x04  // Entry was made
} AccessPointEventFlags_t;

struct AccessPointEvent_t {
    uint32_t SerialNumber;
    uint32_t EventDateTime;
    uint8_t Node;
    uint8_t Type;               // EventType_AccPoint
    uint8_t SubType;            // See etAccPoint_t
    LPA_t Dest;                 // Reserved
    LPA_t Source;               // AccessPoint LPA
    LPA_t Initiator;            // Who initiated (c_lpaNULL = Host)
    uint8_t Flags;              // See AccessPointEventFlags_t
    AccessPointState_t NewState;
    uint8_t Strike;             // Strike number used
    AccessPointState_t OldState;
    AccessPointMode_t NewMode;
    AccessPointMode_t OldMode;
    RelayControlOperation_t NewRelayState;
    RelayControlOperation_t OldRelayState;
    KCMFTA_t NewHeldOpen;
    KCMFTA_t OldHeldOpen;
    KCMFTA_t NewForceOpen;
    KCMFTA_t OldForceOpen;
    KCMFTA_t OldDoorContactState;
    KCMFTA_t NewDoorContactState;
    KCMFTA_t OldEPBState;
    KCMFTA_t NewEPBState;
};
```

---

## OSDP Protocol

### Command Types

**Include:** `CmdType.h`

```c
typedef enum {
    CmdType_Protocol    = 0,   // Protocol commands
    CmdType_Hardware    = 1,   // Hardware configuration
    CmdType_Access      = 2,   // Access configuration
    CmdType_Alarm       = 3,   // Alarm configuration
    CmdType_TimeZone    = 4,   // Time zone configuration
    CmdType_Permission  = 5,   // Permission configuration
    CmdType_Card        = 6,   // Card configuration
    CmdType_Event       = 7,   // Event buffer configuration
    CmdType_Misc        = 8,   // Misc configuration
    CmdType_Script      = 9,   // Script configuration
    CmdType_Virtual     = 10,  // Virtual/SDK-only commands
    CmdType_InternalVariables = 11  // Internal variables
} CmdType_t;
```

### Protocol Commands

```c
typedef enum {
    ctProtocol_WhoAreYou        = 1,
    ctProtocol_IAmWhoAreYou     = 2,
    ctProtocol_IAm              = 3,
    ctProtocol_ConnectionStatus = 4
    // ...
} ctProtocol_t;
```

### Device Model IDs

```c
typedef enum {
    DeviceModelId_Unknown = 0,
    DeviceModelId_ASP4    = 1,
    DeviceModelId_ASP2    = 2,
    DeviceModelId_HC1     = 3,
    DeviceModelId_HC2     = 4,
    DeviceModelId_HC4     = 5
} DeviceModelId_t;
```

### Device Info Structure

```c
struct DeviceInfo_t {
    char NodeName[CoreConsts_MaxNodeName];
    char AppVersion[CoreConsts_MaxNodeName];
    char ImageVersion[CoreConsts_MaxNodeName];
    uint32_t Version;          // App version number
    uint32_t APIVersion;       // Script API version
    uint32_t DBVersion;        // Database version
    uint8_t PICReaderVersion;  // PIC firmware revision
    char MAC0[CoreConsts_MaxNodeName];  // 1st interface MAC
    char MAC1[CoreConsts_MaxNodeName];  // 2nd interface MAC
    uint32_t CardCount;        // Current card count
    uint32_t MaxReaderCount;   // Max reader count
    uint32_t MaxCardCount;     // Max card count
    DeviceModelId_t ModelId;   // Device model
    uint8_t NodeNumber;        // Assigned node number
    uint32_t ActiveCardCount;
    uint32_t EstimatedCardCount;
    uint64_t RAMAvailable;     // Available RAM (bytes)
    uint64_t FlashFree;        // Free flash (bytes)
    char BuildVersion[CoreConsts_MaxNodeName];
    char BuildTimestamp[CoreConsts_MaxNodeName];
};
```

---

## Error Codes

**Include:** `ErrorCode.h`

```c
typedef enum {
    // Success
    ErrorCode_OK                    = 0,   // Delivered and executed
    ErrorCode_Queued                = 1,   // Queued for later

    // Protocol Errors
    ErrorCode_ProtocolVersion       = 2,   // Unsupported protocol version
    ErrorCode_Unauthorized          = 3,   // No WRU sequence or permissions
    ErrorCode_AlreadyConnected      = 4,   // Already connected
    ErrorCode_TooManyConnections    = 5,   // Max connections reached

    // Node Errors
    ErrorCode_NodeUnknown           = 10,  // Node not defined
    ErrorCode_NodeOffline           = 11,  // Node declared offline
    ErrorCode_UnknownCommand        = 12,  // Unknown command

    // Execution Errors
    ErrorCode_CantExecute           = 13,  // Can't execute (check logs)
    ErrorCode_Script                = 20,  // Script error
    ErrorCode_BadParams             = 21,  // Bad parameters
    ErrorCode_ObjectNotfound        = 22,  // Object not found
    ErrorCode_NotEnoughMemory       = 23,  // Out of memory
    ErrorCode_Database              = 24,  // Database error
    ErrorCode_CommunicationError    = 25,  // Communication error
    ErrorCode_UnknownException      = 26,  // Unknown exception

    // System Errors
    ErrorCode_NotStarted            = 27,  // Service not started
    ErrorCode_CreateDriver          = 28,  // Can't create driver
    ErrorCode_ExecuteTimeout        = 29,  // Command timeout
    ErrorCode_License               = 30,  // License error
    ErrorCode_BadCommandType        = 31,  // Bad command type
    ErrorCode_BufferOverflow        = 32,  // Buffer overflow

    // Certificate Errors
    ErrorCode_CertificateChainFile  = 33,  // Public key not found
    ErrorCode_PrivateKeyFile        = 34,  // Private key not found
    ErrorCode_VerifyPath            = 35,  // CA folder not found

    // Connection Errors
    ErrorCode_KeepaliveTime         = 36,  // Keepalive time not set
    ErrorCode_KeepaliveInterval     = 37,  // Keepalive interval not set

    // License Limits
    ErrorCode_LicenseReaderCount    = 38,  // Reader count exceeded
    ErrorCode_LicenseCardCount      = 39,  // Card count exceeded
    ErrorCode_LicenseAccessPointCount = 40,// Access point count exceeded

    // Async
    ErrorCode_Pending               = 41   // Operation not finished
} ErrorCode_t;
```

---

## LibOSDP Integration

### Overview

For OSDP reader communication, HAL integrates with the open-source **libosdp** library:
- GitHub: https://github.com/goToMain/libosdp
- Documentation: https://doc.osdp.dev/
- License: Apache-2.0

### Key Features

- **AES-128 Secure Channel** - Encrypted reader communication
- **Zero runtime allocation** - All memory at init time
- **Non-blocking, async design** - 50ms refresh requirement
- **Language bindings** - C/C++, Python, Rust

### Key Concepts

#### SCBK (Secure Channel Base Key)
- 128-bit pre-shared key unique per peripheral device
- Must be securely provisioned and stored
- Passed via `osdp_pd_info_t::scbk`

#### Session Keys (Derived)
- **S-ENC** - Session encryption key
- **S-MAC1** - CP-to-PD MAC key
- **S-MAC2** - PD-to-CP MAC key

#### Secure Channel Handshake

1. CP sends `CMD_CHLNG` (challenge)
2. PD responds with `REPLY_CCRYPT` (client cryptogram)
3. CP sends `CMD_SCRYPT` (server cryptogram)
4. PD returns `REPLY_RMAC_I` (initial MAC)
5. **Secure channel established**

### HAL OSDP Implementation

The HAL includes a complete OSDP implementation:

**Files:**
- `src/hal_core/osdp_reader.c` - Reader communication
- `src/hal_core/osdp_secure_channel.c` - AES-128 encryption
- `include/osdp_types.h` - Protocol types

**Features:**
- Complete OSDP v2.2 compliance
- AES-128 CBC encryption with MAC
- Serial RS-485 communication
- LED and buzzer control
- Event queue for card reads
- Tamper detection

### OSDP API Example

```c
// Configure reader
OSDP_Config_t config = {
    .address = 0,
    .baud_rate = 9600,
    .secure_channel = true,
    .scbk = { /* 16-byte key */ },
    .poll_interval_ms = 100,
    .retry_count = 3,
    .timeout_ms = 200
};

// Initialize
OSDP_Reader_t* reader = OSDP_Reader_Create(&config, "/dev/ttyS0");

// Establish secure channel
OSDP_Reader_EstablishSecureChannel(reader);

// Control LED
OSDP_Reader_SetLED(reader, 0, OSDP_LED_COLOR_GREEN);

// Process events
while (running) {
    OSDP_Reader_Poll(reader);

    OSDP_Card_Data_t card;
    if (OSDP_Reader_GetCardRead(reader, &card) == ErrorCode_OK) {
        // Process card read
    }
}
```

---

## Sources

- Azure Access Technology Wiki: https://wiki.azure-access.com/en/sdk/
- Azure Access Website: https://azure-access.com/
- LibOSDP Documentation: https://doc.osdp.dev/
- SIA OSDP Specification: https://www.securityindustry.org/industry-standards/open-supervised-device-protocol/

---

*Compiled from Azure Access Technology SDK documentation and research*
*HAL Azure Panel Project - March 2026*
