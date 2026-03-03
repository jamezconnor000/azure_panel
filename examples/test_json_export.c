#include "../src/hal_core/json_config.h"
#include "../src/hal_core/card_database.h"
#include "../src/sdk_modules/common/sdk_database.h"
#include "../src/sdk_modules/access_points/access_point.h"
#include "../src/sdk_modules/areas/area.h"
#include "../src/sdk_modules/card_formats/card_format.h"
#include <stdio.h>
#include <stdlib.h>

int main() {
    printf("\n");
    printf("╔══════════════════════════════════════════════════════════════╗\n");
    printf("║                                                              ║\n");
    printf("║         JSON EXPORT/IMPORT TEST                             ║\n");
    printf("║         IntegrationApp Compatibility Demo                   ║\n");
    printf("║                                                              ║\n");
    printf("╚══════════════════════════════════════════════════════════════╝\n");
    printf("\n");

    // Initialize databases
    SDK_Database_Initialize("test_json_export.db");
    CardDatabase_Initialize("test_json_export.db");

    // Apply schema
    printf("Applying database schema...\n");
    system("sqlite3 test_json_export.db < ./schema/sdk_tables.sql 2>&1");
    printf("✓ Schema applied\n\n");

    // =============================================================================
    // Create Sample Data
    // =============================================================================

    printf("Creating sample configuration...\n");

    // Create Access Point
    AccessPoint_t* ap = AccessPoint_Create(1);
    AccessPoint_SetMode(ap, AccessPointMode_CardOnly);
    ap->short_strike_time = 5;
    ap->long_strike_time = 10;

    // Create Areas
    Area_t* area1 = Area_Create(1);
    Area_SetName(area1, "Lobby");
    Area_SetTimedAPB(area1, 5);

    Area_t* area2 = Area_Create(2);
    Area_SetName(area2, "SecureZone");
    Area_SetTimedAPB(area2, 10);

    AccessPoint_SetAreas(ap, area1->lpa, area2->lpa);

    // Create Card Format (26-bit Wiegand)
    CardFormat_t* format = CardFormat_Create(1);
    snprintf(format->name, sizeof(format->name), "26-bit Wiegand");
    CardFormat_SetWiegand(format, 26, 1, 8, 9, 16);

    // Create Card Format List
    CardFormatList_t* format_list = CardFormatList_Create(1);
    CardFormatList_AddFormat(format_list, 1);

    // Create Permission
    Permission_t* perm = Permission_Create(100);
    perm->ActivationDateTime = 0;
    perm->DeactivationDateTime = 0;

    // Create Reader
    Reader_t* reader = Reader_Create((LPA_t){LPAType_Reader, 5, 0});
    reader->InitMode = ReaderMode_CardOnly;
    reader->Flags = ReaderFlags_APBEnabled;

    // Create Relay
    Relay_t* relay = Relay_Create((LPA_t){LPAType_Relay, 1, 0});
    relay->PulseDuration = 100;
    relay->Mode = RelayMode_Auto;

    // Create Cards
    CardRecord_t card1 = {
        .card_number = 100001,
        .permission_id = 100,
        .activation_date = 0,
        .expiration_date = 0,
        .is_active = true,
        .pin = 1234
    };
    snprintf(card1.card_holder_name, sizeof(card1.card_holder_name), "John Doe");

    CardRecord_t card2 = {
        .card_number = 200001,
        .permission_id = 100,
        .activation_date = 0,
        .expiration_date = 0,
        .is_active = true,
        .pin = 5678
    };
    snprintf(card2.card_holder_name, sizeof(card2.card_holder_name), "Jane Smith");

    // Save to database
    printf("Saving to database...\n");
    AccessPoint_SaveToDB(ap);
    Area_SaveToDB(area1);
    Area_SaveToDB(area2);
    CardFormat_SaveToDB(format);
    CardFormatList_SaveToDB(format_list);
    Permission_SaveToDB(perm);
    Reader_SaveToDB(reader);
    Relay_SaveToDB(relay);
    CardDatabase_AddCard(&card1);
    CardDatabase_AddCard(&card2);

    printf("✓ Sample data created\n\n");

    // =============================================================================
    // Export to JSON
    // =============================================================================

    printf("Exporting to JSON...\n");
    ErrorCode_t result = HAL_ExportToJSON("config_export.json");
    if (result != ErrorCode_OK) {
        fprintf(stderr, "✗ Export failed\n");
        return 1;
    }
    printf("\n");

    // =============================================================================
    // Display JSON Preview
    // =============================================================================

    printf("JSON Export Preview (first 50 lines):\n");
    printf("─────────────────────────────────────\n");
    system("head -50 config_export.json");
    printf("─────────────────────────────────────\n\n");

    // =============================================================================
    // Test Import (create new database and import)
    // =============================================================================

    printf("Testing import functionality...\n");
    SDK_Database_Shutdown();
    CardDatabase_Shutdown();

    // Create new database
    system("rm -f test_json_import.db");
    SDK_Database_Initialize("test_json_import.db");
    CardDatabase_Initialize("test_json_import.db");
    system("sqlite3 test_json_import.db < ./schema/sdk_tables.sql 2>&1 > /dev/null");

    // Import from JSON
    result = HAL_ImportFromJSON("config_export.json");
    if (result != ErrorCode_OK) {
        fprintf(stderr, "✗ Import failed\n");
        return 1;
    }

    // Verify imported data
    printf("\nVerifying imported data...\n");
    AccessPoint_t* imported_ap = AccessPoint_LoadFromDB(1);
    if (imported_ap) {
        printf("✓ Access Point imported: ID=%u, Mode=%d\n", imported_ap->id, imported_ap->init_mode);
        AccessPoint_Destroy(imported_ap);
    }

    Area_t* imported_area = Area_LoadFromDB(1);
    if (imported_area) {
        printf("✓ Area imported: %s (TimedAPB=%u min)\n", imported_area->name, imported_area->timed_apb);
        Area_Destroy(imported_area);
    }

    CardFormat_t* imported_format = CardFormat_LoadFromDB(1);
    if (imported_format) {
        printf("✓ Card Format imported: %s (%u bits)\n", imported_format->name, imported_format->total_bits);
        CardFormat_Destroy(imported_format);
    }

    // Cleanup
    AccessPoint_Destroy(ap);
    Area_Destroy(area1);
    Area_Destroy(area2);
    CardFormat_Destroy(format);
    CardFormatList_Destroy(format_list);
    Permission_Destroy(perm);
    Reader_Destroy(reader);
    Relay_Destroy(relay);

    SDK_Database_Shutdown();
    CardDatabase_Shutdown();

    printf("\n");
    printf("═══════════════════════════════════════════════════════════════\n");
    printf("  JSON Export/Import Test Complete!                            \n");
    printf("  Output file: config_export.json                              \n");
    printf("═══════════════════════════════════════════════════════════════\n");
    printf("\n");

    return 0;
}
