/*
 * SDK Database Persistence Test
 *
 * Verifies that all SDK modules can be saved to and loaded from the database.
 * Tests the complete round-trip: Create -> Save -> Destroy -> Load -> Verify
 */

#include <stdio.h>
#include <stdlib.h>
#include <assert.h>
#include <string.h>
#include <time.h>

// Include SDK types first to avoid conflicts
#include "../src/sdk_modules/common/sdk_types.h"
#include "../src/sdk_modules/common/sdk_database.h"

// Forward declare card database functions to avoid including hal_types.h
typedef struct {
    uint32_t card_number;
    uint32_t permission_id;
    char card_holder_name[128];
    uint64_t activation_date;
    uint64_t expiration_date;
    bool is_active;
    uint32_t pin;
} CardRecord_t;

ErrorCode_t CardDatabase_Initialize(const char* db_path);
void CardDatabase_Shutdown(void);
ErrorCode_t CardDatabase_AddCard(const CardRecord_t* card);
ErrorCode_t CardDatabase_GetCard(uint32_t card_number, CardRecord_t* out_card);
ErrorCode_t CardDatabase_UpdateCard(const CardRecord_t* card);
uint32_t CardDatabase_GetPermissionForCard(uint32_t card_number);
bool CardDatabase_ValidatePIN(uint32_t card_number, uint32_t pin);
int CardDatabase_LoadAllCards(CardRecord_t* out_cards, int max_count);

#define TEST_DB_PATH "test_sdk_persistence.db"

void print_header(const char* title) {
    printf("\n");
    printf("=============================================================================\n");
    printf("  %s\n", title);
    printf("=============================================================================\n\n");
}

