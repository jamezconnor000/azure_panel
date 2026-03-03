#include <stdio.h>
#include <stdlib.h>
#include <assert.h>
#include <string.h>
#include "../src/sdk_modules/holidays/holiday.h"

int main() {
    printf("=== SDK Holidays Module Test ===\n\n");

    // Test date utilities
    printf("--- Date Utilities ---\n");
    uint32_t christmas = Holiday_ParseDate("2025-12-25");
    printf("Christmas 2025: %u\n", christmas);
    assert(christmas == 20251225);

    char* formatted = Holiday_FormatDate(christmas);
    printf("Formatted: %s\n", formatted);
    assert(strcmp(formatted, "2025-12-25") == 0);
    free(formatted);

    int valid = Holiday_IsValidDate(christmas);
    printf("Date is %s\n", valid ? "VALID ✓" : "INVALID ✗");
    assert(valid == 1);

    // Add holidays
    printf("\n--- Adding Holidays ---\n");
    ErrorCode_t result = Holiday_Add(20251225, HolidayType_1);  // Christmas
    printf("Added Christmas as Type 1: %s\n", result == ErrorCode_OK ? "✓" : "✗");
    assert(result == ErrorCode_OK);

    result = Holiday_Add(20251225, HolidayType_2);  // Also a Type 2 holiday
    printf("Added Christmas as Type 2: %s\n", result == ErrorCode_OK ? "✓" : "✗");
    assert(result == ErrorCode_OK);

    result = Holiday_Add(20250101, HolidayType_1);  // New Year's Day
    printf("Added New Year's as Type 1: %s\n", result == ErrorCode_OK ? "✓" : "✗");
    assert(result == ErrorCode_OK);

    result = Holiday_Add(20250704, HolidayType_3);  // Independence Day
    printf("Added Independence Day as Type 3: %s\n", result == ErrorCode_OK ? "✓" : "✗");
    assert(result == ErrorCode_OK);

    // Check holiday types
    printf("\n--- Checking Holiday Types ---\n");
    uint32_t types = Holiday_GetTypes(20251225);
    printf("Christmas has types: 0x%08X\n", types);
    assert(types == (HolidayType_1 | HolidayType_2));

    int is_holiday = Holiday_IsHoliday(20251225);
    printf("Is Christmas a holiday? %s\n", is_holiday ? "YES ✓" : "NO ✗");
    assert(is_holiday == 1);

    int matches = Holiday_MatchesTypes(20251225, HolidayType_1);
    printf("Christmas matches Type 1? %s\n", matches ? "YES ✓" : "NO ✗");
    assert(matches == 1);

    matches = Holiday_MatchesTypes(20251225, HolidayType_3);
    printf("Christmas matches Type 3? %s\n", matches ? "NO ✓" : "YES ✗");
    assert(matches == 0);

    // Count holidays
    int count = Holiday_Count();
    printf("\nTotal holidays: %d\n", count);
    assert(count == 3);

    // Get range of holidays
    printf("\n--- Holiday Range Query ---\n");
    Vector_t* range = Holiday_GetRange(20250101, 20251231);
    printf("Holidays in 2025: %d\n", range->count);
    assert(range->count == 3);

    for (int i = 0; i < range->count; i++) {
        HolidayDate_t* hol = (HolidayDate_t*)range->data[i];
        printf("  - %u (types: 0x%08X)\n", hol->Date, hol->HolidayTypes);
        HolidayDate_Destroy(hol);
    }
    Vector_Destroy(range);

    // Delete specific types
    printf("\n--- Deleting Holiday Types ---\n");
    result = Holiday_DeleteTypes(20251225, HolidayType_1);
    printf("Removed Type 1 from Christmas: %s\n", result == ErrorCode_OK ? "✓" : "✗");
    assert(result == ErrorCode_OK);

    types = Holiday_GetTypes(20251225);
    printf("Christmas now has types: 0x%08X (should be Type 2 only)\n", types);
    assert(types == HolidayType_2);

    // Delete entire holiday
    printf("\n--- Deleting Holidays ---\n");
    result = Holiday_Delete(20250101);
    printf("Deleted New Year's: %s\n", result == ErrorCode_OK ? "✓" : "✗");
    assert(result == ErrorCode_OK);

    count = Holiday_Count();
    printf("Holidays remaining: %d\n", count);
    assert(count == 2);

    // Clear all holidays
    printf("\n--- Clearing All Holidays ---\n");
    result = Holiday_Clear();
    printf("Cleared all holidays: %s\n", result == ErrorCode_OK ? "✓" : "✗");
    assert(result == ErrorCode_OK);

    count = Holiday_Count();
    printf("Holidays remaining: %d\n", count);
    assert(count == 0);

    printf("\n✓ All tests passed!\n");

    return 0;
}
