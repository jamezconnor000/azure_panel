#include "timezone.h"
#include <stdlib.h>
#include <string.h>

// =============================================================================
// TimeZone Registry - In-memory storage
// =============================================================================

#define MAX_TIMEZONES 256

static TimeZone_t* g_timezones[MAX_TIMEZONES];
static int g_timezone_count = 0;

/*
 * TimeInterval Implementation
 */

TimeInterval_t* TimeInterval_t_Create(void) {
    TimeInterval_t* interval = (TimeInterval_t*)calloc(1, sizeof(TimeInterval_t));
    if (!interval) return NULL;
    
    interval->Recurrence = RecurrenceType_Cyclic;
    return interval;
}

void TimeInterval_t_Destroy(TimeInterval_t* interval) {
    if (interval) {
        free(interval);
    }
}

/*
 * TimeZone Implementation
 */

TimeZone_t* TimeZone_Create(uint16_t id) {
    TimeZone_t* tz = (TimeZone_t*)malloc(sizeof(TimeZone_t));
    if (!tz) return NULL;
    
    tz->Id = id;
    tz->ScriptId = 0;
    tz->TimeIntervalList = Vector_Create(10);
    
    if (!tz->TimeIntervalList) {
        free(tz);
        return NULL;
    }
    
    return tz;
}

void TimeZone_Destroy(TimeZone_t* tz) {
    if (!tz) return;
    
    if (tz->TimeIntervalList) {
        // Free all intervals
        for (uint32_t i = 0; i < tz->TimeIntervalList->count; i++) {
            TimeInterval_t* interval = (TimeInterval_t*)Vector_Get(tz->TimeIntervalList, i);
            TimeInterval_t_Destroy(interval);
        }
        Vector_Destroy(tz->TimeIntervalList);
    }
    
    free(tz);
}

void TimeZone_AddInterval(TimeZone_t* tz, TimeInterval_t* interval) {
    if (tz && tz->TimeIntervalList && interval) {
        Vector_Add(tz->TimeIntervalList, interval);
    }
}

void TimeZone_ClearIntervals(TimeZone_t* tz) {
    if (tz && tz->TimeIntervalList) {
        // Free all intervals
        for (uint32_t i = 0; i < tz->TimeIntervalList->count; i++) {
            TimeInterval_t* interval = (TimeInterval_t*)Vector_Get(tz->TimeIntervalList, i);
            TimeInterval_t_Destroy(interval);
        }
        Vector_Clear(tz->TimeIntervalList);
    }
}

/*
 * TimeZoneStatus Implementation
 */

TimeZoneStatus_t* TimeZoneStatus_Create(LPA_t id, uint8_t status) {
    TimeZoneStatus_t* tzs = (TimeZoneStatus_t*)malloc(sizeof(TimeZoneStatus_t));
    if (!tzs) return NULL;
    
    tzs->Id = id;
    tzs->Status = status;
    
    return tzs;
}

void TimeZoneStatus_Destroy(TimeZoneStatus_t* status) {
    if (status) {
        free(status);
    }
}

/*
 * Time Zone Evaluation - Core Algorithm
 */

int TimeZone_IsActive(TimeZone_t* tz, time_t current_time, uint32_t holiday_types) {
    if (!tz || !tz->TimeIntervalList) {
        return 0;
    }
    
    // Special time zones
    if (tz->Id == TimeZoneConsts_Never) {
        return 0;
    }
    if (tz->Id == TimeZoneConsts_Always) {
        return 1;
    }
    
    // Evaluate each interval - if ANY interval matches, TZ is active
    for (uint32_t i = 0; i < tz->TimeIntervalList->count; i++) {
        TimeInterval_t* interval = (TimeInterval_t*)Vector_Get(tz->TimeIntervalList, i);
        
        if (TimeInterval_Matches(interval, current_time, holiday_types)) {
            return 1;  // Found active interval!
        }
    }
    
    return 0;  // No intervals matched
}

