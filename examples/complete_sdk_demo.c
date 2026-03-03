/*
 * Complete SDK Demo
 *
 * Demonstrates a realistic access control scenario using all SDK modules:
 * - Office building with 3 doors
 * - Employee and contractor permissions
 * - Business hours timezone
 * - Holiday handling
 * - Reader modes and indications
 * - Relay automation
 */

#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include "../src/hal_core/access_logic_sdk.h"
#include "../src/sdk_modules/permissions/permission.h"
#include "../src/sdk_modules/holidays/holiday.h"
#include "../src/sdk_modules/timezones/timezone.h"
#include "../src/sdk_modules/relays/relay.h"
#include "../src/sdk_modules/readers/reader.h"

void print_header(const char* title) {
    printf("\n");
    printf("════════════════════════════════════════════════════════════════\n");
    printf("  %s\n", title);
    printf("════════════════════════════════════════════════════════════════\n\n");
}

void print_decision(AccessDecision_t* decision) {
    printf("\n┌─────────────────────────────────────────────────────────┐\n");
    printf("│ ACCESS DECISION                                         │\n");
    printf("├─────────────────────────────────────────────────────────┤\n");
    printf("│ Card: %u                                        │\n", decision->card_number);
    printf("│ Result: %-45s │\n", decision->granted ? "✓ GRANTED" : "✗ DENIED");
    printf("│ Reason: %-47s │\n", decision->reason);
    printf("└─────────────────────────────────────────────────────────┘\n");
}

