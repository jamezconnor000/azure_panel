#include "relay.h"
#include "../timezones/timezone.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

// Simple in-memory storage for relays
// In production, this would be backed by SQLite database
#define MAX_RELAYS 256
#define MAX_RELAY_LINKS 100

static Relay_t* g_relays[MAX_RELAYS];
static int g_relay_count = 0;

static RelayLink_t* g_relay_links[MAX_RELAY_LINKS];
static int g_relay_link_count = 0;

// Legacy simple relay states for backward compatibility
static bool relay_states[8] = {false};

// =============================================================================
// Relay Structure Functions
// =============================================================================

Relay_t* Relay_Create(LPA_t id) {
    Relay_t* relay = (Relay_t*)malloc(sizeof(Relay_t));
    if (relay) {
        memset(relay, 0, sizeof(Relay_t));
        relay->Id = id;
        relay->PulseDuration = 100;  // 1 second default (100 * 10ms)
        relay->CtrlTimeZone = 0;     // No timezone control
        relay->Flags = RelayFlags_None;
        relay->Mode = RelayMode_Off;  // Use sdk_types.h enum
        relay->ScriptId = 0;
        relay->CurrentState = RelayState_Off;  // RelayState_Off = 1 from sdk_types.h
        relay->LastStateChange = time(NULL);
    }
    return relay;
}

void Relay_Destroy(Relay_t* relay) {
    if (relay) {
        free(relay);
    }
}

// =============================================================================
// RelayLink Structure Functions
// =============================================================================

RelayLink_t* RelayLink_Create(LPA_t id) {
    RelayLink_t* link = (RelayLink_t*)malloc(sizeof(RelayLink_t));
    if (link) {
        link->Id = id;
        link->LinkList = Vector_Create(10);
    }
    return link;
}

void RelayLink_Destroy(RelayLink_t* link) {
    if (!link) return;

    if (link->LinkList) {
        for (int i = 0; i < link->LinkList->count; i++) {
            RelayLinkRecord_t* record = (RelayLinkRecord_t*)link->LinkList->data[i];
            free(record);
        }
        Vector_Destroy(link->LinkList);
    }

    free(link);
}

void RelayLink_AddRecord(RelayLink_t* link, RelayLinkRecord_t* record) {
    if (link && link->LinkList && record) {
        Vector_Add(link->LinkList, record);
    }
}

void RelayLink_ClearRecords(RelayLink_t* link) {
    if (link && link->LinkList) {
        for (int i = 0; i < link->LinkList->count; i++) {
            RelayLinkRecord_t* record = (RelayLinkRecord_t*)link->LinkList->data[i];
            free(record);
        }
        Vector_Clear(link->LinkList);
    }
}

// =============================================================================
// RelayStatus Structure Functions
// =============================================================================

RelayStatus_t* RelayStatus_Create(LPA_t id) {
    RelayStatus_t* status = (RelayStatus_t*)malloc(sizeof(RelayStatus_t));
    if (status) {
        status->Id = id;
        status->State = RelayState_Unknown;
        status->LastChange = time(NULL);
        status->IsOnline = 1;
    }
    return status;
}

void RelayStatus_Destroy(RelayStatus_t* status) {
    if (status) {
        free(status);
    }
}

// =============================================================================
// Internal Helper Functions
// =============================================================================

static int FindRelayIndex(LPA_t id) {
    for (int i = 0; i < g_relay_count; i++) {
        if (g_relays[i] && LPA_Equals(&g_relays[i]->Id, &id)) {
            return i;
        }
    }
    return -1;
}

static int FindRelayLinkIndex(LPA_t id) {
    for (int i = 0; i < g_relay_link_count; i++) {
        if (g_relay_links[i] && LPA_Equals(&g_relay_links[i]->Id, &id)) {
            return i;
        }
    }
    return -1;
}

// =============================================================================
// Relay Management Functions
// =============================================================================

void Relay_Init(void) {
    g_relay_count = 0;
    g_relay_link_count = 0;
    memset(g_relays, 0, sizeof(g_relays));
    memset(g_relay_links, 0, sizeof(g_relay_links));

    // Initialize legacy relay states
    for(int i = 0; i < 8; i++) {
        relay_states[i] = false;
    }

    printf("Relay system initialized (SDK enhanced)\n");
}

ErrorCode_t Relay_Add(Relay_t* relay) {
    if (!relay) return ErrorCode_BadParams;
    if (g_relay_count >= MAX_RELAYS) return ErrorCode_OutOfMemory;

    // Check if already exists
    if (FindRelayIndex(relay->Id) >= 0) {
        return ErrorCode_AlreadyExists;
    }

    g_relays[g_relay_count++] = relay;
    return ErrorCode_OK;
}

