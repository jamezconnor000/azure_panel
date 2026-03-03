#include "json_config.h"
#include "../utils/cJSON.h"
#include "card_database.h"
#include "../sdk_modules/permissions/permission.h"
#include "../sdk_modules/relays/relay.h"
#include "../sdk_modules/readers/reader.h"
#include "../sdk_modules/access_points/access_point.h"
#include "../sdk_modules/areas/area.h"
#include "../sdk_modules/card_formats/card_format.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// Forward declarations for database functions
extern ErrorCode_t AccessPoint_SaveToDB(const AccessPoint_t* access_point);
extern AccessPoint_t* AccessPoint_LoadFromDB(uint32_t id);
extern int AccessPoint_LoadAllFromDB(AccessPoint_t** out_access_points, int max_count);

extern ErrorCode_t Area_SaveToDB(const Area_t* area);
extern Area_t* Area_LoadFromDB(uint32_t id);
extern int Area_LoadAllFromDB(Area_t** out_areas, int max_count);

extern ErrorCode_t CardFormat_SaveToDB(const CardFormat_t* format);
extern CardFormat_t* CardFormat_LoadFromDB(uint8_t id);
extern int CardFormat_LoadAllFromDB(CardFormat_t** out_formats, int max_count);

extern ErrorCode_t CardFormatList_SaveToDB(const CardFormatList_t* list);
extern CardFormatList_t* CardFormatList_LoadFromDB(uint8_t id);

extern ErrorCode_t Permission_SaveToDB(const Permission_t* permission);
extern Permission_t* Permission_LoadFromDB(uint32_t id);
extern int Permission_LoadAllFromDB(Permission_t** out_permissions, int max_count);

extern ErrorCode_t Reader_SaveToDB(const Reader_t* reader);
extern Reader_t* Reader_LoadFromDB(LPA_t lpa);
extern int Reader_LoadAllFromDB(Reader_t** out_readers, int max_count);

extern ErrorCode_t Relay_SaveToDB(const Relay_t* relay);
extern Relay_t* Relay_LoadFromDB(LPA_t lpa);
extern int Relay_LoadAllFromDB(Relay_t** out_relays, int max_count);

// =============================================================================
// Helper Functions
// =============================================================================

static cJSON* LPA_ToJSON(LPA_t lpa) {
    cJSON* lpa_json = cJSON_CreateObject();
    cJSON_AddNumberToObject(lpa_json, "Type", lpa.type);
    cJSON_AddNumberToObject(lpa_json, "Node", lpa.node_id);
    cJSON_AddNumberToObject(lpa_json, "LDA", lpa.id & 0xFF);
    cJSON_AddNumberToObject(lpa_json, "Instance", 0);
    return lpa_json;
}

static LPA_t JSON_ToLPA(cJSON* lpa_json) {
    LPA_t lpa = {0};
    if (lpa_json) {
        cJSON* type = cJSON_GetObjectItem(lpa_json, "Type");
        cJSON* node = cJSON_GetObjectItem(lpa_json, "Node");
        cJSON* lda = cJSON_GetObjectItem(lpa_json, "LDA");

        if (type) lpa.type = type->valueint;
        if (node) lpa.node_id = node->valueint;
        if (lda) lpa.id = lda->valueint;
    }
    return lpa;
}

// =============================================================================
// Export Functions
// =============================================================================

static cJSON* Export_AccessPoints() {
    cJSON* access_points = cJSON_CreateObject();

    AccessPoint_t* aps[100];
    int ap_count = AccessPoint_LoadAllFromDB(aps, 100);

    for (int i = 0; i < ap_count; i++) {
        AccessPoint_t* ap = aps[i];
        char ap_name[32];
        snprintf(ap_name, sizeof(ap_name), "Door %u", ap->id);

        cJSON* ap_json = cJSON_CreateObject();
        cJSON_AddItemToObject(ap_json, "Id", LPA_ToJSON(ap->lpa));
        cJSON_AddNumberToObject(ap_json, "InitMode", ap->init_mode);
        cJSON_AddNumberToObject(ap_json, "ShortStrikeTime", ap->short_strike_time);
        cJSON_AddNumberToObject(ap_json, "LongStrikeTime", ap->long_strike_time);
        cJSON_AddNumberToObject(ap_json, "ShortHeldOpenTime", ap->short_held_open_time);
        cJSON_AddNumberToObject(ap_json, "LongHeldOpenTime", ap->long_held_open_time);
        cJSON_AddItemToObject(ap_json, "AreaA", LPA_ToJSON(ap->area_a));
        cJSON_AddItemToObject(ap_json, "AreaB", LPA_ToJSON(ap->area_b));

        cJSON* strikes_array = cJSON_CreateArray();
        for (int j = 0; j < ap->strike_count; j++) {
            cJSON* strike = LPA_ToJSON(ap->strikes[j].strike_lpa);
            cJSON_AddItemToArray(strikes_array, strike);
        }
        cJSON_AddItemToObject(ap_json, "StrikeList", strikes_array);

        cJSON* strikes_to_add = cJSON_CreateArray();
        for (int j = 0; j < ap->strike_count; j++) {
            cJSON_AddItemToArray(strikes_to_add, cJSON_CreateNumber(j));
        }
        cJSON_AddItemToObject(ap_json, "StrikesToAdd", strikes_to_add);

        cJSON_AddItemToObject(access_points, ap_name, ap_json);
        AccessPoint_Destroy(ap);
    }

    return access_points;
}

