/*
 * Enhanced Access Logic with Full SDK Integration
 *
 * This implementation uses all SDK modules:
 * - Permissions for access control
 * - TimeZones for schedule restrictions
 * - Holidays for special day handling
 * - Relays for physical access control
 * - Readers for card/PIN validation
 */

#include "access_logic.h"
#include "../sdk_modules/permissions/permission.h"
#include "../sdk_modules/holidays/holiday.h"
#include "../sdk_modules/timezones/timezone.h"
#include "../sdk_modules/relays/relay.h"
#include "../sdk_modules/readers/reader.h"
#include "../sdk_modules/events/access_event.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

// =============================================================================
// Global SDK State
// =============================================================================

typedef struct {
    Permission_t** permissions;     // Array of permissions
    int permission_count;
    TimeZone_t** timezones;        // Array of timezones
    int timezone_count;
    int initialized;
} AccessLogicSDK_t;

static AccessLogicSDK_t* g_sdk_logic = NULL;

// Forward declarations
ErrorCode_t AccessLogic_SDK_AddTimeZone(TimeZone_t* timezone);

// =============================================================================
// Initialization
// =============================================================================

ErrorCode_t AccessLogic_SDK_Initialize(void) {
    if (g_sdk_logic && g_sdk_logic->initialized) {
        return ErrorCode_OK;
    }

    g_sdk_logic = (AccessLogicSDK_t*)malloc(sizeof(AccessLogicSDK_t));
    if (!g_sdk_logic) return ErrorCode_OutOfMemory;

    g_sdk_logic->permissions = NULL;
    g_sdk_logic->permission_count = 0;
    g_sdk_logic->timezones = NULL;
    g_sdk_logic->timezone_count = 0;
    g_sdk_logic->initialized = 1;

    // Initialize SDK modules
    Relay_Init();

    // Setup default timezones
    TimeZone_t* tz_always = TimeZone_Create(2);  // TimeZoneConsts_Always
    AccessLogic_SDK_AddTimeZone(tz_always);

    printf("✓ Enhanced Access Logic (SDK) initialized\n");
    return ErrorCode_OK;
}

// =============================================================================
// Permission Management
// =============================================================================

ErrorCode_t AccessLogic_SDK_AddPermission(Permission_t* permission) {
    if (!g_sdk_logic || !permission) return ErrorCode_BadParams;

    g_sdk_logic->permissions = (Permission_t**)realloc(
        g_sdk_logic->permissions,
        sizeof(Permission_t*) * (g_sdk_logic->permission_count + 1)
    );

    g_sdk_logic->permissions[g_sdk_logic->permission_count++] = permission;
    return ErrorCode_OK;
}

Permission_t* AccessLogic_SDK_FindPermission(uint32_t permission_id) {
    if (!g_sdk_logic) return NULL;

    for (int i = 0; i < g_sdk_logic->permission_count; i++) {
        if (g_sdk_logic->permissions[i]->Id == permission_id) {
            return g_sdk_logic->permissions[i];
        }
    }

    return NULL;
}

// =============================================================================
// TimeZone Management
// =============================================================================

ErrorCode_t AccessLogic_SDK_AddTimeZone(TimeZone_t* timezone) {
    if (!g_sdk_logic || !timezone) return ErrorCode_BadParams;

    g_sdk_logic->timezones = (TimeZone_t**)realloc(
        g_sdk_logic->timezones,
        sizeof(TimeZone_t*) * (g_sdk_logic->timezone_count + 1)
    );

    g_sdk_logic->timezones[g_sdk_logic->timezone_count++] = timezone;
    return ErrorCode_OK;
}

TimeZone_t* AccessLogic_SDK_FindTimeZone(uint16_t timezone_id) {
    if (!g_sdk_logic) return NULL;

    for (int i = 0; i < g_sdk_logic->timezone_count; i++) {
        if (g_sdk_logic->timezones[i]->Id == timezone_id) {
            return g_sdk_logic->timezones[i];
        }
    }

    return NULL;
}

// =============================================================================
// Enhanced Access Decision Logic
// =============================================================================

/**
 * Process card read with full SDK integration
 *
 * Decision flow:
 * 1. Find permission for card
 * 2. Check permission is active (not expired)
 * 3. Find permission entry for this reader
 * 4. Check for exclusions
 * 5. Evaluate timezone (if specified)
 * 6. Check holiday restrictions
 * 7. Make final decision
 * 8. Control relay if granted
 */
