/**
 * @file event_types.h
 * @brief Event type definitions for Aether Access PoC
 *
 * Defines the core event structures used for IPC communication
 * between the HAL Engine and Ambient.ai Forwarder.
 *
 * @author FAM-HAL-v1.0-001
 * @date February 10, 2026
 */

#ifndef POC_EVENT_TYPES_H
#define POC_EVENT_TYPES_H

#include <stdint.h>
#include <stdbool.h>
#include <string.h>
#include <time.h>

#ifdef __cplusplus
extern "C" {
#endif

/* ============================================================================
 * Constants
 * ========================================================================== */

#define UUID_STRING_LEN         37      /* 36 chars + null terminator */
#define DEVICE_NAME_MAX_LEN     64
#define DEVICE_TYPE_MAX_LEN     16
#define ALARM_NAME_MAX_LEN      64
#define ACCESS_ITEM_KEY_MAX_LEN 32
#define EVENT_VERSION           1

/* ============================================================================
 * Event Types
 * ========================================================================== */

/**
 * @brief Event type enumeration
 */
typedef enum {
    EVENT_TYPE_UNKNOWN = 0,
    EVENT_TYPE_ACCESS_GRANTED,
    EVENT_TYPE_ACCESS_DENIED,
    EVENT_TYPE_DOOR_FORCED_OPEN,
    EVENT_TYPE_DOOR_HELD_OPEN,
    EVENT_TYPE_INPUT_ACTIVE,
    EVENT_TYPE_INPUT_INACTIVE,
    EVENT_TYPE_RELAY_ACTIVATED,
    EVENT_TYPE_RELAY_DEACTIVATED,
    EVENT_TYPE_SYSTEM_ERROR,
    EVENT_TYPE_MAX
} event_type_t;

/* Compatibility aliases for event types */
#define EVENT_UNKNOWN           EVENT_TYPE_UNKNOWN
#define EVENT_ACCESS_GRANTED    EVENT_TYPE_ACCESS_GRANTED
#define EVENT_ACCESS_DENIED     EVENT_TYPE_ACCESS_DENIED
#define EVENT_DOOR_FORCED       EVENT_TYPE_DOOR_FORCED_OPEN
#define EVENT_DOOR_HELD_OPEN    EVENT_TYPE_DOOR_HELD_OPEN
#define EVENT_TAMPER            EVENT_TYPE_SYSTEM_ERROR
#define EVENT_HEARTBEAT         EVENT_TYPE_MAX

/**
 * @brief Access decision result codes
 */
typedef enum {
    ACCESS_RESULT_UNKNOWN = 0,
    ACCESS_RESULT_GRANTED,          /* Valid card with permission */
    ACCESS_RESULT_DENIED_NO_CARD,   /* Card not in database */
    ACCESS_RESULT_DENIED_EXPIRED,   /* Card expired */
    ACCESS_RESULT_DENIED_TIMEZONE,  /* Outside valid timezone */
    ACCESS_RESULT_DENIED_DISABLED,  /* Card disabled */
    ACCESS_RESULT_DENIED_APB,       /* Anti-passback violation */
    ACCESS_RESULT_MAX
} access_result_t;

/* Compatibility aliases for access results */
#define ACCESS_GRANTED              ACCESS_RESULT_GRANTED
#define ACCESS_DENIED_UNKNOWN       ACCESS_RESULT_DENIED_NO_CARD
#define ACCESS_DENIED_EXPIRED       ACCESS_RESULT_DENIED_EXPIRED
#define ACCESS_DENIED_SUSPENDED     ACCESS_RESULT_DENIED_DISABLED
#define ACCESS_DENIED_TIME          ACCESS_RESULT_DENIED_TIMEZONE
#define ACCESS_DENIED_ZONE          ACCESS_RESULT_DENIED_APB

/**
 * @brief Device type enumeration
 */
typedef enum {
    DEVICE_TYPE_UNKNOWN = 0,
    DEVICE_TYPE_READER,
    DEVICE_TYPE_INPUT,
    DEVICE_TYPE_RELAY,
    DEVICE_TYPE_DOOR,
    DEVICE_TYPE_PANEL,
    DEVICE_TYPE_MAX
} device_type_enum_t;

/* ============================================================================
 * Core Event Structure
 * ========================================================================== */

/**
 * @brief HAL event structure for IPC and Ambient.ai forwarding
 *
 * This structure contains all fields required by the Ambient.ai
 * Generic Cloud Event Ingestion API.
 */
typedef struct {
    /* Event identification */
    char event_uid[UUID_STRING_LEN];            /* Unique event ID (UUID) */
    event_type_t event_type;                     /* Event type enum */
    int version;                                 /* Message version */

    /* Device information */
    char device_uid[UUID_STRING_LEN];           /* Device UUID */
    char device_name[DEVICE_NAME_MAX_LEN];      /* Human-readable name */
    char device_type[DEVICE_TYPE_MAX_LEN];      /* "Reader", "Door", etc. */

    /* Alarm information */
    char alarm_uid[UUID_STRING_LEN];            /* Alarm type UUID */
    char alarm_name[ALARM_NAME_MAX_LEN];        /* "Access Granted", etc. */

    /* Timestamps (Unix epoch seconds) */
    int64_t occurred_timestamp;                  /* When event happened */
    int64_t published_timestamp;                 /* When event was sent */

    /* Access-specific fields */
    char person_uid[UUID_STRING_LEN];           /* Optional cardholder UUID */
    char access_item_key[ACCESS_ITEM_KEY_MAX_LEN]; /* Card number as string */
    access_result_t access_result;              /* Access decision result */

    /* Wiegand-specific data */
    uint32_t facility_code;                     /* Wiegand facility code */
    uint32_t card_number;                       /* Wiegand card number */

    /* Metadata */
    bool has_person;                            /* True if person_uid is set */
    uint32_t reader_port;                       /* Physical reader port (1-2) */
} hal_event_t;

/* ============================================================================
 * Card Information Structure
 * ========================================================================== */

/**
 * @brief Card/cardholder information from database
 */
typedef struct {
    int64_t id;                                 /* Database row ID */
    uint32_t card_number;                       /* Card number */
    uint32_t facility_code;                     /* Facility code */
    char card_uid[UUID_STRING_LEN];             /* Card UUID */
    char person_uid[UUID_STRING_LEN];           /* Cardholder UUID */
    char first_name[64];                        /* First name */
    char last_name[64];                         /* Last name */
    bool enabled;                               /* Card enabled flag */
    int64_t valid_from;                         /* Valid from timestamp */
    int64_t valid_until;                        /* Valid until timestamp */
    int32_t permission_group;                   /* Permission group ID */
} card_info_t;

/* ============================================================================
 * Device Registry Entry
 * ========================================================================== */

/**
 * @brief Device registry entry for UUID mapping
 */
typedef struct {
    char device_uid[UUID_STRING_LEN];           /* Device UUID */
    char device_name[DEVICE_NAME_MAX_LEN];      /* Device name */
    device_type_enum_t device_type;             /* Device type */
    int port;                                   /* Physical port number */
    bool enabled;                               /* Device enabled flag */
} device_entry_t;

/* ============================================================================
 * Alarm Definition
 * ========================================================================== */

/**
 * @brief Alarm type definition for Ambient.ai mapping
 */
typedef struct {
    char alarm_uid[UUID_STRING_LEN];            /* Alarm type UUID */
    char alarm_name[ALARM_NAME_MAX_LEN];        /* Alarm name */
    event_type_t event_type;                    /* Corresponding event type */
} alarm_definition_t;

/* ============================================================================
 * IPC Message Types
 * ========================================================================== */

/**
 * @brief IPC message type enumeration
 */
typedef enum {
    IPC_MSG_TYPE_UNKNOWN = 0,
    IPC_MSG_TYPE_EVENT,             /* Event notification */
    IPC_MSG_TYPE_ACK,               /* Acknowledgment */
    IPC_MSG_TYPE_HEARTBEAT,         /* Keepalive */
    IPC_MSG_TYPE_SUBSCRIBE,         /* Subscribe to events */
    IPC_MSG_TYPE_UNSUBSCRIBE,       /* Unsubscribe */
    IPC_MSG_TYPE_STATUS,            /* Status query/response */
    IPC_MSG_TYPE_MAX
} ipc_msg_type_t;

/* ============================================================================
 * Utility Functions (Inline)
 * ========================================================================== */

/**
 * @brief Get human-readable event type name
 */
static inline const char* event_type_to_string(event_type_t type) {
    switch (type) {
        case EVENT_TYPE_ACCESS_GRANTED:     return "Access Granted";
        case EVENT_TYPE_ACCESS_DENIED:      return "Access Denied";
        case EVENT_TYPE_DOOR_FORCED_OPEN:   return "Door Forced Open";
        case EVENT_TYPE_DOOR_HELD_OPEN:     return "Door Held Open";
        case EVENT_TYPE_INPUT_ACTIVE:       return "Input Active";
        case EVENT_TYPE_INPUT_INACTIVE:     return "Input Inactive";
        case EVENT_TYPE_RELAY_ACTIVATED:    return "Relay Activated";
        case EVENT_TYPE_RELAY_DEACTIVATED:  return "Relay Deactivated";
        case EVENT_TYPE_SYSTEM_ERROR:       return "System Error";
        default:                            return "Unknown";
    }
}

/**
 * @brief Get human-readable access result name
 */
static inline const char* access_result_to_string(access_result_t result) {
    switch (result) {
        case ACCESS_RESULT_GRANTED:         return "Granted";
        case ACCESS_RESULT_DENIED_NO_CARD:  return "Denied - Unknown Card";
        case ACCESS_RESULT_DENIED_EXPIRED:  return "Denied - Card Expired";
        case ACCESS_RESULT_DENIED_TIMEZONE: return "Denied - Invalid Timezone";
        case ACCESS_RESULT_DENIED_DISABLED: return "Denied - Card Disabled";
        case ACCESS_RESULT_DENIED_APB:      return "Denied - APB Violation";
        default:                            return "Unknown";
    }
}

/**
 * @brief Get device type string for Ambient.ai
 */
static inline const char* device_type_to_string(device_type_enum_t type) {
    switch (type) {
        case DEVICE_TYPE_READER:    return "Reader";
        case DEVICE_TYPE_INPUT:     return "Input";
        case DEVICE_TYPE_RELAY:     return "Relay";
        case DEVICE_TYPE_DOOR:      return "Door";
        case DEVICE_TYPE_PANEL:     return "Panel";
        default:                    return "Unknown";
    }
}

/**
 * @brief Initialize event structure with defaults
 */
static inline void event_init(hal_event_t* event) {
    if (event) {
        memset(event, 0, sizeof(hal_event_t));
        event->version = EVENT_VERSION;
        event->event_type = EVENT_TYPE_UNKNOWN;
        event->access_result = ACCESS_RESULT_UNKNOWN;
        event->has_person = false;
    }
}

#ifdef __cplusplus
}
#endif

#endif /* POC_EVENT_TYPES_H */