Relay_t* Relay_Get(LPA_t id) {
    int index = FindRelayIndex(id);
    if (index >= 0) {
        return g_relays[index];
    }
    return NULL;
}

ErrorCode_t Relay_Update(Relay_t* relay) {
    if (!relay) return ErrorCode_BadParams;

    int index = FindRelayIndex(relay->Id);
    if (index < 0) return ErrorCode_ObjectNotFound;

    // Keep current state
    RelayState_t current_state = g_relays[index]->CurrentState;
    time_t last_change = g_relays[index]->LastStateChange;

    // Replace relay
    Relay_Destroy(g_relays[index]);
    g_relays[index] = relay;

    // Restore state
    relay->CurrentState = current_state;
    relay->LastStateChange = last_change;

    return ErrorCode_OK;
}

ErrorCode_t Relay_Delete(LPA_t id) {
    int index = FindRelayIndex(id);
    if (index < 0) return ErrorCode_ObjectNotFound;

    Relay_Destroy(g_relays[index]);

    // Shift remaining relays
    for (int i = index; i < g_relay_count - 1; i++) {
        g_relays[i] = g_relays[i + 1];
    }
    g_relay_count--;

    return ErrorCode_OK;
}

// =============================================================================
// Relay Control Functions
// =============================================================================

bool Relay_TurnOn(LPA_t id) {
    Relay_t* relay = Relay_Get(id);
    if (!relay) return false;

    relay->CurrentState = RelayState_On;
    relay->LastStateChange = time(NULL);

    printf("RELAY [%d:%d]: ON\n", id.type, id.id);
    return true;
}

bool Relay_TurnOff(LPA_t id) {
    Relay_t* relay = Relay_Get(id);
    if (!relay) return false;

    relay->CurrentState = RelayState_Off;
    relay->LastStateChange = time(NULL);

    printf("RELAY [%d:%d]: OFF\n", id.type, id.id);
    return true;
}

bool Relay_Pulse(LPA_t id) {
    Relay_t* relay = Relay_Get(id);
    if (!relay) return false;

    uint32_t duration_ms = relay->PulseDuration * 10;  // Convert 10ms units to ms

    relay->CurrentState = RelayState_On;
    relay->LastStateChange = time(NULL);

    printf("RELAY [%d:%d]: PULSE for %dms\n", id.type, id.id, duration_ms);

    // Note: In real implementation, would schedule automatic OFF
    return true;
}

bool Relay_PulseWithDuration(LPA_t id, uint32_t duration_units) {
    Relay_t* relay = Relay_Get(id);
    if (!relay) return false;

    uint32_t duration_ms = duration_units * 10;

    relay->CurrentState = RelayState_On;
    relay->LastStateChange = time(NULL);

    printf("RELAY [%d:%d]: PULSE for %dms\n", id.type, id.id, duration_ms);
    return true;
}

bool Relay_Unlock(uint8_t relay_id, uint32_t duration_ms) {
    // Legacy function for backward compatibility
    if(relay_id >= 8) return false;

    relay_states[relay_id] = true;
    printf("RELAY %d: UNLOCKED for %dms\n", relay_id, duration_ms);

    // Also update in SDK relay system
    LPA_t id = {.type = 0, .id = relay_id, .node_id = 0};
    return Relay_PulseWithDuration(id, duration_ms / 10);
}

bool Relay_Lock(uint8_t relay_id) {
    // Legacy function for backward compatibility
    if(relay_id >= 8) return false;

    relay_states[relay_id] = false;
    printf("RELAY %d: LOCKED\n", relay_id);

    // Also update in SDK relay system
    LPA_t id = {.type = 0, .id = relay_id, .node_id = 0};
    return Relay_TurnOff(id);
}

ErrorCode_t Relay_ExecuteControl(LPA_t id, RelayControlOperation_t operation) {
    Relay_t* relay = Relay_Get(id);
    if (!relay) return ErrorCode_ObjectNotFound;

    switch (operation) {
        case RelayControlOperation_OFF:
            return Relay_TurnOff(id) ? ErrorCode_OK : ErrorCode_Failed;

        case RelayControlOperation_ON:
            return Relay_TurnOn(id) ? ErrorCode_OK : ErrorCode_Failed;

        case RelayControlOperation_PULSE:
            return Relay_Pulse(id) ? ErrorCode_OK : ErrorCode_Failed;

        default:
            return ErrorCode_BadParams;
    }
}

// =============================================================================
// Relay Status Functions
// =============================================================================

