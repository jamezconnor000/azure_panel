#ifndef AREA_H
#define AREA_H

#include "../../../include/hal_types.h"
#include <stdint.h>
#include <stdbool.h>

/**
 * Area Module
 *
 * Manages areas for Anti-Passback (APB) and occupancy control.
 * Areas track personnel movement between access points.
 */

// Area structure
typedef struct {
    uint32_t id;                    // Area ID
    LPA_t lpa;                      // Area LPA
    char name[64];                  // Area name (for JSON export)

    // APB Configuration
    uint8_t timed_apb;              // Timed APB in minutes (0 = disabled)

    // Occupancy Control
    uint8_t min_occupancy;          // Minimum occupancy
    uint8_t max_occupancy;          // Maximum occupancy
    uint8_t occupancy_limit;        // Occupancy limit before alarm
    uint8_t min_required_occupancy; // Minimum required occupancy

    // Runtime state
    uint16_t current_occupancy;     // Current occupancy count

} Area_t;

// =============================================================================
// Area Functions
// =============================================================================

/**
 * Create a new area
 */
Area_t* Area_Create(uint32_t id);

/**
 * Destroy area
 */
void Area_Destroy(Area_t* area);

/**
 * Set area name
 */
ErrorCode_t Area_SetName(Area_t* area, const char* name);

/**
 * Set APB configuration
 */
ErrorCode_t Area_SetTimedAPB(Area_t* area, uint8_t minutes);

/**
 * Set occupancy limits
 */
ErrorCode_t Area_SetOccupancyLimits(Area_t* area, uint8_t min, uint8_t max, uint8_t limit, uint8_t min_required);

/**
 * Update occupancy count
 */
ErrorCode_t Area_UpdateOccupancy(Area_t* area, int16_t delta);

#endif // AREA_H
