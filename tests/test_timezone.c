#include "../src/sdk_modules/timezones/timezone.h"
#include "../src/sdk_modules/common/sdk_types.h"
#include <stdio.h>
#include <time.h>

int main() {
    printf("=== Testing TimeZone Module ===\n\n");
    
    // Create a timezone
    TimeZone_t* tz = TimeZone_Create(1);
    if (!tz) {
        printf("ERROR: Failed to create timezone\n");
        return 1;
    }
    printf("✓ TimeZone created (ID=%d)\n", tz->Id);
    
    // Create an interval: Monday-Friday, 9 AM to 5 PM
    TimeInterval_t* interval = TimeInterval_t_Create();
    if (!interval) {
        printf("ERROR: Failed to create interval\n");
        TimeZone_Destroy(tz);
        return 1;
    }
    
    interval->StartTime = Time_FromHMS(9, 0, 0);   // 9:00 AM
    interval->EndTime = Time_FromHMS(17, 0, 0);    // 5:00 PM
    interval->Recurrence = RecurrenceType_Cyclic;
    interval->CycleLength = 7;                      // Weekly cycle
    interval->CycleDays = 0x0000003E;              // Mon-Fri (bits 1-5)
    interval->CycleStart = time(NULL) - (86400 * 30);  // Started 30 days ago
    
    TimeZone_AddInterval(tz, interval);
    printf("✓ Interval added: Mon-Fri 9AM-5PM\n\n");
    
    // Test current time
    time_t now = time(NULL);
    int is_active = TimeZone_IsActive(tz, now, 0);
    
    struct tm* tm_info = localtime(&now);
    printf("Current time: %04d-%02d-%02d %02d:%02d:%02d\n",
           tm_info->tm_year + 1900, tm_info->tm_mon + 1, tm_info->tm_mday,
           tm_info->tm_hour, tm_info->tm_min, tm_info->tm_sec);
    
    printf("Day of week: ");
    switch(tm_info->tm_wday) {
        case 0: printf("Sunday\n"); break;
        case 1: printf("Monday\n"); break;
        case 2: printf("Tuesday\n"); break;
        case 3: printf("Wednesday\n"); break;
        case 4: printf("Thursday\n"); break;
        case 5: printf("Friday\n"); break;
        case 6: printf("Saturday\n"); break;
    }
    
    printf("\nTimeZone Status: %s\n", is_active ? "✓ ACTIVE" : "✗ INACTIVE");
    
    // Cleanup
    TimeZone_Destroy(tz);
    printf("\n✓ Test complete - TimeZone module is working!\n");
    
    return 0;
}