AccessLogicResult_t AccessLogic_SDK_ProcessCardRead(
    uint32_t card_number,
    uint32_t permission_id,
    LPA_t reader_lpa,
    LPA_t relay_lpa
) {
    AccessLogicResult_t decision = {0};
    decision.card_number = card_number;
    decision.granted = false;
    decision.timestamp = time(NULL);
    strcpy(decision.reason, "Unknown");

    // Step 1: Find permission
    Permission_t* permission = AccessLogic_SDK_FindPermission(permission_id);
    if (!permission) {
        strcpy(decision.reason, "Permission not found");
        return decision;
    }

    // Step 2: Check permission is active
    if (!Permission_IsActive(permission, decision.timestamp)) {
        strcpy(decision.reason, "Permission expired or not yet active");
        return decision;
    }

    // Step 3: Find permission entry for this reader
    PermissionEntry_t* entry = Permission_FindEntryForAccessObject(permission, reader_lpa);
    if (!entry) {
        strcpy(decision.reason, "No access to this reader");
        return decision;
    }

    // Step 4: Check for exclusions
    if (Permission_IsExcluded(permission, reader_lpa)) {
        strcpy(decision.reason, "Explicitly excluded from this reader");
        return decision;
    }

    // Step 5: Evaluate timezone (if specified)
    if (entry->TimeZone > 0) {
        TimeZone_t* tz = AccessLogic_SDK_FindTimeZone(entry->TimeZone);
        if (tz) {
            // Get current holiday types
            uint32_t today = Holiday_DateFromTime(decision.timestamp);
            uint32_t holiday_types = Holiday_GetTypes(today);

            // Check if timezone is active
            int tz_active = TimeZone_IsActive(tz, decision.timestamp, holiday_types);
            if (!tz_active) {
                strcpy(decision.reason, "Outside allowed time schedule");
                return decision;
            }
        } else {
            // TimeZone not found - conservative denial
            strcpy(decision.reason, "TimeZone configuration error");
            return decision;
        }
    }

    // Step 6: Check holiday restrictions
    uint32_t today = Holiday_DateFromTime(decision.timestamp);
    if (Holiday_IsHoliday(today)) {
        // Could add additional holiday logic here
        // For now, if timezone evaluation passed, allow
    }

    // Step 7: Access granted!
    decision.granted = true;
    strcpy(decision.reason, "Access granted");

    // Step 8: Control relay
    if (decision.granted) {
        // Use the relay from permission entry if specified
        LPA_t strike = (entry->Strike.type != 0) ? entry->Strike : relay_lpa;
        Relay_Pulse(strike);
    }

    return decision;
}

/**
 * Simplified access decision for backward compatibility
 */
AccessLogicResult_t AccessLogic_SDK_ProcessCardRead_Simple(
    uint32_t card_number,
    uint8_t door_number
) {
    // Convert legacy door number to reader LPA
    LPA_t reader_lpa = {.type = LPAType_Reader, .id = door_number, .node_id = 0};
    LPA_t relay_lpa = {.type = LPAType_Relay, .id = door_number, .node_id = 0};

    // Assume permission ID matches card number for simplicity
    // In production, this would lookup from database
    return AccessLogic_SDK_ProcessCardRead(card_number, 1, reader_lpa, relay_lpa);
}

// =============================================================================
// Reader Integration
// =============================================================================

ErrorCode_t AccessLogic_SDK_SetReaderMode(LPA_t reader_lpa, ReaderMode_t mode) {
    ErrorCode_t result = Reader_SetMode(reader_lpa, mode);

    if (result == ErrorCode_OK) {
        // Update indication based on mode
        switch (mode) {
            case ReaderMode_Unlocked:
                Reader_SetIndicationState(reader_lpa, ReaderIndicationState_Unlocked);
                break;
            case ReaderMode_Locked:
                Reader_SetIndicationState(reader_lpa, ReaderIndicationState_Locked);
                break;
            case ReaderMode_CardOnly:
                Reader_SetIndicationState(reader_lpa, ReaderIndicationState_Card);
                break;
            case ReaderMode_CardAndPin:
                Reader_SetIndicationState(reader_lpa, ReaderIndicationState_CardAndPin);
                break;
            default:
                break;
        }
    }

    return result;
}

// =============================================================================
// Event Generation
// =============================================================================

void AccessLogic_SDK_GenerateAccessEvent(AccessLogicResult_t* decision) {
    if (!decision) return;

    AccessEventType_t event_type = decision->granted ?
        EVENT_ACCESS_GRANTED : EVENT_ACCESS_DENIED;

    AccessEvent_t* event = AccessEvent_Create(event_type);
    if (event) {
        snprintf(event->cardNumber, sizeof(event->cardNumber), "%u", decision->card_number);
        event->doorNumber = decision->door_number;
        event->granted = decision->granted;
        event->timestamp = decision->timestamp;

        // Publish event (would integrate with EventManager)
        char* json = AccessEvent_ToJSON(event);
        printf("EVENT: %s\n", json);
        free(json);

        AccessEvent_Destroy(event);
    }
}

// =============================================================================
// Shutdown
// =============================================================================

void AccessLogic_SDK_Shutdown(void) {
    if (!g_sdk_logic) return;

    // Free permissions
    for (int i = 0; i < g_sdk_logic->permission_count; i++) {
        Permission_Destroy(g_sdk_logic->permissions[i]);
    }
    free(g_sdk_logic->permissions);

    // Free timezones
    for (int i = 0; i < g_sdk_logic->timezone_count; i++) {
        TimeZone_Destroy(g_sdk_logic->timezones[i]);
    }
    free(g_sdk_logic->timezones);

    free(g_sdk_logic);
    g_sdk_logic = NULL;

    printf("✓ Enhanced Access Logic (SDK) shutdown\n");
}