int main() {
    printf("\n");
    printf("╔══════════════════════════════════════════════════════════════╗\n");
    printf("║                                                              ║\n");
    printf("║         COMPLETE HAL SDK DEMONSTRATION                       ║\n");
    printf("║         Real-World Access Control Scenario                   ║\n");
    printf("║                                                              ║\n");
    printf("╚══════════════════════════════════════════════════════════════╝\n");

    // =========================================================================
    // INITIALIZATION
    // =========================================================================
    print_header("1. SYSTEM INITIALIZATION");

    AccessLogic_SDK_Initialize();
    Relay_Init();

    // =========================================================================
    // CONFIGURE HOLIDAYS
    // =========================================================================
    print_header("2. CONFIGURE HOLIDAYS");

    Holiday_Add(20251225, HolidayType_1);  // Christmas
    Holiday_Add(20250101, HolidayType_1);  // New Year's
    Holiday_Add(20250704, HolidayType_1);  // Independence Day

    printf("✓ Added 3 company holidays:\n");
    printf("  - Christmas (Dec 25)\n");
    printf("  - New Year's Day (Jan 1)\n");
    printf("  - Independence Day (Jul 4)\n");

    // =========================================================================
    // CONFIGURE TIME ZONES
    // =========================================================================
    print_header("3. CONFIGURE TIME ZONES");

    // Business hours: Monday-Friday 8AM-6PM
    TimeZone_t* tz_business = TimeZone_Create(100);
    TimeInterval_t* interval = TimeInterval_t_Create();
    interval->StartTime = Time_FromHMS(8, 0, 0);   // 8:00 AM
    interval->EndTime = Time_FromHMS(18, 0, 0);    // 6:00 PM
    interval->Recurrence = RecurrenceType_Cyclic;
    interval->CycleLength = 7;
    interval->CycleDays = 0x0000003E;  // Mon-Fri (bits 1-5)
    interval->CycleStart = time(NULL) - (86400 * 7);  // Started last week
    TimeZone_AddInterval(tz_business, interval);
    AccessLogic_SDK_AddTimeZone(tz_business);

    printf("✓ Business Hours Timezone (ID=100):\n");
    printf("  - Monday-Friday\n");
    printf("  - 8:00 AM - 6:00 PM\n");

    // Extended hours: Monday-Friday 6AM-10PM
    TimeZone_t* tz_extended = TimeZone_Create(101);
    TimeInterval_t* interval2 = TimeInterval_t_Create();
    interval2->StartTime = Time_FromHMS(6, 0, 0);
    interval2->EndTime = Time_FromHMS(22, 0, 0);
    interval2->Recurrence = RecurrenceType_Cyclic;
    interval2->CycleLength = 7;
    interval2->CycleDays = 0x0000003E;
    interval2->CycleStart = time(NULL) - (86400 * 7);
    TimeZone_AddInterval(tz_extended, interval2);
    AccessLogic_SDK_AddTimeZone(tz_extended);

    printf("✓ Extended Hours Timezone (ID=101):\n");
    printf("  - Monday-Friday\n");
    printf("  - 6:00 AM - 10:00 PM\n");

    // =========================================================================
    // CONFIGURE READERS AND RELAYS
    // =========================================================================
    print_header("4. CONFIGURE READERS AND RELAYS");

    // Front door (Reader 1, Relay 1)
    LPA_t reader1 = {.type = LPAType_Reader, .id = 1, .node_id = 0};
    Reader_t* r1 = Reader_Create(reader1);
    r1->InitMode = ReaderMode_CardOnly;
    r1->Flags = ReaderFlags_APBEnabled;
    Reader_Add(r1);

    LPA_t relay1 = {.type = LPAType_Relay, .id = 1, .node_id = 0};
    Relay_t* rl1 = Relay_Create(relay1);
    rl1->PulseDuration = 100;  // 1 second
    Relay_Add(rl1);

    printf("✓ Front Door (Reader 1, Relay 1):\n");
    printf("  - Mode: Card Only\n");
    printf("  - APB: Enabled\n");
    printf("  - Strike time: 1.0 seconds\n");

    // Server room (Reader 3, Relay 3)
    LPA_t reader3 = {.type = LPAType_Reader, .id = 3, .node_id = 0};
    Reader_t* r3 = Reader_Create(reader3);
    r3->InitMode = ReaderMode_CardAndPin;
    r3->Flags = ReaderFlags_PINMandatory | ReaderFlags_TwoPersonRule;
    Reader_Add(r3);

    LPA_t relay3 = {.type = LPAType_Relay, .id = 3, .node_id = 0};
    Relay_t* rl3 = Relay_Create(relay3);
    rl3->PulseDuration = 50;  // 0.5 seconds
    rl3->CtrlTimeZone = 100;  // Business hours only
    Relay_Add(rl3);

    printf("✓ Server Room (Reader 3, Relay 3):\n");
    printf("  - Mode: Card + PIN\n");
    printf("  - Two-person rule: Required\n");
    printf("  - Access: Business hours only\n");
    printf("  - Strike time: 0.5 seconds\n");

    // =========================================================================
    // CONFIGURE PERMISSIONS
    // =========================================================================
    print_header("5. CONFIGURE PERMISSIONS");

    // Employee permission (Card 100001)
    Permission_t* perm_employee = Permission_Create(1);
    perm_employee->ActivationDateTime = 0;  // Always active
    perm_employee->DeactivationDateTime = 0;  // Never expires

    PermissionEntry_t* entry1 = PermissionEntry_Create();
    entry1->AccessObject = reader1;
    entry1->TimeZone = 101;  // Extended hours
    entry1->Strike = relay1;
    Permission_AddEntry(perm_employee, entry1);

    PermissionEntry_t* entry2 = PermissionEntry_Create();
    entry2->AccessObject = reader3;
    entry2->TimeZone = 100;  // Business hours
    entry2->Strike = relay3;
    Permission_AddEntry(perm_employee, entry2);

    AccessLogic_SDK_AddPermission(perm_employee);

    printf("✓ Employee Permission (ID=1, Card 100001):\n");
    printf("  - Front door: Extended hours (6AM-10PM)\n");
    printf("  - Server room: Business hours (8AM-6PM)\n");

    // Contractor permission (Card 200001)
    Permission_t* perm_contractor = Permission_Create(2);

    PermissionEntry_t* entry3 = PermissionEntry_Create();
    entry3->AccessObject = reader1;
    entry3->TimeZone = 100;  // Business hours only
    entry3->Strike = relay1;
    Permission_AddEntry(perm_contractor, entry3);

    // Exclude from server room
    ExclusionEntry_t* excl = ExclusionEntry_Create();
    excl->AccessObject = reader3;
    Permission_AddExclusion(perm_contractor, excl);

    AccessLogic_SDK_AddPermission(perm_contractor);

    printf("✓ Contractor Permission (ID=2, Card 200001):\n");
    printf("  - Front door: Business hours only (8AM-6PM)\n");
    printf("  - Server room: EXCLUDED\n");

    // =========================================================================
    // SIMULATE ACCESS SCENARIOS
    // =========================================================================
    print_header("6. ACCESS SCENARIOS");

    // Scenario 1: Employee at front door
    printf("Scenario 1: Employee (100001) swipes at front door\n");
    AccessDecision_t decision = AccessLogic_SDK_ProcessCardRead(
        100001, 1, reader1, relay1
    );
    print_decision(&decision);
    if (decision.granted) {
        AccessLogic_SDK_SetReaderMode(reader1, ReaderMode_CardOnly);
        Reader_SetIndicationState(reader1, ReaderIndicationState_Grant);
    }

    // Scenario 2: Contractor tries server room
    printf("\nScenario 2: Contractor (200001) tries server room\n");
    decision = AccessLogic_SDK_ProcessCardRead(
        200001, 2, reader3, relay3
    );
    print_decision(&decision);
    if (!decision.granted) {
        Reader_SetIndicationState(reader3, ReaderIndicationState_Deny);
    }

    // Scenario 3: Employee at server room
    printf("\nScenario 3: Employee (100001) accesses server room\n");
    decision = AccessLogic_SDK_ProcessCardRead(
        100001, 1, reader3, relay3
    );
    print_decision(&decision);
    if (decision.granted) {
        Reader_SetIndicationState(reader3, ReaderIndicationState_Grant);
        AccessLogic_SDK_GenerateAccessEvent(&decision);
    }

    // Scenario 4: Unknown card
    printf("\nScenario 4: Unknown card (999999) at front door\n");
    decision = AccessLogic_SDK_ProcessCardRead(
        999999, 999, reader1, relay1
    );
    print_decision(&decision);

    // =========================================================================
    // READER MODE CHANGES
    // =========================================================================
    print_header("7. READER MODE CHANGES");

    printf("Unlocking front door for maintenance...\n");
    AccessLogic_SDK_SetReaderMode(reader1, ReaderMode_Unlocked);
    printf("✓ Front door is now UNLOCKED\n");

    printf("\nLocking front door after maintenance...\n");
    AccessLogic_SDK_SetReaderMode(reader1, ReaderMode_Locked);
    printf("✓ Front door is now LOCKED\n");

    printf("\nReturning to normal operation...\n");
    AccessLogic_SDK_SetReaderMode(reader1, ReaderMode_CardOnly);
    printf("✓ Front door is now CARD ONLY\n");

    // =========================================================================
    // SUMMARY
    // =========================================================================
    print_header("8. SYSTEM SUMMARY");

    printf("System Configuration:\n");
    printf("  ✓ Holidays: %d\n", Holiday_Count());
    printf("  ✓ Time Zones: 2 (Business + Extended)\n");
    printf("  ✓ Readers: 2 (Front Door, Server Room)\n");
    printf("  ✓ Relays: 2\n");
    printf("  ✓ Permissions: 2 (Employee, Contractor)\n");
    printf("\nAll SDK modules integrated and working!\n");

    // =========================================================================
    // CLEANUP
    // =========================================================================
    print_header("9. SHUTDOWN");

    AccessLogic_SDK_Shutdown();
    Holiday_Clear();

    printf("✓ System shutdown complete\n\n");

    return 0;
}