static cJSON* Export_Areas() {
    cJSON* areas = cJSON_CreateObject();

    Area_t* area_list[100];
    int area_count = Area_LoadAllFromDB(area_list, 100);

    for (int i = 0; i < area_count; i++) {
        Area_t* area = area_list[i];

        cJSON* area_json = cJSON_CreateObject();
        cJSON_AddItemToObject(area_json, "Id", LPA_ToJSON(area->lpa));
        cJSON_AddNumberToObject(area_json, "TimedAPB", area->timed_apb);
        cJSON_AddNumberToObject(area_json, "MinOccupancy", area->min_occupancy);
        cJSON_AddNumberToObject(area_json, "MaxOccupancy", area->max_occupancy);
        cJSON_AddNumberToObject(area_json, "OccupancyLimit", area->occupancy_limit);
        cJSON_AddNumberToObject(area_json, "MinRequiredOccupancy", area->min_required_occupancy);

        const char* area_name = strlen(area->name) > 0 ? area->name : "Unknown Area";
        cJSON_AddItemToObject(areas, area_name, area_json);
        Area_Destroy(area);
    }

    return areas;
}

static cJSON* Export_CardFormats() {
    cJSON* formats = cJSON_CreateArray();

    CardFormat_t* format_list[100];
    int format_count = CardFormat_LoadAllFromDB(format_list, 100);

    for (int i = 0; i < format_count; i++) {
        CardFormat_t* format = format_list[i];

        cJSON* format_json = cJSON_CreateObject();
        cJSON_AddNumberToObject(format_json, "Id", format->id);
        cJSON_AddStringToObject(format_json, "Name", format->name);
        cJSON_AddNumberToObject(format_json, "TotalBits", format->total_bits);
        cJSON_AddNumberToObject(format_json, "FacilityStartBit", format->facility_start_bit);
        cJSON_AddNumberToObject(format_json, "FacilityBitLength", format->facility_bit_length);
        cJSON_AddNumberToObject(format_json, "CardStartBit", format->card_start_bit);
        cJSON_AddNumberToObject(format_json, "CardBitLength", format->card_bit_length);

        cJSON_AddItemToArray(formats, format_json);
        CardFormat_Destroy(format);
    }

    return formats;
}

static cJSON* Export_Cards() {
    cJSON* cards = cJSON_CreateArray();

    CardRecord_t card_list[1000];
    int card_count = CardDatabase_LoadAllCards(card_list, 1000);

    for (int i = 0; i < card_count; i++) {
        CardRecord_t* card = &card_list[i];

        cJSON* card_json = cJSON_CreateObject();
        cJSON_AddNumberToObject(card_json, "CardId", card->card_number);

        cJSON* fields = cJSON_CreateArray();

        // Add permission field
        cJSON* perm_field = cJSON_CreateObject();
        cJSON* perm_array = cJSON_CreateArray();
        char perm_str[16];
        snprintf(perm_str, sizeof(perm_str), "%u", card->permission_id);
        cJSON_AddItemToArray(perm_array, cJSON_CreateString(perm_str));
        cJSON_AddItemToObject(perm_field, "Permission", perm_array);
        cJSON_AddItemToArray(fields, perm_field);

        cJSON_AddItemToObject(card_json, "Fields", fields);
        cJSON_AddItemToArray(cards, card_json);
    }

    return cards;
}

