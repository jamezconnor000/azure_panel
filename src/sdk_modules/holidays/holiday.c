#include "holiday.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

// Simple in-memory storage for holidays
// In production, this would be backed by SQLite database
#define MAX_HOLIDAYS 1000

typedef struct {
    uint32_t date;
    uint32_t types;
} HolidayEntry;

static HolidayEntry g_holidays[MAX_HOLIDAYS];
static int g_holiday_count = 0;

// =============================================================================
// HolidayDate Implementation
// =============================================================================

HolidayDate_t* HolidayDate_Create(uint32_t date, uint32_t holiday_types) {
    HolidayDate_t* holiday = (HolidayDate_t*)malloc(sizeof(HolidayDate_t));
    if (holiday) {
        holiday->Date = date;
        holiday->HolidayTypes = holiday_types;
    }
    return holiday;
}

void HolidayDate_Destroy(HolidayDate_t* holiday) {
    if (holiday) {
        free(holiday);
    }
}

// =============================================================================
// Internal Helper Functions
// =============================================================================

static int FindHolidayIndex(uint32_t date) {
    for (int i = 0; i < g_holiday_count; i++) {
        if (g_holidays[i].date == date) {
            return i;
        }
    }
    return -1;
}

// =============================================================================
// Holiday Management Functions
// =============================================================================

ErrorCode_t Holiday_Add(uint32_t date, uint32_t holiday_types) {
    if (!Holiday_IsValidDate(date)) {
        return ErrorCode_BadParams;
    }

    int index = FindHolidayIndex(date);

    if (index >= 0) {
        // Date exists - OR the types together
        g_holidays[index].types |= holiday_types;
    } else {
        // New date
        if (g_holiday_count >= MAX_HOLIDAYS) {
            return ErrorCode_OutOfMemory;
        }
        g_holidays[g_holiday_count].date = date;
        g_holidays[g_holiday_count].types = holiday_types;
        g_holiday_count++;
    }

    return ErrorCode_OK;
}

ErrorCode_t Holiday_Update(uint32_t date, uint32_t holiday_types) {
    if (!Holiday_IsValidDate(date)) {
        return ErrorCode_BadParams;
    }

    int index = FindHolidayIndex(date);

    if (index >= 0) {
        // Update existing
        g_holidays[index].types = holiday_types;
    } else {
        // Create new
        if (g_holiday_count >= MAX_HOLIDAYS) {
            return ErrorCode_OutOfMemory;
        }
        g_holidays[g_holiday_count].date = date;
        g_holidays[g_holiday_count].types = holiday_types;
        g_holiday_count++;
    }

    return ErrorCode_OK;
}

ErrorCode_t Holiday_DeleteTypes(uint32_t date, uint32_t holiday_types_to_remove) {
    int index = FindHolidayIndex(date);

    if (index < 0) {
        return ErrorCode_ObjectNotFound;
    }

    // Remove specified types
    g_holidays[index].types &= ~holiday_types_to_remove;

    // If no types remain, delete the entry
    if (g_holidays[index].types == 0) {
        // Shift remaining entries
        for (int i = index; i < g_holiday_count - 1; i++) {
            g_holidays[i] = g_holidays[i + 1];
        }
        g_holiday_count--;
    }

    return ErrorCode_OK;
}

ErrorCode_t Holiday_Delete(uint32_t date) {
    int index = FindHolidayIndex(date);

    if (index < 0) {
        return ErrorCode_ObjectNotFound;
    }

    // Shift remaining entries
    for (int i = index; i < g_holiday_count - 1; i++) {
        g_holidays[i] = g_holidays[i + 1];
    }
    g_holiday_count--;

    return ErrorCode_OK;
}

ErrorCode_t Holiday_Clear(void) {
    g_holiday_count = 0;
    memset(g_holidays, 0, sizeof(g_holidays));
    return ErrorCode_OK;
}

uint32_t Holiday_GetTypes(uint32_t date) {
    int index = FindHolidayIndex(date);
    if (index >= 0) {
        return g_holidays[index].types;
    }
    return 0;
}

uint32_t Holiday_GetTypesToday(void) {
    time_t now = time(NULL);
    uint32_t today = Holiday_DateFromTime(now);
    return Holiday_GetTypes(today);
}

int Holiday_IsHoliday(uint32_t date) {
    return FindHolidayIndex(date) >= 0 ? 1 : 0;
}

int Holiday_MatchesTypes(uint32_t date, uint32_t holiday_types) {
    uint32_t date_types = Holiday_GetTypes(date);
    return (date_types & holiday_types) != 0 ? 1 : 0;
}

Vector_t* Holiday_GetRange(uint32_t start_date, uint32_t end_date) {
    Vector_t* result = Vector_Create(10);

    for (int i = 0; i < g_holiday_count; i++) {
        if (g_holidays[i].date >= start_date && g_holidays[i].date <= end_date) {
            HolidayDate_t* holiday = HolidayDate_Create(g_holidays[i].date, g_holidays[i].types);
            Vector_Add(result, holiday);
        }
    }

    return result;
}

int Holiday_Count(void) {
    return g_holiday_count;
}

// =============================================================================
// Utility Functions
// =============================================================================

uint32_t Holiday_DateFromTime(time_t timestamp) {
    struct tm* tm_info = localtime(&timestamp);
    uint32_t year = tm_info->tm_year + 1900;
    uint32_t month = tm_info->tm_mon + 1;
    uint32_t day = tm_info->tm_mday;
    return year * 10000 + month * 100 + day;
}

time_t Holiday_TimeFromDate(uint32_t date) {
    uint32_t year = date / 10000;
    uint32_t month = (date / 100) % 100;
    uint32_t day = date % 100;

    struct tm tm_info = {0};
    tm_info.tm_year = year - 1900;
    tm_info.tm_mon = month - 1;
    tm_info.tm_mday = day;
    tm_info.tm_hour = 0;
    tm_info.tm_min = 0;
    tm_info.tm_sec = 0;
    tm_info.tm_isdst = -1;  // Auto-detect DST

    return mktime(&tm_info);
}

uint32_t Holiday_ParseDate(const char* date_string) {
    if (!date_string) return 0;

    unsigned int year, month, day;
    if (sscanf(date_string, "%u-%u-%u", &year, &month, &day) == 3) {
        return year * 10000 + month * 100 + day;
    }

    return 0;
}

char* Holiday_FormatDate(uint32_t date) {
    uint32_t year = date / 10000;
    uint32_t month = (date / 100) % 100;
    uint32_t day = date % 100;

    char* result = (char*)malloc(11);  // "YYYY-MM-DD\0"
    if (result) {
        snprintf(result, 11, "%04u-%02u-%02u", year, month, day);
    }
    return result;
}

int Holiday_IsValidDate(uint32_t date) {
    uint32_t year = date / 10000;
    uint32_t month = (date / 100) % 100;
    uint32_t day = date % 100;

    // Basic validation
    if (year < 1970 || year > 2100) return 0;
    if (month < 1 || month > 12) return 0;
    if (day < 1 || day > 31) return 0;

    // Month-specific day validation
    static const int days_in_month[] = {31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31};
    if (day > days_in_month[month - 1]) return 0;

    return 1;
}
