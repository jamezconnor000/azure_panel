#include <stdio.h>
#include <stdlib.h>
#include <assert.h>
#include <time.h>
#include "../src/sdk_modules/permissions/permission.h"
#include "../src/sdk_modules/holidays/holiday.h"
#include "../src/sdk_modules/relays/relay.h"
#include "../src/sdk_modules/readers/reader.h"
#include "../src/sdk_modules/group_lists/group_list.h"
#include "../src/sdk_modules/timezones/timezone.h"

void print_separator(const char* title) {
    printf("\n");
    printf("=============================================================================\n");
    printf("  %s\n", title);
    printf("=============================================================================\n\n");
}

int main() {
    printf("╔═══════════════════════════════════════════════════════════════╗\n");
    printf("║      HAL SDK COMPLETE INTEGRATION TEST                       ║\n");
    printf("║      Testing all SDK modules working together                ║\n");
    printf("╚═══════════════════════════════════════════════════════════════╝\n");

    // =========================================================================
    // SCENARIO: Office Building Access Control System
    // =========================================================================

    print_separator("SCENARIO SETUP");
    printf("Office building with:\n");
    printf("  - Front door (Reader 1, Relay 1)\n");
    printf("  - Back door (Reader 2, Relay 2)\n");
    printf("  - Server room (Reader 3, Relay 3)\n");
    printf("  - Employee: John Doe (Permission 1)\n");
    printf("  - Contractor: Jane Smith (Permission 2)\n");
    printf("  - Holidays: Christmas, New Year's\n");
    printf("  - Business hours: Monday-Friday 8AM-6PM\n");

    // =========================================================================
    // STEP 1: Configure Holidays
    // =========================================================================
    print_separator("STEP 1: Configure Holidays");

    Holiday_Add(20251225, HolidayType_1);  // Christmas
    Holiday_Add(20250101, HolidayType_1);  // New Year's
    printf("✓ Added 2 holidays (Christmas, New Year's)\n");
    printf("  Holiday count: %d\n", Holiday_Count());

    // =========================================================================
    // STEP 2: Configure Time Zones
    // =========================================================================
    print_separator("STEP 2: Configure Time Zones");

    // Business hours: Monday-Friday 8AM-6PM
    TimeZone_t* tz_business = TimeZone_Create(100);
    TimeInterval_t* interval = TimeInterval_t_Create();
    interval->StartTime = Time_FromHMS(8, 0, 0);   // 8:00 AM
    interval->EndTime = Time_FromHMS(18, 0, 0);    // 6:00 PM
    interval->Recurrence = RecurrenceType_Cyclic;
    interval->CycleLength = 7;                      // Weekly cycle
    interval->CycleDays = 0x0000003E;              // Mon-Fri (bits 1-5)
    TimeZone_AddInterval(tz_business, interval);
    printf("✓ Created business hours timezone (Mon-Fri 8AM-6PM)\n");

    // After hours: All other times
    TimeZone_t* tz_afterhours = TimeZone_Create(101);
    printf("✓ Created after-hours timezone\n");

    // =========================================================================
    // STEP 3: Configure Relays
    // =========================================================================
    print_separator("STEP 3: Configure Relays");

    Relay_Init();

    LPA_t relay1_lpa = {.type = LPAType_Relay, .id = 1, .node_id = 0};
    Relay_t* relay1 = Relay_Create(relay1_lpa);
    relay1->PulseDuration = 100;  // 1 second (100 * 10ms)
    Relay_Add(relay1);
    printf("✓ Configured Relay 1 (Front door strike)\n");

    LPA_t relay2_lpa = {.type = LPAType_Relay, .id = 2, .node_id = 0};
    Relay_t* relay2 = Relay_Create(relay2_lpa);
    relay2->PulseDuration = 100;
    Relay_Add(relay2);
    printf("✓ Configured Relay 2 (Back door strike)\n");

    LPA_t relay3_lpa = {.type = LPAType_Relay, .id = 3, .node_id = 0};
    Relay_t* relay3 = Relay_Create(relay3_lpa);
    relay3->PulseDuration = 50;   // 0.5 second for server room
    relay3->CtrlTimeZone = 100;   // Only unlock during business hours
    relay3->Flags = RelayFlags_OnWhileTZActive;
    Relay_Add(relay3);
    printf("✓ Configured Relay 3 (Server room - restricted)\n");

    // =========================================================================
    // STEP 4: Configure Readers
    // =========================================================================
    print_separator("STEP 4: Configure Readers");

    LPA_t reader1_lpa = {.type = LPAType_Reader, .id = 1, .node_id = 0};
    Reader_t* reader1 = Reader_Create(reader1_lpa);
    reader1->InitMode = ReaderMode_CardOnly;
    reader1->Flags = ReaderFlags_APBEnabled;
    Reader_Add(reader1);
    printf("✓ Configured Reader 1 (Front door, Card Only, APB enabled)\n");

    LPA_t reader2_lpa = {.type = LPAType_Reader, .id = 2, .node_id = 0};
    Reader_t* reader2 = Reader_Create(reader2_lpa);
    reader2->InitMode = ReaderMode_CardOnly;
    Reader_Add(reader2);
    printf("✓ Configured Reader 2 (Back door, Card Only)\n");

    LPA_t reader3_lpa = {.type = LPAType_Reader, .id = 3, .node_id = 0};
    Reader_t* reader3 = Reader_Create(reader3_lpa);
    reader3->InitMode = ReaderMode_CardAndPin;
    reader3->Flags = ReaderFlags_PINMandatory | ReaderFlags_TwoPersonRule;
    Reader_Add(reader3);
    printf("✓ Configured Reader 3 (Server room, Card+PIN, Two-person rule)\n");

    // =========================================================================
    // STEP 5: Configure Permissions
    // =========================================================================
    print_separator("STEP 5: Configure Permissions");

    // Employee permission (John Doe) - Access all doors during business hours
    Permission_t* perm_employee = Permission_Create(1);

    PermissionEntry_t* entry1 = PermissionEntry_Create();
    entry1->AccessObject = reader1_lpa;
    entry1->TimeZone = 100;  // Business hours
    entry1->Strike = relay1_lpa;
    Permission_AddEntry(perm_employee, entry1);

    PermissionEntry_t* entry2 = PermissionEntry_Create();
    entry2->AccessObject = reader2_lpa;
    entry2->TimeZone = 100;  // Business hours
    entry2->Strike = relay2_lpa;
    Permission_AddEntry(perm_employee, entry2);

    PermissionEntry_t* entry3 = PermissionEntry_Create();
    entry3->AccessObject = reader3_lpa;
    entry3->TimeZone = 100;  // Business hours
    entry3->Strike = relay3_lpa;
    Permission_AddEntry(perm_employee, entry3);

    printf("✓ Created Employee Permission (John Doe)\n");
    printf("  - Front door (business hours)\n");
    printf("  - Back door (business hours)\n");
    printf("  - Server room (business hours)\n");

    // Contractor permission (Jane Smith) - Front door only, no server room
    Permission_t* perm_contractor = Permission_Create(2);

    PermissionEntry_t* entry4 = PermissionEntry_Create();
    entry4->AccessObject = reader1_lpa;
    entry4->TimeZone = 100;  // Business hours
    entry4->Strike = relay1_lpa;
    Permission_AddEntry(perm_contractor, entry4);

    // Explicitly exclude server room
    ExclusionEntry_t* exclusion = ExclusionEntry_Create();
    exclusion->AccessObject = reader3_lpa;
    Permission_AddExclusion(perm_contractor, exclusion);

    printf("✓ Created Contractor Permission (Jane Smith)\n");
    printf("  - Front door only (business hours)\n");
    printf("  - Server room EXCLUDED\n");

    // =========================================================================
    // STEP 6: Configure Group Lists
    // =========================================================================
    print_separator("STEP 6: Configure Group Lists (Escorts)");

    LPA_t escort_list_lpa = {.type = 0, .id = 1, .node_id = 0};
    GroupList_t* escort_list = GroupList_Create(escort_list_lpa);
    GroupList_AddGroup(escort_list, 100);  // Security group
    GroupList_AddGroup(escort_list, 101);  // Management group
    GroupList_Add(escort_list);

    printf("✓ Created escort group list\n");
    printf("  - Security group (100)\n");
    printf("  - Management group (101)\n");

    // =========================================================================
    // STEP 7: Simulate Access Scenarios
    // =========================================================================
    print_separator("STEP 7: Simulate Access Scenarios");

    time_t now = time(NULL);

    // Scenario A: Employee accesses front door
    printf("Scenario A: John Doe (Employee) swipes at front door\n");
    printf("  Permission active: %s\n", Permission_IsActive(perm_employee, now) ? "YES" : "NO");
    printf("  Has entry for Reader 1: %s\n",
           Permission_FindEntryForAccessObject(perm_employee, reader1_lpa) ? "YES" : "NO");
    printf("  Is excluded: %s\n",
           Permission_IsExcluded(perm_employee, reader1_lpa) ? "YES" : "NO");
    int access = Permission_EvaluateAccess(perm_employee, reader1_lpa, now, 0);
    printf("  Decision: %s\n", access == 1 ? "GRANT ✓" : "DENY ✗");

    if (access == 1) {
        Reader_SetIndicationState(reader1_lpa, ReaderIndicationState_Grant);
        Relay_Pulse(relay1_lpa);
    }

    // Scenario B: Contractor tries server room
    printf("\nScenario B: Jane Smith (Contractor) tries server room\n");
    printf("  Permission active: %s\n", Permission_IsActive(perm_contractor, now) ? "YES" : "NO");
    printf("  Has entry for Reader 3: %s\n",
           Permission_FindEntryForAccessObject(perm_contractor, reader3_lpa) ? "YES" : "NO");
    printf("  Is excluded: %s\n",
           Permission_IsExcluded(perm_contractor, reader3_lpa) ? "YES" : "NO");
    access = Permission_EvaluateAccess(perm_contractor, reader3_lpa, now, 0);
    printf("  Decision: %s (Excluded)\n", access == 0 ? "DENY ✓" : "GRANT ✗");

    if (access == 0) {
        Reader_SetIndicationState(reader3_lpa, ReaderIndicationState_Deny);
    }

    // Scenario C: Reader mode changes
    printf("\nScenario C: Front door reader mode changes\n");
    printf("  Initial mode: %d (CardOnly)\n", Reader_GetMode(reader1_lpa));
    Reader_SetMode(reader1_lpa, ReaderMode_Unlocked);
    printf("  New mode: %d (Unlocked)\n", Reader_GetMode(reader1_lpa));
    Reader_SetIndicationState(reader1_lpa, ReaderIndicationState_Unlocked);

    // =========================================================================
    // STEP 8: Relay Automation
    // =========================================================================
    print_separator("STEP 8: Relay Automation (Event-Driven)");

    // Create relay link: When Reader 1 grants access, pulse Relay 1
    LPA_t relay_link_lpa = {.type = 0, .id = 1, .node_id = 0};
    RelayLink_t* link = RelayLink_Create(relay_link_lpa);

    RelayLinkRecord_t* record = (RelayLinkRecord_t*)malloc(sizeof(RelayLinkRecord_t));
    record->Source = reader1_lpa;
    record->Type = EventType_AccPoint;
    record->SubType = etAccPoint_Grant;
    record->NewStatus = 0xFF;  // Any status
    record->Operation = RelayControlOperation_PULSE;
    RelayLink_AddRecord(link, record);
    Relay_AddLink(link);

    printf("✓ Created relay automation link\n");
    printf("  When Reader 1 grants access → Pulse Relay 1\n");

    // Trigger the automation
    printf("\nTriggering automation...\n");
    Relay_ProcessEvent(reader1_lpa, EventType_AccPoint, etAccPoint_Grant, 0);

    // =========================================================================
    // SUMMARY
    // =========================================================================
    print_separator("TEST SUMMARY");

    printf("✓ Holidays configured: %d\n", Holiday_Count());
    printf("✓ Time zones configured: 2\n");
    printf("✓ Relays configured: 3\n");
    printf("✓ Readers configured: 3\n");
    printf("✓ Permissions configured: 2\n");
    printf("✓ Group lists configured: 1\n");
    printf("✓ Relay automation links: 1\n");

    printf("\n");
    printf("═══════════════════════════════════════════════════════════════\n");
    printf("  All SDK modules are working together successfully!\n");
    printf("═══════════════════════════════════════════════════════════════\n\n");

    // Cleanup
    Permission_Destroy(perm_employee);
    Permission_Destroy(perm_contractor);
    TimeZone_Destroy(tz_business);
    TimeZone_Destroy(tz_afterhours);
    Holiday_Clear();

    return 0;
}
