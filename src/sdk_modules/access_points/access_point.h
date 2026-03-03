#ifndef ACCESS_POINT_H
#define ACCESS_POINT_H

#include "../../../include/hal_types.h"
#include <stdint.h>
#include <stdbool.h>

/**
 * Access Point Module
 *
 * Manages access points (doors, gates, etc.) with areas and strike configurations.
 * Links readers to physical access control points.
 */

// Access Point Modes
typedef enum {
    AccessPointMode_Locked = 0,
    AccessPointMode_Unlocked = 1,
    AccessPointMode_CardOnly = 2,
    AccessPointMode_PINOnly = 3,
    AccessPointMode_CardAndPIN = 4,
    AccessPointMode_CardOrPIN = 5,
    AccessPointMode_FacilityCode = 6,
    AccessPointMode_DisabledLocked = 7,
    AccessPointMode_DisabledUnlocked = 8
} AccessPointMode_t;

// Strike definition
typedef struct {
    LPA_t strike_lpa;           // Strike relay LPA
    uint16_t pulse_duration;    // 10ms units
} Strike_t;

// Access Point structure
typedef struct {
    uint32_t id;                        // Access Point ID
    LPA_t lpa;                          // Access Point LPA
    AccessPointMode_t init_mode;        // Initial mode

    // Strike timings (seconds)
    uint16_t short_strike_time;
    uint16_t long_strike_time;
    uint16_t short_held_open_time;
    uint16_t long_held_open_time;

    // Areas for APB
    LPA_t area_a;
    LPA_t area_b;

    // Strike list
    Strike_t strikes[8];                // Max 8 strikes per access point
    uint8_t strike_count;

    // Associated reader
    LPA_t reader_lpa;

} AccessPoint_t;

// =============================================================================
// Access Point Functions
// =============================================================================

/**
 * Create a new access point
 */
AccessPoint_t* AccessPoint_Create(uint32_t id);

/**
 * Destroy access point
 */
void AccessPoint_Destroy(AccessPoint_t* access_point);

/**
 * Add a strike to access point
 */
ErrorCode_t AccessPoint_AddStrike(AccessPoint_t* access_point, LPA_t strike_lpa, uint16_t pulse_duration);

/**
 * Set access point mode
 */
ErrorCode_t AccessPoint_SetMode(AccessPoint_t* access_point, AccessPointMode_t mode);

/**
 * Set areas for APB
 */
ErrorCode_t AccessPoint_SetAreas(AccessPoint_t* access_point, LPA_t area_a, LPA_t area_b);

#endif // ACCESS_POINT_H
