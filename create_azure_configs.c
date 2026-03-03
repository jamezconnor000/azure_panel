#include "src/hal_core/json_config.h"
#include "src/hal_core/card_database.h"
#include "src/sdk_modules/common/sdk_database.h"
#include "src/sdk_modules/access_points/access_point.h"
#include "src/sdk_modules/areas/area.h"
#include "src/sdk_modules/card_formats/card_format.h"
#include "src/sdk_modules/permissions/permission.h"
#include "src/sdk_modules/readers/reader.h"
#include "src/sdk_modules/relays/relay.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

void create_basic_config(const char* output_file) {
    printf("Creating basic configuration: %s\n", output_file);

    // Initialize databases
    SDK_Database_Initialize("temp_basic.db");
    CardDatabase_Initialize("temp_basic.db");
    system("sqlite3 temp_basic.db < ./schema/sdk_tables.sql 2>&1 > /dev/null");

    // Create 2 access points (Front Door, Back Door)
    AccessPoint_t* front_door = AccessPoint_Create(1);
    front_door->lpa.type = LPAType_AccessPoint;
    front_door->lpa.id = 1;
    front_door->lpa.node_id = 1;
    front_door->init_mode = AccessPointMode_CardOnly;
    front_door->short_strike_time = 5;
    front_door->long_strike_time = 10;
    AccessPoint_SaveToDB(front_door);

    AccessPoint_t* back_door = AccessPoint_Create(2);
    back_door->lpa.type = LPAType_AccessPoint;
    back_door->lpa.id = 2;
    back_door->lpa.node_id = 1;
    back_door->init_mode = AccessPointMode_CardAndPIN;
    back_door->short_strike_time = 5;
    back_door->long_strike_time = 10;
    AccessPoint_SaveToDB(back_door);

    // Create 2 areas (Lobby, Office)
    Area_t* lobby = Area_Create(1);
    lobby->lpa.type = LPAType_Area;
    lobby->lpa.id = 1;
    lobby->lpa.node_id = 1;
    Area_SetName(lobby, "Lobby");
    Area_SetTimedAPB(lobby, 5);
    Area_SaveToDB(lobby);

    Area_t* office = Area_Create(2);
    office->lpa.type = LPAType_Area;
    office->lpa.id = 2;
    office->lpa.node_id = 1;
    Area_SetName(office, "Office Area");
    Area_SetTimedAPB(office, 10);
    Area_SaveToDB(office);

    // Create card format (26-bit Wiegand)
    CardFormat_t* format = CardFormat_Create(1);
    strcpy(format->name, "26-bit Wiegand");
    format->type = CardFormatType_Wiegand;
    CardFormat_SetWiegand(format, 26, 1, 8, 9, 16);
    CardFormat_SaveToDB(format);

    // Create 5 employee cards
    for (int i = 1; i <= 5; i++) {
        CardRecord_t card = {0};
        card.card_number = 100000 + i;
        card.permission_id = 100;
        snprintf(card.card_holder_name, sizeof(card.card_holder_name), "Employee %d", i);
        card.activation_date = 0;
        card.expiration_date = 0;
        card.is_active = true;
        card.pin = 0;
        CardDatabase_AddCard(&card);
    }

    // Create readers
    Reader_t* reader1 = Reader_Create((LPA_t){LPAType_Reader, 1, 1});
    Reader_SaveToDB(reader1);

    Reader_t* reader2 = Reader_Create((LPA_t){LPAType_Reader, 2, 1});
    Reader_SaveToDB(reader2);

    // Create relays
    Relay_t* relay1 = Relay_Create((LPA_t){LPAType_Relay, 1, 1});
    relay1->PulseDuration = 100;
    relay1->Mode = RelayMode_Auto;
    Relay_SaveToDB(relay1);

    Relay_t* relay2 = Relay_Create((LPA_t){LPAType_Relay, 2, 1});
    relay2->PulseDuration = 100;
    relay2->Mode = RelayMode_Auto;
    Relay_SaveToDB(relay2);

    // Export to JSON
    HAL_ExportToJSON(output_file);

    // Cleanup
    AccessPoint_Destroy(front_door);
    AccessPoint_Destroy(back_door);
    Area_Destroy(lobby);
    Area_Destroy(office);
    CardFormat_Destroy(format);
    Reader_Destroy(reader1);
    Reader_Destroy(reader2);
    Relay_Destroy(relay1);
    Relay_Destroy(relay2);

    SDK_Database_Shutdown();
    CardDatabase_Shutdown();
}