int TimeInterval_Matches(TimeInterval_t* interval, time_t current_time, uint32_t holiday_types) {
    if (!interval) return 0;
    
    // Step 1: Check validity window (BeginDateTime/EndDateTime)
    if (!TimeInterval_WithinValidityWindow(interval, current_time)) {
        return 0;
    }
    
    // Step 2: Check CycleCount limit
    if (interval->BeginDateTime > 0 && interval->CycleCount > 0) {
        time_t elapsed = current_time - interval->BeginDateTime;
        uint32_t cycles_completed = elapsed / (interval->CycleLength * 86400);
        
        if (cycles_completed >= interval->CycleCount) {
            return 0;  // Exceeded cycle count
        }
    }
    
    // Step 3: Evaluate recurrence pattern
    int recurrence_match = 0;
    switch (interval->Recurrence) {
        case RecurrenceType_Cyclic:
            recurrence_match = TimeInterval_EvaluateCyclic(interval, current_time);
            break;
        case RecurrenceType_Monthly:
            recurrence_match = TimeInterval_EvaluateMonthly(interval, current_time);
            break;
        case RecurrenceType_Annually:
            recurrence_match = TimeInterval_EvaluateAnnually(interval, current_time);
            break;
        case RecurrenceType_MonthlyAtDay:
            recurrence_match = TimeInterval_EvaluateMonthlyAtDay(interval, current_time);
            break;
    }
    
    if (!recurrence_match) {
        return 0;
    }
    
    // Step 4: Check daily time window (StartTime to EndTime)
    if (!TimeInterval_WithinDailyWindow(interval, current_time)) {
        return 0;
    }
    
    // Step 5: Check holiday types (if specified)
    if (interval->HolidayTypes != 0) {
        // Interval requires specific holiday types
        if ((interval->HolidayTypes & holiday_types) == 0) {
            return 0;  // No matching holiday type
        }
    }
    
    // All checks passed!
    return 1;
}

int TimeInterval_WithinDailyWindow(TimeInterval_t* interval, time_t current_time) {
    if (!interval) return 0;
    
    // Get current time of day (seconds since midnight)
    struct tm* tm_info = localtime(&current_time);
    Time_t current_tod = Time_FromHMS(tm_info->tm_hour, tm_info->tm_min, tm_info->tm_sec);
    
    Time_t start = interval->StartTime;
    Time_t end = interval->EndTime;
    
    // Handle wrap-around (e.g., 23:00 to 02:00)
    if (start <= end) {
        // Normal case: 08:00 to 17:00
        return (current_tod >= start && current_tod <= end);
    } else {
        // Wrap-around case: 23:00 to 02:00
        return (current_tod >= start || current_tod <= end);
    }
}

int TimeInterval_WithinValidityWindow(TimeInterval_t* interval, time_t current_time) {
    if (!interval) return 0;
    
    // If BeginDateTime is set, check lower bound
    if (interval->BeginDateTime > 0) {
        if (current_time < interval->BeginDateTime) {
            return 0;
        }
    }
    
    // If EndDateTime is set, check upper bound
    if (interval->EndDateTime > 0) {
        if (current_time > interval->EndDateTime) {
            return 0;
        }
    }
    
    return 1;
}

int TimeInterval_EvaluateCyclic(TimeInterval_t* interval, time_t current_time) {
    if (!interval || interval->CycleLength == 0) {
        return 0;
    }
    
    // Calculate which day in the cycle we're on
    time_t reference = interval->CycleStart > 0 ? interval->CycleStart : 
                       (interval->BeginDateTime > 0 ? interval->BeginDateTime : 0);
    
    if (reference == 0) {
        // No reference date - can't evaluate
        return 0;
    }
    
    // Days since cycle start
    time_t elapsed_seconds = current_time - reference;
    uint32_t elapsed_days = elapsed_seconds / 86400;
    
    // Which day in the cycle (0-based)
    uint32_t cycle_day = elapsed_days % interval->CycleLength;
    
    // Check if this day is active (bit field)
    uint32_t day_mask = 1U << cycle_day;
    
    return (interval->CycleDays & day_mask) != 0;
}

int TimeInterval_EvaluateMonthly(TimeInterval_t* interval, time_t current_time) {
    if (!interval) return 0;
    
    struct tm* tm_info = localtime(&current_time);
    uint32_t day_of_month = tm_info->tm_mday;  // 1-31
    
    // Check if this day of month is in CycleDays bit field
    if (day_of_month > 0 && day_of_month <= 31) {
        uint32_t day_mask = 1U << (day_of_month - 1);
        return (interval->CycleDays & day_mask) != 0;
    }
    
    return 0;
}

