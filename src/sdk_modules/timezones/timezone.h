#ifndef SDK_TIMEZONE_H
#define SDK_TIMEZONE_H

#include "../common/sdk_types.h"

/*
 * Azure Access Technology SDK - Time Zone Module
 * Based on TimeZone.h, TimeZoneConsts.h, TimeZoneStatus.h documentation
 */

// =============================================================================
// Time Zone Constants
// =============================================================================

typedef enum {
    TimeZoneConsts_Null = 0,
    TimeZoneConsts_Never = 1,
    TimeZoneConsts_Always = 2,
    TimeZoneConsts_MaxTZString = 32
} TimeZoneConsts_t;

typedef enum {
    TimeZoneState_Unknown = 0,
    TimeZoneState_Activated = 1,
    TimeZoneState_Deactivated = 2
} TimeZoneState_t;

typedef enum {
    RecurrenceType_Cyclic = 0,          // Legacy TimeInterval logic
    RecurrenceType_Monthly = 1,         // Monthly recurrence
    RecurrenceType_Annually = 2,        // Annual recurrence
    RecurrenceType_MonthlyAtDay = 3     // Monthly at specific day
} RecurrenceType_t;

// =============================================================================
// Time Interval Structure
// =============================================================================

typedef struct {
    Time_t StartTime;                   // Start time (seconds since midnight)
    Time_t EndTime;                     // End time (seconds since midnight)
    uint32_t CycleStart;                // Date cycle begins
    uint8_t CycleLength;                // Days in cycle: 0-32
    uint32_t CycleDays;                 // Bit field: 0x00000001 = Day 1, 0x80000000 = Day 32
    uint32_t HolidayTypes;              // Bit field: 0x00000001 = Type 1, 0x80000000 = Type 32
    uint64_t BeginDateTime;             // Begin date/time (limits applicability)
    uint64_t EndDateTime;               // End date/time (limits applicability)
    uint32_t CycleCount;                // Max completed cycles since BeginDateTime
    RecurrenceType_t Recurrence;        // Recurrence type
} TimeInterval_t;

// TimeInterval Standard Functions
TimeInterval_t* TimeInterval_t_Create(void);
void TimeInterval_t_Destroy(TimeInterval_t* interval);

// =============================================================================
// Time Zone Structure
// =============================================================================

typedef struct {
    uint16_t Id;                        // Time zone ID
    uint16_t ScriptId;                  // Custom logic script ID
    Vector_t* TimeIntervalList;         // List of TimeInterval_t*
} TimeZone_t;

// TimeZone Standard Functions
TimeZone_t* TimeZone_Create(uint16_t id);
void TimeZone_Destroy(TimeZone_t* tz);
void TimeZone_AddInterval(TimeZone_t* tz, TimeInterval_t* interval);
void TimeZone_ClearIntervals(TimeZone_t* tz);

// =============================================================================
// Time Zone Status
// =============================================================================

typedef enum {
    TimeZoneStatusFlags_IsActive = 0x01
} TimeZoneStatusFlags_t;

typedef struct {
    LPA_t Id;                           // TimeZone ID
    uint8_t Status;                     // See TimeZoneStatusFlags_t
} TimeZoneStatus_t;

// TimeZoneStatus Standard Functions
TimeZoneStatus_t* TimeZoneStatus_Create(LPA_t id, uint8_t status);
void TimeZoneStatus_Destroy(TimeZoneStatus_t* status);

// =============================================================================
// Time Zone Evaluation Functions
// =============================================================================

/**
 * Evaluate if a time zone is currently active
 * 
 * @param tz The time zone to evaluate
 * @param current_time Current Unix timestamp
 * @param holiday_types Current holiday types bit field
 * @return 1 if active, 0 if not active
 */
int TimeZone_IsActive(TimeZone_t* tz, time_t current_time, uint32_t holiday_types);

/**
 * Evaluate a specific time interval
 * 
 * @param interval The interval to check
 * @param current_time Current Unix timestamp
 * @param holiday_types Current holiday types bit field
 * @return 1 if interval matches, 0 if not
 */
int TimeInterval_Matches(TimeInterval_t* interval, time_t current_time, uint32_t holiday_types);

/**
 * Check if current time is within daily window (StartTime to EndTime)
 */
int TimeInterval_WithinDailyWindow(TimeInterval_t* interval, time_t current_time);

/**
 * Check if current date is within validity window (BeginDateTime to EndDateTime)
 */
int TimeInterval_WithinValidityWindow(TimeInterval_t* interval, time_t current_time);

/**
 * Evaluate cyclic recurrence pattern
 */
int TimeInterval_EvaluateCyclic(TimeInterval_t* interval, time_t current_time);

/**
 * Evaluate monthly recurrence pattern
 */
int TimeInterval_EvaluateMonthly(TimeInterval_t* interval, time_t current_time);

/**
 * Evaluate annual recurrence pattern
 */
int TimeInterval_EvaluateAnnually(TimeInterval_t* interval, time_t current_time);

/**
 * Evaluate monthly-at-day recurrence pattern
 */
int TimeInterval_EvaluateMonthlyAtDay(TimeInterval_t* interval, time_t current_time);

#endif // SDK_TIMEZONE_H