void create_office_building_config(const char* output_file) {
    printf("Creating office building configuration: %s\n", output_file);

    // Initialize databases
    SDK_Database_Initialize("temp_office.db");
    CardDatabase_Initialize("temp_office.db");
    system("sqlite3 temp_office.db < ./schema/sdk_tables.sql 2>&1 > /dev/null");

    // Create access points for a 3-floor office building
    const char* door_names[] = {
        "Main Entrance", "Lobby Elevator", "1st Floor Office", "1st Floor Server Room",
        "2nd Floor Office", "2nd Floor Conference", "3rd Floor Office", "3rd Floor Executive",
        "Parking Garage", "Roof Access"
    };

    for (int i = 0; i < 10; i++) {
        AccessPoint_t* ap = AccessPoint_Create(i + 1);
        ap->lpa.type = LPAType_AccessPoint;
        ap->lpa.id = i + 1;
        ap->lpa.node_id = 1;

        // Higher security areas require card+PIN
        if (i == 3 || i == 7 || i == 9) {
            ap->init_mode = AccessPointMode_CardAndPIN;
        } else {
            ap->init_mode = AccessPointMode_CardOnly;
        }

        ap->short_strike_time = 5;
        ap->long_strike_time = 10;
        ap->short_held_open_time = 30;
        ap->long_held_open_time = 120;

        AccessPoint_SaveToDB(ap);
        AccessPoint_Destroy(ap);
    }

    // Create areas for APB
    const char* area_names[] = {"Ground Floor", "1st Floor", "2nd Floor", "3rd Floor", "Parking"};
    for (int i = 0; i < 5; i++) {
        Area_t* area = Area_Create(i + 1);
        area->lpa.type = LPAType_Area;
        area->lpa.id = i + 1;
        area->lpa.node_id = 1;
        Area_SetName(area, area_names[i]);
        Area_SetTimedAPB(area, 15);
        Area_SetOccupancyLimits(area, 0, 100, 90, 0);
        Area_SaveToDB(area);
        Area_Destroy(area);
    }

    // Create multiple card formats
    CardFormat_t* format26 = CardFormat_Create(1);
    strcpy(format26->name, "26-bit Wiegand Standard");
    format26->type = CardFormatType_Wiegand;
    CardFormat_SetWiegand(format26, 26, 1, 8, 9, 16);
    CardFormat_SaveToDB(format26);
    CardFormat_Destroy(format26);

    CardFormat_t* format37 = CardFormat_Create(2);
    strcpy(format37->name, "37-bit H10304");
    format37->type = CardFormatType_Wiegand;
    CardFormat_SetWiegand(format37, 37, 1, 16, 17, 19);
    CardFormat_SaveToDB(format37);
    CardFormat_Destroy(format37);

    // Create 50 employee cards
    for (int i = 1; i <= 50; i++) {
        CardRecord_t card = {0};
        card.card_number = 200000 + i;
        card.permission_id = 100 + (i % 10); // Varied permissions
        snprintf(card.card_holder_name, sizeof(card.card_holder_name), "Office Employee %d", i);
        card.activation_date = 0;
        card.expiration_date = 0;
        card.is_active = true;
        card.pin = (i <= 10) ? (1000 + i) : 0; // First 10 have PINs
        CardDatabase_AddCard(&card);
    }

    // Create readers for each door
    for (int i = 1; i <= 10; i++) {
        Reader_t* reader = Reader_Create((LPA_t){LPAType_Reader, i, 1});
        Reader_SaveToDB(reader);
        Reader_Destroy(reader);

        Relay_t* relay = Relay_Create((LPA_t){LPAType_Relay, i, 1});
        relay->PulseDuration = 100;
        relay->Mode = RelayMode_Auto;
        Relay_SaveToDB(relay);
        Relay_Destroy(relay);
    }

    // Export to JSON
    HAL_ExportToJSON(output_file);

    SDK_Database_Shutdown();
    CardDatabase_Shutdown();
}

