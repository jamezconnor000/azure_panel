#ifndef SDK_TYPES_H
#define SDK_TYPES_H

#include "../../../include/hal_types.h"
#include <stdint.h>
#include <time.h>

/*
 * Azure Access Technology SDK - Common Types
 * Based on wiki documentation at wiki.azure-access.com
 * Auto-generated from PDF documentation - October 30, 2025
 */

// =============================================================================
// Use types from hal_types.h (LPA_t, LPAType_t, ErrorCode_t, etc.)
// =============================================================================

#define c_lpaNULL ((LPA_t){.type = 0, .id = 0, .node_id = 0})

// LPA Helper Functions
int LPA_Equals(const LPA_t* a, const LPA_t* b);

// =============================================================================
// Vector Type (Dynamic Array)
// =============================================================================

typedef struct {
    void** data;
    uint32_t count;
    uint32_t capacity;
} Vector_t;

Vector_t* Vector_Create(uint32_t initial_capacity);
void Vector_Destroy(Vector_t* vec);
void Vector_Add(Vector_t* vec, void* item);
void* Vector_Get(Vector_t* vec, uint32_t index);
void Vector_RemoveAt(Vector_t* vec, uint32_t index);
void Vector_Clear(Vector_t* vec);

// =============================================================================
// Time Types
// =============================================================================

typedef uint32_t Time_t;  // Seconds since midnight

// Helper functions
Time_t Time_FromHMS(uint8_t hour, uint8_t minute, uint8_t second);
void Time_ToHMS(Time_t time, uint8_t* hour, uint8_t* minute, uint8_t* second);

// =============================================================================
// Card Types
// =============================================================================

typedef uint32_t CardId_t;
typedef uint32_t FacilityCode_t;

#define CardConsts_MaxFieldSize 64  // Max bytes for raw card data

// =============================================================================
// Event Types - Using definitions from hal_types.h
// =============================================================================

// Event subtypes (SDK-specific)
typedef enum {
    etInput_Alarm = 0,
    etInput_Tamper = 1,
    etInput_Fault = 2,
    etInput_Masked = 3
} etInput_t;

typedef enum {
    etAccPoint_Grant = 0,
    etAccPoint_Deny = 1,
    etAccPoint_DoorForced = 2,
    etAccPoint_DoorHeld = 3
} etAccPoint_t;

typedef enum {
    etConnection_Online = 0,
    etConnection_Offline = 1
} etConnection_t;

// =============================================================================
// Relay State
// =============================================================================

typedef enum {
    RelayState_Unknown = 0,
    RelayState_Off = 1,
    RelayState_On = 2,
    RelayState_Pulsing = 3
} RelayState_t;

// =============================================================================
// Relay Mode
// =============================================================================

typedef enum {
    RelayMode_Off = 0,
    RelayMode_On = 1,
    RelayMode_Auto = 2
} RelayMode_t;

// =============================================================================
// LED Color
// =============================================================================

typedef enum {
    LEDColor_Off = 0,
    LEDColor_Red = 1,
    LEDColor_Green = 2,
    LEDColor_Amber = 3,
    LEDColor_Blue = 4
} LEDColor_t;

// =============================================================================
// Core Constants
// =============================================================================

#define CoreConsts_MaxStrikesArray 16  // Max strikes per reader

// =============================================================================
// Utility Macros
// =============================================================================

#define LPA_Equal(a, b) ((a).type == (b).type && (a).id == (b).id && (a).node_id == (b).node_id)
#define LPA_IsNull(a) ((a).type == 0 && (a).id == 0 && (a).node_id == 0)

#endif // SDK_TYPES_H