int TimeInterval_EvaluateAnnually(TimeInterval_t* interval, time_t current_time) {
    if (!interval) return 0;
    
    struct tm* tm_info = localtime(&current_time);
    
    // Get month and day from BeginDateTime for comparison
    if (interval->BeginDateTime > 0) {
        time_t begin = interval->BeginDateTime;
        struct tm* begin_tm = localtime(&begin);
        
        // Check if current month and day match
        if (tm_info->tm_mon == begin_tm->tm_mon && 
            tm_info->tm_mday == begin_tm->tm_mday) {
            return 1;
        }
    }
    
    return 0;
}

int TimeInterval_EvaluateMonthlyAtDay(TimeInterval_t* interval, time_t current_time) {
    if (!interval) return 0;
    
    struct tm* tm_info = localtime(&current_time);
    
    // Get day of week (0=Sunday, 6=Saturday)
    uint32_t weekday = tm_info->tm_wday;
    
    // Check if this weekday is in CycleDays bit field
    uint32_t weekday_mask = 1U << weekday;
    
    if ((interval->CycleDays & weekday_mask) == 0) {
        return 0;  // This weekday not enabled
    }
    
    // Calculate which occurrence of this weekday (1st, 2nd, 3rd, 4th, 5th)
    uint32_t day_of_month = tm_info->tm_mday;
    uint32_t occurrence = ((day_of_month - 1) / 7) + 1;  // 1-5
    
    // CycleLength specifies which occurrence(s) to match
    // For example: CycleLength = 1 means "1st Monday of month"
    if (interval->CycleLength > 0 && interval->CycleLength <= 5) {
        return (occurrence == interval->CycleLength);
    }
    
    return 1;  // No specific occurrence requirement
}

// =============================================================================
// TimeZone Registry Functions
// =============================================================================

ErrorCode_t TimeZone_Register(TimeZone_t* tz) {
    if (!tz) {
        return ErrorCode_BadParams;
    }

    // Check if already registered
    for (int i = 0; i < g_timezone_count; i++) {
        if (g_timezones[i] && g_timezones[i]->Id == tz->Id) {
            // Replace existing
            TimeZone_Destroy(g_timezones[i]);
            g_timezones[i] = tz;
            return ErrorCode_OK;
        }
    }

    if (g_timezone_count >= MAX_TIMEZONES) {
        return ErrorCode_OutOfMemory;
    }

    g_timezones[g_timezone_count++] = tz;
    return ErrorCode_OK;
}

TimeZone_t* TimeZone_GetById(uint16_t id) {
    // Handle special constants
    if (id == TimeZoneConsts_Null || id == TimeZoneConsts_Never || id == TimeZoneConsts_Always) {
        // Return a static timezone for these constants
        static TimeZone_t tz_never = { .Id = TimeZoneConsts_Never };
        static TimeZone_t tz_always = { .Id = TimeZoneConsts_Always };

        if (id == TimeZoneConsts_Never) return &tz_never;
        if (id == TimeZoneConsts_Always) return &tz_always;
        return NULL;
    }

    for (int i = 0; i < g_timezone_count; i++) {
        if (g_timezones[i] && g_timezones[i]->Id == id) {
            return g_timezones[i];
        }
    }

    return NULL;
}

int TimeZone_IsActiveById(uint16_t tz_id, time_t current_time, uint32_t holiday_types) {
    // Handle special cases
    if (tz_id == TimeZoneConsts_Null || tz_id == 0) {
        return 0;  // Null timezone is never active
    }
    if (tz_id == TimeZoneConsts_Never) {
        return 0;  // Never active
    }
    if (tz_id == TimeZoneConsts_Always) {
        return 1;  // Always active
    }

    TimeZone_t* tz = TimeZone_GetById(tz_id);
    if (!tz) {
        return 0;  // Unknown timezone
    }

    return TimeZone_IsActive(tz, current_time, holiday_types);
}

void TimeZone_UnregisterAll(void) {
    for (int i = 0; i < g_timezone_count; i++) {
        if (g_timezones[i]) {
            TimeZone_Destroy(g_timezones[i]);
            g_timezones[i] = NULL;
        }
    }
    g_timezone_count = 0;
}

int TimeZone_GetCount(void) {
    return g_timezone_count;
}
