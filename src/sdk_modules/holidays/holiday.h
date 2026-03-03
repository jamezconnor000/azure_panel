#ifndef SDK_HOLIDAY_H
#define SDK_HOLIDAY_H

#include "../common/sdk_types.h"
#include <stdint.h>
#include <time.h>

/*
 * Azure Access Technology SDK - Holiday Module
 * Based on HolidayDate.h, DeleteHoliday.h, HolidayClear.h documentation
 */

// =============================================================================
// Holiday Type Constants
// =============================================================================

// Holiday types are stored as a 32-bit field, supporting up to 32 different
// holiday types. Bit 0 = Type 1, Bit 31 = Type 32.
typedef enum {
    HolidayType_1  = 0x00000001,
    HolidayType_2  = 0x00000002,
    HolidayType_3  = 0x00000004,
    HolidayType_4  = 0x00000008,
    HolidayType_5  = 0x00000010,
    HolidayType_6  = 0x00000020,
    HolidayType_7  = 0x00000040,
    HolidayType_8  = 0x00000080,
    HolidayType_9  = 0x00000100,
    HolidayType_10 = 0x00000200,
    HolidayType_11 = 0x00000400,
    HolidayType_12 = 0x00000800,
    HolidayType_13 = 0x00001000,
    HolidayType_14 = 0x00002000,
    HolidayType_15 = 0x00004000,
    HolidayType_16 = 0x00008000,
    HolidayType_17 = 0x00010000,
    HolidayType_18 = 0x00020000,
    HolidayType_19 = 0x00040000,
    HolidayType_20 = 0x00080000,
    HolidayType_21 = 0x00100000,
    HolidayType_22 = 0x00200000,
    HolidayType_23 = 0x00400000,
    HolidayType_24 = 0x00800000,
    HolidayType_25 = 0x01000000,
    HolidayType_26 = 0x02000000,
    HolidayType_27 = 0x04000000,
    HolidayType_28 = 0x08000000,
    HolidayType_29 = 0x10000000,
    HolidayType_30 = 0x20000000,
    HolidayType_31 = 0x40000000,
    HolidayType_32 = 0x80000000,
    HolidayType_All = 0xFFFFFFFF
} HolidayType_t;

// =============================================================================
// Holiday Date Structure
// =============================================================================

/**
 * HolidayDate - Defines a holiday on a specific date
 *
 * Date format: YYYYMMDD (e.g., 20251225 for December 25, 2025)
 * HolidayTypes: Bit field indicating which holiday types apply
 */
typedef struct {
    uint32_t Date;          // Date in YYYYMMDD format
    uint32_t HolidayTypes;  // Bit field of holiday types (32 types max)
} HolidayDate_t;

// HolidayDate Standard Functions
HolidayDate_t* HolidayDate_Create(uint32_t date, uint32_t holiday_types);
void HolidayDate_Destroy(HolidayDate_t* holiday);

// =============================================================================
// Holiday Management Functions
// =============================================================================

/**
 * Add or update a holiday for a specific date
 *
 * If the date already exists, the holiday types are OR'd together.
 * This allows multiple holiday types on the same date.
 */
ErrorCode_t Holiday_Add(uint32_t date, uint32_t holiday_types);

/**
 * Update a holiday for a specific date
 *
 * Replaces the holiday types for the given date (does not OR).
 */
ErrorCode_t Holiday_Update(uint32_t date, uint32_t holiday_types);

/**
 * Delete specific holiday types from a date
 *
 * Removes only the specified holiday types from the date.
 * If all types are removed, the date entry is deleted.
 */
ErrorCode_t Holiday_DeleteTypes(uint32_t date, uint32_t holiday_types_to_remove);

/**
 * Delete all holidays for a specific date
 */
ErrorCode_t Holiday_Delete(uint32_t date);

/**
 * Clear all holidays from the system
 */
ErrorCode_t Holiday_Clear(void);

/**
 * Get holiday types for a specific date
 *
 * Returns the holiday types bit field, or 0 if not a holiday.
 */
uint32_t Holiday_GetTypes(uint32_t date);

/**
 * Get holiday types for the current date
 *
 * Convenience function that uses current time.
 */
uint32_t Holiday_GetTypesToday(void);

/**
 * Check if a specific date is a holiday of any type
 *
 * Returns 1 if holiday, 0 if not.
 */
int Holiday_IsHoliday(uint32_t date);

/**
 * Check if a specific date matches given holiday types
 *
 * Returns 1 if the date has at least one of the specified holiday types.
 */
int Holiday_MatchesTypes(uint32_t date, uint32_t holiday_types);

/**
 * Get all holidays in a date range
 *
 * Returns a Vector_t* containing HolidayDate_t* entries.
 * Caller must free the vector and entries.
 */
Vector_t* Holiday_GetRange(uint32_t start_date, uint32_t end_date);

/**
 * Count total holidays in the system
 */
int Holiday_Count(void);

// =============================================================================
// Utility Functions
// =============================================================================

/**
 * Convert Unix timestamp to YYYYMMDD format
 */
uint32_t Holiday_DateFromTime(time_t timestamp);

/**
 * Convert YYYYMMDD format to Unix timestamp (midnight local time)
 */
time_t Holiday_TimeFromDate(uint32_t date);

/**
 * Parse date string (YYYY-MM-DD) to YYYYMMDD format
 */
uint32_t Holiday_ParseDate(const char* date_string);

/**
 * Format YYYYMMDD date to string (YYYY-MM-DD)
 */
char* Holiday_FormatDate(uint32_t date);

/**
 * Validate date format (basic sanity check)
 *
 * Returns 1 if valid, 0 if invalid.
 */
int Holiday_IsValidDate(uint32_t date);

#endif // SDK_HOLIDAY_H