RelayStatus_t* Relay_GetStatus(LPA_t id) {
    Relay_t* relay = Relay_Get(id);
    if (!relay) return NULL;

    RelayStatus_t* status = RelayStatus_Create(id);
    if (status) {
        status->State = relay->CurrentState;
        status->LastChange = relay->LastStateChange;
        status->IsOnline = 1;
    }

    return status;
}

RelayState_t Relay_GetState(LPA_t id) {
    Relay_t* relay = Relay_Get(id);
    if (relay) {
        return relay->CurrentState;
    }
    return RelayState_Unknown;
}

int Relay_IsOnline(LPA_t id) {
    Relay_t* relay = Relay_Get(id);
    return relay != NULL ? 1 : 0;
}

// =============================================================================
// Relay Automation Functions
// =============================================================================

ErrorCode_t Relay_AddLink(RelayLink_t* link) {
    if (!link) return ErrorCode_BadParams;
    if (g_relay_link_count >= MAX_RELAY_LINKS) return ErrorCode_OutOfMemory;

    // Check if already exists
    if (FindRelayLinkIndex(link->Id) >= 0) {
        return ErrorCode_AlreadyExists;
    }

    g_relay_links[g_relay_link_count++] = link;
    return ErrorCode_OK;
}

RelayLink_t* Relay_GetLink(LPA_t id) {
    int index = FindRelayLinkIndex(id);
    if (index >= 0) {
        return g_relay_links[index];
    }
    return NULL;
}

ErrorCode_t Relay_DeleteLink(LPA_t id) {
    int index = FindRelayLinkIndex(id);
    if (index < 0) return ErrorCode_ObjectNotFound;

    RelayLink_Destroy(g_relay_links[index]);

    // Shift remaining links
    for (int i = index; i < g_relay_link_count - 1; i++) {
        g_relay_links[i] = g_relay_links[i + 1];
    }
    g_relay_link_count--;

    return ErrorCode_OK;
}

void Relay_ProcessEvent(LPA_t source, uint16_t event_type, uint16_t event_subtype, uint8_t status) {
    // Check all relay links for matching events
    for (int i = 0; i < g_relay_link_count; i++) {
        RelayLink_t* link = g_relay_links[i];

        // Check each record in this link
        for (int j = 0; j < link->LinkList->count; j++) {
            RelayLinkRecord_t* record = (RelayLinkRecord_t*)link->LinkList->data[j];

            // Match source, type, subtype, and status
            if (LPA_Equals(&record->Source, &source) &&
                record->Type == event_type &&
                record->SubType == event_subtype &&
                (record->NewStatus == 0xFF || record->NewStatus == status)) {

                // Execute the relay operation
                printf("Relay automation triggered: [%d:%d] -> operation %d\n",
                       link->Id.type, link->Id.id, record->Operation);

                Relay_ExecuteControl(link->Id, record->Operation);
            }
        }
    }
}

// Track previous timezone state for edge detection
static bool g_relay_tz_was_active[MAX_RELAYS] = {false};

void Relay_EvaluateTimezones(void) {
    time_t now = time(NULL);
    uint32_t holiday_types = 0;  // Would come from holiday module

    for (int i = 0; i < g_relay_count; i++) {
        Relay_t* relay = g_relays[i];
        if (!relay || relay->CtrlTimeZone == 0) {
            continue;
        }

        bool tz_active = TimeZone_IsActiveById(relay->CtrlTimeZone, now, holiday_types) != 0;
        bool was_active = g_relay_tz_was_active[i];

        // Detect timezone start (edge: inactive -> active)
        bool tz_just_started = tz_active && !was_active;
        bool tz_just_ended = !tz_active && was_active;

        // Update state for next evaluation
        g_relay_tz_was_active[i] = tz_active;

        // Process relay flags
        if (relay->Flags & RelayFlags_OnWhileTZActive) {
            // Stay on while timezone is active
            if (tz_active && relay->CurrentState != RelayState_On) {
                Relay_ExecuteControl(relay->Id, RelayControlOperation_ON);
            } else if (!tz_active && relay->CurrentState == RelayState_On) {
                Relay_ExecuteControl(relay->Id, RelayControlOperation_OFF);
            }
        }

        if (relay->Flags & RelayFlags_PulseAtTZStart) {
            // Pulse when timezone becomes active
            if (tz_just_started) {
                Relay_ExecuteControl(relay->Id, RelayControlOperation_PULSE);
            }
        }

        if (relay->Flags & RelayFlags_PulseAtTZEnd) {
            // Pulse when timezone becomes inactive
            if (tz_just_ended) {
                Relay_ExecuteControl(relay->Id, RelayControlOperation_PULSE);
            }
        }

        // RelayFlags_Latching, RelayFlags_FailSecure, RelayFlags_FailSafe are handled elsewhere
    }
}
