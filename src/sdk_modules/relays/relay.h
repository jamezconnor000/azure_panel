#ifndef RELAY_H
#define RELAY_H

#include <stdint.h>
#include <stdbool.h>
#include "../common/sdk_types.h"

/*
 * Azure Access Technology SDK - Relay Module
 * Based on Relay.h, RelayControl.h, RelayLink.h, RelayStatus.h documentation
 */

// =============================================================================
// Relay Constants
// =============================================================================

// Note: RelayMode_t is defined in sdk_types.h
// RelayMode_Off = 0, RelayMode_On = 1, RelayMode_Auto = 2

typedef enum {
    RelayFlags_None = 0x0000,
    RelayFlags_OnWhileTZActive = 0x0001,    // Turn on while timezone active
    RelayFlags_PulseAtTZStart = 0x0002,     // Pulse when timezone starts
    RelayFlags_PulseAtTZEnd = 0x0004,       // Pulse when timezone ends
    RelayFlags_Latching = 0x0008,           // Latching relay (stays on)
    RelayFlags_FailSecure = 0x0010,         // Locks on power failure
    RelayFlags_FailSafe = 0x0020            // Unlocks on power failure
} RelayFlags_t;

typedef enum {
    RelayControlOperation_OFF = 0,      // Turn relay off
    RelayControlOperation_ON = 1,       // Turn relay on
    RelayControlOperation_PULSE = 2     // Pulse relay (timed)
} RelayControlOperation_t;

// Note: RelayState_t is defined in sdk_types.h
// RelayState_Unknown = 0, RelayState_Off = 1, RelayState_On = 2, RelayState_Pulsing = 3

// =============================================================================
// Relay Structure
// =============================================================================

/**
 * Relay - Complete relay configuration
 */
typedef struct {
    LPA_t Id;                           // Relay LPA
    uint32_t PulseDuration;             // Pulse duration in 10ms units
    uint16_t CtrlTimeZone;              // TimeZone ID for automatic control
    uint16_t Flags;                     // RelayFlags_t bit field
    uint8_t Mode;                       // RelayMode_t
    uint16_t ScriptId;                  // Custom script ID

    // Runtime state
    RelayState_t CurrentState;
    time_t LastStateChange;
} Relay_t;

// Relay Standard Functions
Relay_t* Relay_Create(LPA_t id);
void Relay_Destroy(Relay_t* relay);

// =============================================================================
// Relay Link Structure
// =============================================================================

/**
 * RelayLinkRecord - Single automation link
 */
typedef struct {
    LPA_t Source;                       // Event source (input, reader, etc.)
    uint16_t Type;                      // Event type
    uint16_t SubType;                   // Event subtype
    uint8_t NewStatus;                  // KCMFTA status filter
    RelayControlOperation_t Operation;  // What to do with relay
} RelayLinkRecord_t;

/**
 * RelayLink - Event-driven relay automation
 */
typedef struct {
    LPA_t Id;                           // RelayLink LPA
    Vector_t* LinkList;                 // List of RelayLinkRecord_t*
} RelayLink_t;

// RelayLink Standard Functions
RelayLink_t* RelayLink_Create(LPA_t id);
void RelayLink_Destroy(RelayLink_t* link);
void RelayLink_AddRecord(RelayLink_t* link, RelayLinkRecord_t* record);
void RelayLink_ClearRecords(RelayLink_t* link);

// =============================================================================
// Relay Status Structure
// =============================================================================

typedef struct {
    LPA_t Id;                           // Relay LPA
    RelayState_t State;                 // Current state
    time_t LastChange;                  // When state last changed
    uint8_t IsOnline;                   // 1 if online, 0 if offline
} RelayStatus_t;

// RelayStatus Standard Functions
RelayStatus_t* RelayStatus_Create(LPA_t id);
void RelayStatus_Destroy(RelayStatus_t* status);

// =============================================================================
// Relay Management Functions
// =============================================================================

/**
 * Initialize relay system
 */
void Relay_Init(void);

/**
 * Add a relay configuration
 */
ErrorCode_t Relay_Add(Relay_t* relay);

/**
 * Get relay configuration by ID
 */
Relay_t* Relay_Get(LPA_t id);

/**
 * Update relay configuration
 */
ErrorCode_t Relay_Update(Relay_t* relay);

/**
 * Delete relay configuration
 */
ErrorCode_t Relay_Delete(LPA_t id);

// =============================================================================
// Relay Control Functions
// =============================================================================

/**
 * Turn relay ON
 */
bool Relay_TurnOn(LPA_t id);

/**
 * Turn relay OFF
 */
bool Relay_TurnOff(LPA_t id);

/**
 * Pulse relay for configured duration
 */
bool Relay_Pulse(LPA_t id);

/**
 * Pulse relay for specific duration (10ms units)
 */
bool Relay_PulseWithDuration(LPA_t id, uint32_t duration_units);

/**
 * Unlock relay (convenience function for door strikes)
 */
bool Relay_Unlock(uint8_t relay_id, uint32_t duration_ms);

/**
 * Lock relay (convenience function)
 */
bool Relay_Lock(uint8_t relay_id);

/**
 * Execute relay control operation
 */
ErrorCode_t Relay_ExecuteControl(LPA_t id, RelayControlOperation_t operation);

// =============================================================================
// Relay Status Functions
// =============================================================================

/**
 * Get current relay status
 */
RelayStatus_t* Relay_GetStatus(LPA_t id);

/**
 * Get state of specific relay
 */
RelayState_t Relay_GetState(LPA_t id);

/**
 * Check if relay is online
 */
int Relay_IsOnline(LPA_t id);

// =============================================================================
// Relay Automation Functions
// =============================================================================

/**
 * Process event for relay automation
 *
 * Checks all RelayLinks and executes matching relay operations
 */
void Relay_ProcessEvent(LPA_t source, uint16_t event_type, uint16_t event_subtype, uint8_t status);

/**
 * Add relay link for automation
 */
ErrorCode_t Relay_AddLink(RelayLink_t* link);

/**
 * Get relay link by ID
 */
RelayLink_t* Relay_GetLink(LPA_t id);

/**
 * Delete relay link
 */
ErrorCode_t Relay_DeleteLink(LPA_t id);

/**
 * Evaluate timezone-controlled relays
 *
 * Should be called periodically to check timezone activation
 */
void Relay_EvaluateTimezones(void);

#endif