int main() {
    printf("\n");
    printf("╔══════════════════════════════════════════════════════════════╗\n");
    printf("║                                                              ║\n");
    printf("║         SDK DATABASE PERSISTENCE TEST                       ║\n");
    printf("║         Verify Save/Load Round-Trip                         ║\n");
    printf("║                                                              ║\n");
    printf("╚══════════════════════════════════════════════════════════════╝\n");

    // Delete old test database
    remove(TEST_DB_PATH);

    // =========================================================================
    // PHASE 1: Initialize Databases
    // =========================================================================
    print_header("PHASE 1: Initialize Databases");

    ErrorCode_t result = SDK_Database_Initialize(TEST_DB_PATH);
    assert(result == ErrorCode_OK);
    printf("✓ SDK Database initialized\n");

    // Apply SDK schema using sqlite3 command-line tool
    printf("Applying SDK schema...\n");
    int schema_result = system("sqlite3 test_sdk_persistence.db < ./schema/sdk_tables.sql 2>&1");
    if (schema_result != 0) {
        fprintf(stderr, "Warning: Schema application returned non-zero status: %d\n", schema_result);
    }
    printf("✓ SDK schema applied\n");

    result = CardDatabase_Initialize(TEST_DB_PATH);
    assert(result == ErrorCode_OK);
    printf("✓ Card Database initialized\n");

    // =========================================================================
    // PHASE 2: Create and Save Permissions
    // =========================================================================
    print_header("PHASE 2: Create and Save Permissions");

    Permission_t* perm1 = Permission_Create(100);
    perm1->ActivationDateTime = 1704067200;  // 2024-01-01 00:00:00
    perm1->DeactivationDateTime = 1735689599;  // 2024-12-31 23:59:59

    // Add entry for reader 1
    LPA_t reader1 = {.type = LPAType_Reader, .id = 1, .node_id = 0};
    LPA_t relay1 = {.type = LPAType_Relay, .id = 1, .node_id = 0};
    PermissionEntry_t* entry1 = PermissionEntry_Create();
    entry1->AccessObject = reader1;
    entry1->TimeZone = 100;
    entry1->Strike = relay1;
    Permission_AddEntry(perm1, entry1);

    // Add entry for reader 2
    LPA_t reader2 = {.type = LPAType_Reader, .id = 2, .node_id = 0};
    LPA_t relay2 = {.type = LPAType_Relay, .id = 2, .node_id = 0};
    PermissionEntry_t* entry2 = PermissionEntry_Create();
    entry2->AccessObject = reader2;
    entry2->TimeZone = 101;
    entry2->Strike = relay2;
    Permission_AddEntry(perm1, entry2);

    // Add exclusion for reader 3
    LPA_t reader3 = {.type = LPAType_Reader, .id = 3, .node_id = 0};
    ExclusionEntry_t* exclusion = ExclusionEntry_Create();
    exclusion->AccessObject = reader3;
    Permission_AddExclusion(perm1, exclusion);

    result = Permission_SaveToDB(perm1);
    assert(result == ErrorCode_OK);
    printf("✓ Saved Permission 100 with 2 entries and 1 exclusion\n");

    // =========================================================================
    // PHASE 3: Create and Save TimeZones
    // =========================================================================
    print_header("PHASE 3: Create and Save TimeZones");

    TimeZone_t* tz1 = TimeZone_Create(100);
    TimeInterval_t* interval1 = TimeInterval_t_Create();
    interval1->StartTime = Time_FromHMS(8, 0, 0);
    interval1->EndTime = Time_FromHMS(18, 0, 0);
    interval1->Recurrence = RecurrenceType_Cyclic;
    interval1->CycleLength = 7;
    interval1->CycleDays = 0x0000003E;  // Mon-Fri
    interval1->CycleStart = time(NULL) - (86400 * 7);
    TimeZone_AddInterval(tz1, interval1);

    result = TimeZone_SaveToDB(tz1);
    assert(result == ErrorCode_OK);
    printf("✓ Saved TimeZone 100 (Business hours)\n");

    // =========================================================================
    // PHASE 4: Create and Save Relays
    // =========================================================================
    print_header("PHASE 4: Create and Save Relays");

    Relay_t* relay_obj1 = Relay_Create(relay1);
    relay_obj1->PulseDuration = 100;
    relay_obj1->CtrlTimeZone = 100;
    relay_obj1->Flags = RelayFlags_OnWhileTZActive;
    relay_obj1->Mode = RelayMode_Auto;

    result = Relay_SaveToDB(relay_obj1);
    assert(result == ErrorCode_OK);
    printf("✓ Saved Relay 1\n");

    // =========================================================================
    // PHASE 5: Create and Save Readers
    // =========================================================================
    print_header("PHASE 5: Create and Save Readers");

    Reader_t* reader_obj1 = Reader_Create(reader1);
    reader_obj1->InitMode = ReaderMode_CardOnly;
    reader_obj1->Flags = ReaderFlags_APBEnabled;

    result = Reader_SaveToDB(reader_obj1);
    assert(result == ErrorCode_OK);
    printf("✓ Saved Reader 1 (InitMode and Flags only)\n");

    // =========================================================================
    // PHASE 6: Create and Save GroupLists
    // =========================================================================
    print_header("PHASE 6: Create and Save GroupLists");

    LPA_t group_list_lpa = {.type = 0, .id = 1, .node_id = 0};
    GroupList_t* group_list = GroupList_Create(group_list_lpa);
    GroupList_AddGroup(group_list, 100);
    GroupList_AddGroup(group_list, 101);
    GroupList_AddGroup(group_list, 102);

    result = GroupList_SaveToDB(group_list);
    assert(result == ErrorCode_OK);
    printf("✓ Saved GroupList 1 with 3 groups\n");

    // =========================================================================
    // PHASE 7: Create and Save Holidays
    // =========================================================================
    print_header("PHASE 7: Create and Save Holidays");

    result = Holiday_SaveToDB(20251225, HolidayType_1);  // Christmas
    assert(result == ErrorCode_OK);
    result = Holiday_SaveToDB(20250101, HolidayType_1);  // New Year's
    assert(result == ErrorCode_OK);
    result = Holiday_SaveToDB(20250704, HolidayType_1 | HolidayType_2);  // July 4th
    assert(result == ErrorCode_OK);
    printf("✓ Saved 3 holidays\n");

    // =========================================================================
    // PHASE 8: Create and Save Cards
    // =========================================================================
    print_header("PHASE 8: Create and Save Cards");

    CardRecord_t card1 = {
        .card_number = 100001,
        .permission_id = 100,
        .card_holder_name = "John Doe",
        .activation_date = 1704067200,
        .expiration_date = 1735689599,
        .is_active = true,
        .pin = 1234
    };

    result = CardDatabase_AddCard(&card1);
    assert(result == ErrorCode_OK);
    printf("✓ Saved Card 100001 (John Doe)\n");

    CardRecord_t card2 = {
        .card_number = 200001,
        .permission_id = 100,
        .card_holder_name = "Jane Smith",
        .activation_date = 0,
        .expiration_date = 0,
        .is_active = true,
        .pin = 0
    };

    result = CardDatabase_AddCard(&card2);
    assert(result == ErrorCode_OK);
    printf("✓ Saved Card 200001 (Jane Smith)\n");

    // =========================================================================
    // PHASE 9: Destroy In-Memory Objects
    // =========================================================================
    print_header("PHASE 9: Destroy In-Memory Objects (Simulate Restart)");

    Permission_Destroy(perm1);
    TimeZone_Destroy(tz1);
    free(relay_obj1);
    free(reader_obj1);
    GroupList_Destroy(group_list);
    Holiday_Clear();

    printf("✓ All in-memory objects destroyed\n");
    printf("  (Simulating system restart)\n");

    // =========================================================================
    // PHASE 10: Load Permission from Database
    // =========================================================================
    print_header("PHASE 10: Load Permission from Database");

    Permission_t* loaded_perm = Permission_LoadFromDB(100);
    assert(loaded_perm != NULL);
    assert(loaded_perm->Id == 100);
    assert(loaded_perm->ActivationDateTime == 1704067200);
    assert(loaded_perm->DeactivationDateTime == 1735689599);
    assert(loaded_perm->PermissionEntryList->count == 2);
    assert(loaded_perm->ExclusionEntryList->count == 1);
    printf("✓ Loaded Permission 100\n");
    printf("  - Entries: %d\n", loaded_perm->PermissionEntryList->count);
    printf("  - Exclusions: %d\n", loaded_perm->ExclusionEntryList->count);

    // Verify entry details
    PermissionEntry_t* loaded_entry = (PermissionEntry_t*)loaded_perm->PermissionEntryList->data[0];
    assert(loaded_entry->AccessObject.type == LPAType_Reader);
    assert(loaded_entry->AccessObject.id == 1);
    assert(loaded_entry->TimeZone == 100);
    printf("  - Entry 1: Reader 1, TimeZone 100 ✓\n");

    Permission_Destroy(loaded_perm);

    // =========================================================================
    // PHASE 11: Load TimeZone from Database
    // =========================================================================
    print_header("PHASE 11: Load TimeZone from Database");

    TimeZone_t* loaded_tz = TimeZone_LoadFromDB(100);
    assert(loaded_tz != NULL);
    assert(loaded_tz->Id == 100);
    assert(loaded_tz->TimeIntervalList->count == 1);
    printf("✓ Loaded TimeZone 100\n");

    TimeInterval_t* loaded_interval = (TimeInterval_t*)loaded_tz->TimeIntervalList->data[0];
    assert(loaded_interval->StartTime == Time_FromHMS(8, 0, 0));
    assert(loaded_interval->EndTime == Time_FromHMS(18, 0, 0));
    assert(loaded_interval->Recurrence == RecurrenceType_Cyclic);
    printf("  - Interval: 8:00 AM - 6:00 PM, Cyclic (Mon-Fri) ✓\n");

    TimeZone_Destroy(loaded_tz);

    // =========================================================================
    // PHASE 12: Load Relay from Database
    // =========================================================================
    print_header("PHASE 12: Load Relay from Database");

    Relay_t* loaded_relay = Relay_LoadFromDB(relay1);
    assert(loaded_relay != NULL);
    assert(loaded_relay->PulseDuration == 100);
    assert(loaded_relay->CtrlTimeZone == 100);
    assert(loaded_relay->Flags == RelayFlags_OnWhileTZActive);
    assert(loaded_relay->Mode == RelayMode_Auto);
    printf("✓ Loaded Relay 1\n");
    printf("  - Pulse Duration: %d (1.0 sec)\n", loaded_relay->PulseDuration);
    printf("  - Control TimeZone: %d\n", loaded_relay->CtrlTimeZone);

    free(loaded_relay);

    // =========================================================================
    // PHASE 13: Load Reader from Database
    // =========================================================================
    print_header("PHASE 13: Load Reader from Database");

    Reader_t* loaded_reader = Reader_LoadFromDB(reader1);
    assert(loaded_reader != NULL);
    assert(loaded_reader->InitMode == ReaderMode_CardOnly);
    assert(loaded_reader->Flags == ReaderFlags_APBEnabled);
    printf("✓ Loaded Reader 1\n");
    printf("  - Mode: %d (CardOnly)\n", loaded_reader->InitMode);
    printf("  - APB Enabled: %s\n", (loaded_reader->Flags & ReaderFlags_APBEnabled) ? "YES" : "NO");

    free(loaded_reader);

    // =========================================================================
    // PHASE 14: Load GroupList from Database
    // =========================================================================
    print_header("PHASE 14: Load GroupList from Database");

    GroupList_t* loaded_group_list = GroupList_LoadFromDB(group_list_lpa);
    assert(loaded_group_list != NULL);
    assert(loaded_group_list->Count == 3);
    printf("✓ Loaded GroupList 1\n");
    printf("  - Group count: %d\n", loaded_group_list->Count);

    // Groups is a static array, not a Vector
    assert(loaded_group_list->Groups[0] == 100);
    printf("  - Group 1: %d ✓\n", loaded_group_list->Groups[0]);

    GroupList_Destroy(loaded_group_list);

    // =========================================================================
    // PHASE 15: Load Holidays from Database
    // =========================================================================
    print_header("PHASE 15: Load Holidays from Database");

    int holiday_count = Holiday_LoadAllFromDB();
    assert(holiday_count == 3);
    printf("✓ Loaded %d holidays\n", holiday_count);

    assert(Holiday_IsHoliday(20251225));
    assert(Holiday_IsHoliday(20250101));
    assert(Holiday_IsHoliday(20250704));
    printf("  - Christmas (12/25/2025) ✓\n");
    printf("  - New Year's (01/01/2025) ✓\n");
    printf("  - Independence Day (07/04/2025) ✓\n");

    // =========================================================================
    // PHASE 16: Load Cards from Database
    // =========================================================================
    print_header("PHASE 16: Load Cards from Database");

    CardRecord_t loaded_card;
    result = CardDatabase_GetCard(100001, &loaded_card);
    assert(result == ErrorCode_OK);
    assert(loaded_card.permission_id == 100);
    assert(strcmp(loaded_card.card_holder_name, "John Doe") == 0);
    assert(loaded_card.pin == 1234);
    printf("✓ Loaded Card 100001 (John Doe)\n");
    printf("  - Permission ID: %d\n", loaded_card.permission_id);
    printf("  - PIN: ****\n");

    // Test fast lookup
    uint32_t perm_id = CardDatabase_GetPermissionForCard(100001);
    assert(perm_id == 100);
    printf("✓ Fast lookup: Card 100001 -> Permission %d\n", perm_id);

    // Test PIN validation
    bool pin_valid = CardDatabase_ValidatePIN(100001, 1234);
    assert(pin_valid == true);
    printf("✓ PIN validation successful\n");

    // =========================================================================
    // PHASE 17: Bulk Load Operations
    // =========================================================================
    print_header("PHASE 17: Bulk Load Operations");

    Permission_t* all_perms[10];
    int perm_count = Permission_LoadAllFromDB(all_perms, 10);
    assert(perm_count == 1);
    printf("✓ Loaded %d permissions\n", perm_count);
    Permission_Destroy(all_perms[0]);

    TimeZone_t* all_tzs[10];
    int tz_count = TimeZone_LoadAllFromDB(all_tzs, 10);
    assert(tz_count == 4);  // 3 default timezones (0,1,2) + 1 user-created (100)
    printf("✓ Loaded %d timezones (including 3 defaults)\n", tz_count);
    for (int i = 0; i < tz_count; i++) {
        TimeZone_Destroy(all_tzs[i]);
    }

    CardRecord_t all_cards[10];
    int card_count = CardDatabase_LoadAllCards(all_cards, 10);
    assert(card_count == 2);
    printf("✓ Loaded %d cards\n", card_count);

    // =========================================================================
    // PHASE 18: Update Operations
    // =========================================================================
    print_header("PHASE 18: Update Operations");

    // Update card
    CardRecord_t updated_card = loaded_card;
    updated_card.pin = 5678;
    strcpy(updated_card.card_holder_name, "John Michael Doe");
    result = CardDatabase_UpdateCard(&updated_card);
    assert(result == ErrorCode_OK);
    printf("✓ Updated Card 100001\n");

    // Verify update
    CardRecord_t verify_card;
    result = CardDatabase_GetCard(100001, &verify_card);
    assert(result == ErrorCode_OK);
    assert(verify_card.pin == 5678);
    assert(strcmp(verify_card.card_holder_name, "John Michael Doe") == 0);
    printf("✓ Verified update: PIN changed to ****, Name: %s\n", verify_card.card_holder_name);

    // =========================================================================
    // SUMMARY
    // =========================================================================
    print_header("TEST SUMMARY");

    printf("✓ Database Initialization: PASS\n");
    printf("✓ Permission Persistence: PASS\n");
    printf("✓ TimeZone Persistence: PASS\n");
    printf("✓ Relay Persistence: PASS\n");
    printf("✓ Reader Persistence: PASS\n");
    printf("✓ GroupList Persistence: PASS\n");
    printf("✓ Holiday Persistence: PASS\n");
    printf("✓ Card Persistence: PASS\n");
    printf("✓ Bulk Load Operations: PASS\n");
    printf("✓ Update Operations: PASS\n");

    printf("\n");
    printf("═══════════════════════════════════════════════════════════════\n");
    printf("  ALL TESTS PASSED - Database Persistence Verified!            \n");
    printf("═══════════════════════════════════════════════════════════════\n\n");

    // Cleanup
    SDK_Database_Shutdown();
    CardDatabase_Shutdown();
    Holiday_Clear();

    return 0;
}
