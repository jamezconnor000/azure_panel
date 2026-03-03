#ifndef HAL_TYPES_H
#define HAL_TYPES_H
#include <stdint.h>
#include <stdbool.h>
#include <time.h>

typedef uint8_t LPAType_t;
#define LPAType_Reader 2
#define LPAType_AccessPoint 3
#define LPAType_Area 4
#define LPAType_Relay 6
#define LPAType_Card 210

typedef struct { LPAType_t type; uint16_t id; uint8_t node_id; } LPA_t;

typedef enum { AccessDecision_Grant=0, AccessDecision_Deny=1, AccessDecision_Error=2 } AccessDecision_t;
typedef enum { DenyReason_CardNotFound=0, DenyReason_NoPermission=1, DenyReason_TimeRestriction=2, DenyReason_CardBlocked=3 } DenyReason_t;

typedef uint32_t CardId_t;
typedef uint32_t FacilityCode_t;

typedef struct {
    CardId_t card_id;
    FacilityCode_t facility_code;
    uint32_t card_number;
    uint8_t card_format_id;
    time_t activation_time;
    time_t deactivation_time;
    uint16_t use_limit;
    uint8_t is_blocked;
} Card_t;

typedef enum { EventType_AccessGrant=0, EventType_AccessDeny=1, EventType_AccPoint=3, EventType_Input=4, EventType_Reader=5, EventType_Relay=6 } EventType_t;

typedef struct {
    uint32_t serial_number;
    time_t event_time;
    uint8_t node_id;
    EventType_t event_type;
    uint8_t event_subtype;
    LPA_t destination;
    LPA_t source;
} EventHeader_t;

typedef struct { EventHeader_t header; CardId_t card_id; uint8_t card_format_id; FacilityCode_t facility_code; } AccessGrantEvent_t;
typedef struct { EventHeader_t header; CardId_t card_id; DenyReason_t reason; uint8_t card_format_id; FacilityCode_t facility_code; } AccessDenyEvent_t;

// Generic HAL event structure (for internal event buffer)
typedef struct {
    EventHeader_t header;
    uint32_t serial_number;
    CardId_t card_id;
    uint8_t card_format_id;
    FacilityCode_t facility_code;
    DenyReason_t deny_reason;
    uint8_t data[64];          // Generic data payload
} HAL_Event_t;

typedef enum { KCMFTA_Unknown=0, KCMFTA_Alarm=1, KCMFTA_Tamper=2, KCMFTA_Fault=4, KCMFTA_Masked=8 } KCMFTA_t;
typedef enum {
    ErrorCode_OK=0,
    ErrorCode_NodeOffline=11,
    ErrorCode_BadParams=21,
    ErrorCode_ObjectNotFound=22,
    ErrorCode_OutOfMemory=23,
    ErrorCode_Database=24,
    ErrorCode_Failed=25,
    ErrorCode_AlreadyExists=26,
    ErrorCode_CryptoError=27,
    ErrorCode_NotEnabled=28,
    ErrorCode_InvalidState=29,
    ErrorCode_AuthFailed=30
} ErrorCode_t;

typedef struct { uint32_t event_buffer_size; uint32_t max_events_before_ack; uint32_t connection_timeout_ms; uint8_t log_level; } HAL_RuntimeConfig_t;
typedef struct { uint8_t max_events_before_ack; uint8_t src_node; uint32_t start_event_serial_number; } EventSubscription_t;
typedef struct { uint32_t ack_serial_number; uint8_t dst_node; uint8_t src_node; } EventAck_t;
typedef struct {
    uint32_t total_events;
    uint32_t buffer_size;
    uint32_t last_ack_serial;
    uint32_t last_event_serial;
    uint8_t connection_status;
    uint32_t total_capacity;
    uint32_t events_pending;
    uint32_t events_available;
} EventBufferStatus_t;
typedef struct { AccessDecision_t decision; DenyReason_t deny_reason; uint32_t strike_time_ms; uint32_t relay_id; } AccessResult_t;

#endif