void create_warehouse_config(const char* output_file) {
    printf("Creating warehouse/industrial configuration: %s\n", output_file);

    // Initialize databases
    SDK_Database_Initialize("temp_warehouse.db");
    CardDatabase_Initialize("temp_warehouse.db");
    system("sqlite3 temp_warehouse.db < ./schema/sdk_tables.sql 2>&1 > /dev/null");

    // Create access points for warehouse
    const char* door_names[] = {
        "Front Office Entry", "Warehouse Floor Entry", "Loading Dock 1",
        "Loading Dock 2", "Parts Storage", "Hazmat Storage",
        "Tool Cage", "Employee Break Room"
    };

    for (int i = 0; i < 8; i++) {
        AccessPoint_t* ap = AccessPoint_Create(i + 1);
        ap->lpa.type = LPAType_AccessPoint;
        ap->lpa.id = i + 1;
        ap->lpa.node_id = 1;

        // Hazmat and parts require higher security
        if (i == 4 || i == 5 || i == 6) {
            ap->init_mode = AccessPointMode_CardAndPIN;
        } else {
            ap->init_mode = AccessPointMode_CardOnly;
        }

        ap->short_strike_time = 5;
        ap->long_strike_time = 15;
        ap->short_held_open_time = 45;  // Longer for material transport
        ap->long_held_open_time = 180;

        AccessPoint_SaveToDB(ap);
        AccessPoint_Destroy(ap);
    }

    // Create areas
    const char* area_names[] = {"Office", "Warehouse Floor", "Loading Docks", "Secure Storage"};
    for (int i = 0; i < 4; i++) {
        Area_t* area = Area_Create(i + 1);
        area->lpa.type = LPAType_Area;
        area->lpa.id = i + 1;
        area->lpa.node_id = 1;
        Area_SetName(area, area_names[i]);
        Area_SetTimedAPB(area, 20);
        Area_SaveToDB(area);
        Area_Destroy(area);
    }

    // Create card format
    CardFormat_t* format = CardFormat_Create(1);
    strcpy(format->name, "26-bit Wiegand");
    format->type = CardFormatType_Wiegand;
    CardFormat_SetWiegand(format, 26, 1, 8, 9, 16);
    CardFormat_SaveToDB(format);
    CardFormat_Destroy(format);

    // Create employee cards (25 employees)
    for (int i = 1; i <= 25; i++) {
        CardRecord_t card = {0};
        card.card_number = 300000 + i;
        card.permission_id = 100;
        snprintf(card.card_holder_name, sizeof(card.card_holder_name), "Warehouse Worker %d", i);
        card.activation_date = 0;
        card.expiration_date = 0;
        card.is_active = true;
        card.pin = (i <= 5) ? (2000 + i) : 0; // Supervisors have PINs
        CardDatabase_AddCard(&card);
    }

    // Create readers and relays
    for (int i = 1; i <= 8; i++) {
        Reader_t* reader = Reader_Create((LPA_t){LPAType_Reader, i, 1});
        Reader_SaveToDB(reader);
        Reader_Destroy(reader);

        Relay_t* relay = Relay_Create((LPA_t){LPAType_Relay, i, 1});
        relay->PulseDuration = 150;  // Longer pulse for industrial doors
        relay->Mode = RelayMode_Auto;
        Relay_SaveToDB(relay);
        Relay_Destroy(relay);
    }

    // Export to JSON
    HAL_ExportToJSON(output_file);

    SDK_Database_Shutdown();
    CardDatabase_Shutdown();
}

int main() {
    printf("\n");
    printf("╔══════════════════════════════════════════════════════════════╗\n");
    printf("║                                                              ║\n");
    printf("║     Azure Panel Configuration Generator                     ║\n");
    printf("║     Creating IntegrationApp-Compatible Configs              ║\n");
    printf("║                                                              ║\n");
    printf("╚══════════════════════════════════════════════════════════════╝\n");
    printf("\n");

    // Create configurations
    create_basic_config("/Users/mosley/Documents/AzurePanel_Basic_Config.json");
    create_office_building_config("/Users/mosley/Documents/AzurePanel_OfficeBuilding_Config.json");
    create_warehouse_config("/Users/mosley/Documents/AzurePanel_Warehouse_Config.json");

    printf("\n");
    printf("═══════════════════════════════════════════════════════════════\n");
    printf("  Configuration files created in Documents folder:            \n");
    printf("  - AzurePanel_Basic_Config.json                              \n");
    printf("  - AzurePanel_OfficeBuilding_Config.json                     \n");
    printf("  - AzurePanel_Warehouse_Config.json                          \n");
    printf("═══════════════════════════════════════════════════════════════\n");
    printf("\n");

    // Clean up temporary databases
    remove("temp_basic.db");
    remove("temp_office.db");
    remove("temp_warehouse.db");

    return 0;
}