static cJSON* Export_PermissionEntries() {
    cJSON* perm_entries = cJSON_CreateArray();

    Permission_t* perms[1000];
    int perm_count = Permission_LoadAllFromDB(perms, 1000);

    for (int i = 0; i < perm_count; i++) {
        Permission_t* perm = perms[i];

        if (perm->PermissionEntryList && perm->PermissionEntryList->count > 0) {
            for (uint32_t j = 0; j < perm->PermissionEntryList->count; j++) {
                PermissionEntry_t* entry = (PermissionEntry_t*)perm->PermissionEntryList->data[j];

                cJSON* entry_json = cJSON_CreateObject();
                cJSON_AddItemToObject(entry_json, "AccessObject", LPA_ToJSON(entry->AccessObject));
                cJSON_AddNumberToObject(entry_json, "TimeZone", entry->TimeZone);
                cJSON_AddItemToObject(entry_json, "StrikeId", LPA_ToJSON(entry->Strike));
                cJSON_AddNumberToObject(entry_json, "OverridePermissionFlagsMask", entry->OverridePermissionFlagsMask);
                cJSON_AddNumberToObject(entry_json, "OverridePermissionFlags", entry->OverridePermissionFlags);

                cJSON_AddItemToArray(perm_entries, entry_json);
            }
        }

        Permission_Destroy(perm);
    }

    return perm_entries;
}

static cJSON* Export_ReaderSettings() {
    cJSON* readers = cJSON_CreateObject();

    Reader_t* reader_list[100];
    int reader_count = Reader_LoadAllFromDB(reader_list, 100);

    for (int i = 0; i < reader_count; i++) {
        Reader_t* reader = reader_list[i];

        cJSON* reader_json = cJSON_CreateObject();
        cJSON_AddItemToObject(reader_json, "Id", LPA_ToJSON(reader->Id));
        cJSON_AddNumberToObject(reader_json, "InitMode", reader->InitMode);
        cJSON_AddNumberToObject(reader_json, "Flags", reader->Flags);
        cJSON_AddStringToObject(reader_json, "Type", "Wiegand");

        char reader_name[32];
        snprintf(reader_name, sizeof(reader_name), "RDR%u", reader->Id.id);
        cJSON_AddItemToObject(readers, reader_name, reader_json);
        Reader_Destroy(reader);
    }

    return readers;
}

static cJSON* Export_RelaySettings() {
    cJSON* relays = cJSON_CreateObject();

    Relay_t* relay_list[100];
    int relay_count = Relay_LoadAllFromDB(relay_list, 100);

    for (int i = 0; i < relay_count; i++) {
        Relay_t* relay = relay_list[i];

        cJSON* relay_json = cJSON_CreateObject();
        cJSON_AddItemToObject(relay_json, "Id", LPA_ToJSON(relay->Id));
        cJSON_AddNumberToObject(relay_json, "PulseDuration", relay->PulseDuration);
        cJSON_AddNumberToObject(relay_json, "CtrlTimeZone", relay->CtrlTimeZone);
        cJSON_AddNumberToObject(relay_json, "Flags", relay->Flags);
        cJSON_AddNumberToObject(relay_json, "Mode", relay->Mode);

        char relay_name[32];
        snprintf(relay_name, sizeof(relay_name), "OUT%u", relay->Id.id);
        cJSON_AddItemToObject(relays, relay_name, relay_json);
        Relay_Destroy(relay);
    }

    return relays;
}

ErrorCode_t HAL_ExportToJSONString(char** out_json) {
    if (!out_json) return ErrorCode_BadParams;

    cJSON* root = cJSON_CreateObject();

    // Add config type
    cJSON_AddStringToObject(root, "ConfigType", "IC2");

    // Export all components
    cJSON_AddItemToObject(root, "AccessPoints", Export_AccessPoints());
    cJSON_AddItemToObject(root, "Areas", Export_Areas());
    cJSON_AddItemToObject(root, "CardFormats", Export_CardFormats());
    cJSON_AddItemToObject(root, "Cards", Export_Cards());
    cJSON_AddItemToObject(root, "PermissionEntries", Export_PermissionEntries());
    cJSON_AddItemToObject(root, "ReaderSettings", Export_ReaderSettings());
    cJSON_AddItemToObject(root, "RelaySettings", Export_RelaySettings());

    // Add empty objects for components we don't yet support
    cJSON_AddItemToObject(root, "InputThresholds", cJSON_CreateObject());
    cJSON_AddItemToObject(root, "COMPortSettings", cJSON_CreateObject());
    cJSON_AddItemToObject(root, "DownstreamBoards", cJSON_CreateArray());
    cJSON_AddItemToObject(root, "Strikes", cJSON_CreateArray());
    cJSON_AddItemToObject(root, "BoardAddressToAccessPoint", cJSON_CreateObject());

    *out_json = cJSON_Print(root);
    cJSON_Delete(root);

    return ErrorCode_OK;
}

ErrorCode_t HAL_ExportToJSON(const char* output_file) {
    if (!output_file) return ErrorCode_BadParams;

    char* json_string = NULL;
    ErrorCode_t result = HAL_ExportToJSONString(&json_string);

    if (result != ErrorCode_OK) {
        return result;
    }

    FILE* fp = fopen(output_file, "w");
    if (!fp) {
        free(json_string);
        return ErrorCode_Database;
    }

    fprintf(fp, "%s", json_string);
    fclose(fp);
    free(json_string);

    printf("✓ Configuration exported to: %s\n", output_file);
    return ErrorCode_OK;
}

// =============================================================================
// Import Functions
// =============================================================================

ErrorCode_t HAL_ImportFromJSONString(const char* json_string) {
    if (!json_string) return ErrorCode_BadParams;

    cJSON* root = cJSON_Parse(json_string);
    if (!root) {
        fprintf(stderr, "Error parsing JSON: %s\n", cJSON_GetErrorPtr());
        return ErrorCode_BadParams;
    }

    // Import Access Points
    cJSON* access_points = cJSON_GetObjectItem(root, "AccessPoints");
    if (access_points) {
        cJSON* ap = NULL;
        cJSON_ArrayForEach(ap, access_points) {
            cJSON* id_json = cJSON_GetObjectItem(ap, "Id");
            LPA_t lpa = JSON_ToLPA(id_json);

            AccessPoint_t* access_point = AccessPoint_Create(lpa.id);
            access_point->lpa = lpa;

            cJSON* mode = cJSON_GetObjectItem(ap, "InitMode");
            if (mode) access_point->init_mode = mode->valueint;

            cJSON* short_strike = cJSON_GetObjectItem(ap, "ShortStrikeTime");
            if (short_strike) access_point->short_strike_time = short_strike->valueint;

            cJSON* long_strike = cJSON_GetObjectItem(ap, "LongStrikeTime");
            if (long_strike) access_point->long_strike_time = long_strike->valueint;

            cJSON* area_a = cJSON_GetObjectItem(ap, "AreaA");
            if (area_a) access_point->area_a = JSON_ToLPA(area_a);

            cJSON* area_b = cJSON_GetObjectItem(ap, "AreaB");
            if (area_b) access_point->area_b = JSON_ToLPA(area_b);

            AccessPoint_SaveToDB(access_point);
            AccessPoint_Destroy(access_point);
        }
    }

    // Import Areas
    cJSON* areas = cJSON_GetObjectItem(root, "Areas");
    if (areas) {
        cJSON* area_json = NULL;
        cJSON_ArrayForEach(area_json, areas) {
            cJSON* id_json = cJSON_GetObjectItem(area_json, "Id");
            LPA_t lpa = JSON_ToLPA(id_json);

            Area_t* area = Area_Create(lpa.id);
            area->lpa = lpa;

            cJSON* timed_apb = cJSON_GetObjectItem(area_json, "TimedAPB");
            if (timed_apb) area->timed_apb = timed_apb->valueint;

            Area_SaveToDB(area);
            Area_Destroy(area);
        }
    }

    // Import Card Formats
    cJSON* card_formats = cJSON_GetObjectItem(root, "CardFormats");
    if (card_formats) {
        cJSON* format_json = NULL;
        cJSON_ArrayForEach(format_json, card_formats) {
            cJSON* id = cJSON_GetObjectItem(format_json, "Id");
            if (!id) continue;

            CardFormat_t* format = CardFormat_Create(id->valueint);

            cJSON* total_bits = cJSON_GetObjectItem(format_json, "TotalBits");
            if (total_bits) format->total_bits = total_bits->valueint;

            CardFormat_SaveToDB(format);
            CardFormat_Destroy(format);
        }
    }

    cJSON_Delete(root);
    printf("✓ Configuration imported successfully\n");
    return ErrorCode_OK;
}

ErrorCode_t HAL_ImportFromJSON(const char* input_file) {
    if (!input_file) return ErrorCode_BadParams;

    FILE* fp = fopen(input_file, "r");
    if (!fp) {
        fprintf(stderr, "Error opening file: %s\n", input_file);
        return ErrorCode_Database;
    }

    fseek(fp, 0, SEEK_END);
    long file_size = ftell(fp);
    fseek(fp, 0, SEEK_SET);

    char* json_string = (char*)malloc(file_size + 1);
    if (!json_string) {
        fclose(fp);
        return ErrorCode_BadParams;
    }

    fread(json_string, 1, file_size, fp);
    json_string[file_size] = '\0';
    fclose(fp);

    ErrorCode_t result = HAL_ImportFromJSONString(json_string);
    free(json_string);

    return result;
}
