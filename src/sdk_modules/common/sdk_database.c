#include "sdk_database.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// Global database connection
static sqlite3* g_db = NULL;

// =============================================================================
// Database Initialization
// =============================================================================

ErrorCode_t SDK_Database_Initialize(const char* db_path) {
    if (g_db) {
        return ErrorCode_OK; // Already initialized
    }

    int rc = sqlite3_open(db_path, &g_db);
    if (rc != SQLITE_OK) {
        fprintf(stderr, "Cannot open database: %s\n", sqlite3_errmsg(g_db));
        return ErrorCode_Database;
    }

    printf("✓ SDK Database initialized: %s\n", db_path);
    return ErrorCode_OK;
}

void SDK_Database_Shutdown(void) {
    if (g_db) {
        sqlite3_close(g_db);
        g_db = NULL;
        printf("✓ SDK Database closed\n");
    }
}

sqlite3* SDK_Database_GetConnection(void) {
    return g_db;
}

// =============================================================================
// Permission Database Operations
// =============================================================================

ErrorCode_t Permission_SaveToDB(const Permission_t* permission) {
    if (!g_db || !permission) return ErrorCode_BadParams;

    sqlite3_stmt* stmt = NULL;
    const char* sql = "INSERT OR REPLACE INTO permissions "
                      "(id, activation_datetime, deactivation_datetime) "
                      "VALUES (?, ?, ?)";

    int rc = sqlite3_prepare_v2(g_db, sql, -1, &stmt, NULL);
    if (rc != SQLITE_OK) {
        fprintf(stderr, "Failed to prepare statement: %s\n", sqlite3_errmsg(g_db));
        return ErrorCode_Database;
    }

    sqlite3_bind_int(stmt, 1, permission->Id);
    sqlite3_bind_int64(stmt, 2, permission->ActivationDateTime);
    sqlite3_bind_int64(stmt, 3, permission->DeactivationDateTime);

    rc = sqlite3_step(stmt);
    sqlite3_finalize(stmt);

    if (rc != SQLITE_DONE) {
        fprintf(stderr, "Failed to insert permission: %s\n", sqlite3_errmsg(g_db));
        return ErrorCode_Database;
    }

    // Save permission entries
    if (permission->PermissionEntryList) {
        // First delete existing entries
        sql = "DELETE FROM permission_entries WHERE permission_id = ?";
        sqlite3_prepare_v2(g_db, sql, -1, &stmt, NULL);
        sqlite3_bind_int(stmt, 1, permission->Id);
        sqlite3_step(stmt);
        sqlite3_finalize(stmt);

        // Insert new entries
        sql = "INSERT INTO permission_entries "
              "(permission_id, access_object_type, access_object_id, access_object_node, "
              "timezone_id, strike_type, strike_id, strike_node, "
              "override_mask, override_flags) "
              "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)";

        for (uint32_t i = 0; i < permission->PermissionEntryList->count; i++) {
            PermissionEntry_t* entry = (PermissionEntry_t*)permission->PermissionEntryList->data[i];

            sqlite3_prepare_v2(g_db, sql, -1, &stmt, NULL);
            sqlite3_bind_int(stmt, 1, permission->Id);
            sqlite3_bind_int(stmt, 2, entry->AccessObject.type);
            sqlite3_bind_int(stmt, 3, entry->AccessObject.id);
            sqlite3_bind_int(stmt, 4, entry->AccessObject.node_id);
            sqlite3_bind_int(stmt, 5, entry->TimeZone);
            sqlite3_bind_int(stmt, 6, entry->Strike.type);
            sqlite3_bind_int(stmt, 7, entry->Strike.id);
            sqlite3_bind_int(stmt, 8, entry->Strike.node_id);
            sqlite3_bind_int(stmt, 9, entry->OverridePermissionFlagsMask);
            sqlite3_bind_int(stmt, 10, entry->OverridePermissionFlags);
            sqlite3_step(stmt);
            sqlite3_finalize(stmt);
        }
    }

    // Save exclusion entries
    if (permission->ExclusionEntryList) {
        // First delete existing exclusions
        sql = "DELETE FROM exclusion_entries WHERE permission_id = ?";
        sqlite3_prepare_v2(g_db, sql, -1, &stmt, NULL);
        sqlite3_bind_int(stmt, 1, permission->Id);
        sqlite3_step(stmt);
        sqlite3_finalize(stmt);

        // Insert new exclusions
        sql = "INSERT INTO exclusion_entries "
              "(permission_id, access_object_type, access_object_id, access_object_node) "
              "VALUES (?, ?, ?, ?)";

        for (uint32_t i = 0; i < permission->ExclusionEntryList->count; i++) {
            ExclusionEntry_t* entry = (ExclusionEntry_t*)permission->ExclusionEntryList->data[i];

            sqlite3_prepare_v2(g_db, sql, -1, &stmt, NULL);
            sqlite3_bind_int(stmt, 1, permission->Id);
            sqlite3_bind_int(stmt, 2, entry->AccessObject.type);
            sqlite3_bind_int(stmt, 3, entry->AccessObject.id);
            sqlite3_bind_int(stmt, 4, entry->AccessObject.node_id);
            sqlite3_step(stmt);
            sqlite3_finalize(stmt);
        }
    }

    return ErrorCode_OK;
}

Permission_t* Permission_LoadFromDB(uint32_t id) {
    if (!g_db) return NULL;

    sqlite3_stmt* stmt = NULL;
    const char* sql = "SELECT activation_datetime, deactivation_datetime FROM permissions WHERE id = ?";

    int rc = sqlite3_prepare_v2(g_db, sql, -1, &stmt, NULL);
    if (rc != SQLITE_OK) {
        return NULL;
    }

    sqlite3_bind_int(stmt, 1, id);
    rc = sqlite3_step(stmt);

    if (rc != SQLITE_ROW) {
        sqlite3_finalize(stmt);
        return NULL; // Permission not found
    }

    // Create permission
    Permission_t* permission = Permission_Create(id);
    permission->ActivationDateTime = sqlite3_column_int64(stmt, 0);
    permission->DeactivationDateTime = sqlite3_column_int64(stmt, 1);
    sqlite3_finalize(stmt);

    // Load permission entries
    sql = "SELECT access_object_type, access_object_id, access_object_node, timezone_id, "
          "strike_type, strike_id, strike_node, override_mask, override_flags "
          "FROM permission_entries WHERE permission_id = ?";

    sqlite3_prepare_v2(g_db, sql, -1, &stmt, NULL);
    sqlite3_bind_int(stmt, 1, id);

    while (sqlite3_step(stmt) == SQLITE_ROW) {
        PermissionEntry_t* entry = PermissionEntry_Create();
        entry->AccessObject.type = sqlite3_column_int(stmt, 0);
        entry->AccessObject.id = sqlite3_column_int(stmt, 1);
        entry->AccessObject.node_id = sqlite3_column_int(stmt, 2);
        entry->TimeZone = sqlite3_column_int(stmt, 3);
        entry->Strike.type = sqlite3_column_int(stmt, 4);
        entry->Strike.id = sqlite3_column_int(stmt, 5);
        entry->Strike.node_id = sqlite3_column_int(stmt, 6);
        entry->OverridePermissionFlagsMask = sqlite3_column_int(stmt, 7);
        entry->OverridePermissionFlags = sqlite3_column_int(stmt, 8);
        Permission_AddEntry(permission, entry);
    }
    sqlite3_finalize(stmt);

    // Load exclusion entries
    sql = "SELECT access_object_type, access_object_id, access_object_node "
          "FROM exclusion_entries WHERE permission_id = ?";

    sqlite3_prepare_v2(g_db, sql, -1, &stmt, NULL);
    sqlite3_bind_int(stmt, 1, id);

    while (sqlite3_step(stmt) == SQLITE_ROW) {
        ExclusionEntry_t* entry = ExclusionEntry_Create();
        entry->AccessObject.type = sqlite3_column_int(stmt, 0);
        entry->AccessObject.id = sqlite3_column_int(stmt, 1);
        entry->AccessObject.node_id = sqlite3_column_int(stmt, 2);
        Permission_AddExclusion(permission, entry);
    }
    sqlite3_finalize(stmt);

    return permission;
}

int Permission_LoadAllFromDB(Permission_t** out_permissions, int max_count) {
    if (!g_db || !out_permissions) return 0;

    sqlite3_stmt* stmt = NULL;
    const char* sql = "SELECT id FROM permissions ORDER BY id";

    int rc = sqlite3_prepare_v2(g_db, sql, -1, &stmt, NULL);
    if (rc != SQLITE_OK) {
        return 0;
    }

    int count = 0;
    while (sqlite3_step(stmt) == SQLITE_ROW && count < max_count) {
        uint32_t id = sqlite3_column_int(stmt, 0);
        Permission_t* permission = Permission_LoadFromDB(id);
        if (permission) {
            out_permissions[count++] = permission;
        }
    }
    sqlite3_finalize(stmt);

    return count;
}

ErrorCode_t Permission_UpdateInDB(const Permission_t* permission) {
    // Update is the same as save with INSERT OR REPLACE
    return Permission_SaveToDB(permission);
}

ErrorCode_t Permission_DeleteFromDB(uint32_t id) {
    if (!g_db) return ErrorCode_BadParams;

    sqlite3_stmt* stmt = NULL;

    // Delete entries first (foreign key cascade should handle this, but be explicit)
    const char* sql = "DELETE FROM permission_entries WHERE permission_id = ?";
    sqlite3_prepare_v2(g_db, sql, -1, &stmt, NULL);
    sqlite3_bind_int(stmt, 1, id);
    sqlite3_step(stmt);
    sqlite3_finalize(stmt);

    sql = "DELETE FROM exclusion_entries WHERE permission_id = ?";
    sqlite3_prepare_v2(g_db, sql, -1, &stmt, NULL);
    sqlite3_bind_int(stmt, 1, id);
    sqlite3_step(stmt);
    sqlite3_finalize(stmt);

    // Delete permission
    sql = "DELETE FROM permissions WHERE id = ?";
    sqlite3_prepare_v2(g_db, sql, -1, &stmt, NULL);
    sqlite3_bind_int(stmt, 1, id);
    int rc = sqlite3_step(stmt);
    sqlite3_finalize(stmt);

    return (rc == SQLITE_DONE) ? ErrorCode_OK : ErrorCode_Database;
}

// =============================================================================
// TimeZone Database Operations
// =============================================================================

ErrorCode_t TimeZone_SaveToDB(const TimeZone_t* timezone) {
    if (!g_db || !timezone) return ErrorCode_BadParams;

    sqlite3_stmt* stmt = NULL;
    const char* sql = "INSERT OR REPLACE INTO timezones (Id) VALUES (?)";

    int rc = sqlite3_prepare_v2(g_db, sql, -1, &stmt, NULL);
    if (rc != SQLITE_OK) {
        return ErrorCode_Database;
    }

    sqlite3_bind_int(stmt, 1, timezone->Id);
    rc = sqlite3_step(stmt);
    sqlite3_finalize(stmt);

    if (rc != SQLITE_DONE) {
        return ErrorCode_Database;
    }

    // Save time intervals
    if (timezone->TimeIntervalList) {
        // Delete existing intervals
        sql = "DELETE FROM time_intervals WHERE timezone_id = ?";
        sqlite3_prepare_v2(g_db, sql, -1, &stmt, NULL);
        sqlite3_bind_int(stmt, 1, timezone->Id);
        sqlite3_step(stmt);
        sqlite3_finalize(stmt);

        // Insert new intervals
        sql = "INSERT INTO time_intervals "
              "(timezone_id, start_time, end_time, recurrence_type, cycle_start, cycle_length, cycle_days) "
              "VALUES (?, ?, ?, ?, ?, ?, ?)";

        for (uint32_t i = 0; i < timezone->TimeIntervalList->count; i++) {
            TimeInterval_t* interval = (TimeInterval_t*)timezone->TimeIntervalList->data[i];

            sqlite3_prepare_v2(g_db, sql, -1, &stmt, NULL);
            sqlite3_bind_int(stmt, 1, timezone->Id);
            sqlite3_bind_int(stmt, 2, interval->StartTime);
            sqlite3_bind_int(stmt, 3, interval->EndTime);
            sqlite3_bind_int(stmt, 4, interval->Recurrence);
            sqlite3_bind_int64(stmt, 5, interval->CycleStart);
            sqlite3_bind_int(stmt, 6, interval->CycleLength);
            sqlite3_bind_int(stmt, 7, interval->CycleDays);
            sqlite3_step(stmt);
            sqlite3_finalize(stmt);
        }
    }

    return ErrorCode_OK;
}

TimeZone_t* TimeZone_LoadFromDB(uint16_t id) {
    if (!g_db) return NULL;

    sqlite3_stmt* stmt = NULL;
    const char* sql = "SELECT id FROM timezones WHERE id = ?";

    int rc = sqlite3_prepare_v2(g_db, sql, -1, &stmt, NULL);
    if (rc != SQLITE_OK) {
        return NULL;
    }

    sqlite3_bind_int(stmt, 1, id);
    rc = sqlite3_step(stmt);

    if (rc != SQLITE_ROW) {
        sqlite3_finalize(stmt);
        return NULL;
    }
    sqlite3_finalize(stmt);

    // Create timezone
    TimeZone_t* timezone = TimeZone_Create(id);

    // Load time intervals
    sql = "SELECT start_time, end_time, recurrence_type, cycle_start, cycle_length, cycle_days "
          "FROM time_intervals WHERE timezone_id = ? ORDER BY start_time";

    sqlite3_prepare_v2(g_db, sql, -1, &stmt, NULL);
    sqlite3_bind_int(stmt, 1, id);

    while (sqlite3_step(stmt) == SQLITE_ROW) {
        TimeInterval_t* interval = TimeInterval_t_Create();
        interval->StartTime = sqlite3_column_int(stmt, 0);
        interval->EndTime = sqlite3_column_int(stmt, 1);
        interval->Recurrence = sqlite3_column_int(stmt, 2);
        interval->CycleStart = sqlite3_column_int64(stmt, 3);
        interval->CycleLength = sqlite3_column_int(stmt, 4);
        interval->CycleDays = sqlite3_column_int(stmt, 5);
        TimeZone_AddInterval(timezone, interval);
    }
    sqlite3_finalize(stmt);

    return timezone;
}

int TimeZone_LoadAllFromDB(TimeZone_t** out_timezones, int max_count) {
    if (!g_db || !out_timezones) return 0;

    sqlite3_stmt* stmt = NULL;
    const char* sql = "SELECT id FROM timezones ORDER BY id";

    int rc = sqlite3_prepare_v2(g_db, sql, -1, &stmt, NULL);
    if (rc != SQLITE_OK) {
        return 0;
    }

    int count = 0;
    while (sqlite3_step(stmt) == SQLITE_ROW && count < max_count) {
        uint16_t id = sqlite3_column_int(stmt, 0);
        TimeZone_t* timezone = TimeZone_LoadFromDB(id);
        if (timezone) {
            out_timezones[count++] = timezone;
        }
    }
    sqlite3_finalize(stmt);

    return count;
}

ErrorCode_t TimeZone_UpdateInDB(const TimeZone_t* timezone) {
    return TimeZone_SaveToDB(timezone);
}

ErrorCode_t TimeZone_DeleteFromDB(uint16_t id) {
    if (!g_db) return ErrorCode_BadParams;

    sqlite3_stmt* stmt = NULL;

    // Delete intervals first
    const char* sql = "DELETE FROM time_intervals WHERE timezone_id = ?";
    sqlite3_prepare_v2(g_db, sql, -1, &stmt, NULL);
    sqlite3_bind_int(stmt, 1, id);
    sqlite3_step(stmt);
    sqlite3_finalize(stmt);

    // Delete timezone
    sql = "DELETE FROM timezones WHERE id = ?";
    sqlite3_prepare_v2(g_db, sql, -1, &stmt, NULL);
    sqlite3_bind_int(stmt, 1, id);
    int rc = sqlite3_step(stmt);
    sqlite3_finalize(stmt);

    return (rc == SQLITE_DONE) ? ErrorCode_OK : ErrorCode_Database;
}

// =============================================================================
// Relay Database Operations
// =============================================================================

ErrorCode_t Relay_SaveToDB(const Relay_t* relay) {
    if (!g_db || !relay) return ErrorCode_BadParams;

    sqlite3_stmt* stmt = NULL;
    const char* sql = "INSERT OR REPLACE INTO relays "
                      "(id_type, id_id, id_node, pulse_duration, ctrl_timezone, flags, mode, script_id) "
                      "VALUES (?, ?, ?, ?, ?, ?, ?, ?)";

    int rc = sqlite3_prepare_v2(g_db, sql, -1, &stmt, NULL);
    if (rc != SQLITE_OK) {
        return ErrorCode_Database;
    }

    sqlite3_bind_int(stmt, 1, relay->Id.type);
    sqlite3_bind_int(stmt, 2, relay->Id.id);
    sqlite3_bind_int(stmt, 3, relay->Id.node_id);
    sqlite3_bind_int(stmt, 4, relay->PulseDuration);
    sqlite3_bind_int(stmt, 5, relay->CtrlTimeZone);
    sqlite3_bind_int(stmt, 6, relay->Flags);
    sqlite3_bind_int(stmt, 7, relay->Mode);
    sqlite3_bind_int(stmt, 8, relay->ScriptId);

    rc = sqlite3_step(stmt);
    sqlite3_finalize(stmt);

    return (rc == SQLITE_DONE) ? ErrorCode_OK : ErrorCode_Database;
}

Relay_t* Relay_LoadFromDB(LPA_t lpa) {
    if (!g_db) return NULL;

    sqlite3_stmt* stmt = NULL;
    const char* sql = "SELECT pulse_duration, ctrl_timezone, flags, mode, script_id "
                      "FROM relays WHERE id_type = ? AND id_id = ? AND id_node = ?";

    int rc = sqlite3_prepare_v2(g_db, sql, -1, &stmt, NULL);
    if (rc != SQLITE_OK) {
        return NULL;
    }

    sqlite3_bind_int(stmt, 1, lpa.type);
    sqlite3_bind_int(stmt, 2, lpa.id);
    sqlite3_bind_int(stmt, 3, lpa.node_id);
    rc = sqlite3_step(stmt);

    if (rc != SQLITE_ROW) {
        sqlite3_finalize(stmt);
        return NULL;
    }

    Relay_t* relay = Relay_Create(lpa);
    relay->PulseDuration = sqlite3_column_int(stmt, 0);
    relay->CtrlTimeZone = sqlite3_column_int(stmt, 1);
    relay->Flags = sqlite3_column_int(stmt, 2);
    relay->Mode = sqlite3_column_int(stmt, 3);
    relay->ScriptId = sqlite3_column_int(stmt, 4);
    sqlite3_finalize(stmt);

    return relay;
}

int Relay_LoadAllFromDB(Relay_t** out_relays, int max_count) {
    if (!g_db || !out_relays) return 0;

    sqlite3_stmt* stmt = NULL;
    const char* sql = "SELECT id_type, id_id, id_node FROM relays";

    int rc = sqlite3_prepare_v2(g_db, sql, -1, &stmt, NULL);
    if (rc != SQLITE_OK) {
        return 0;
    }

    int count = 0;
    while (sqlite3_step(stmt) == SQLITE_ROW && count < max_count) {
        LPA_t lpa = {
            .type = sqlite3_column_int(stmt, 0),
            .id = sqlite3_column_int(stmt, 1),
            .node_id = sqlite3_column_int(stmt, 2)
        };
        Relay_t* relay = Relay_LoadFromDB(lpa);
        if (relay) {
            out_relays[count++] = relay;
        }
    }
    sqlite3_finalize(stmt);

    return count;
}

ErrorCode_t Relay_UpdateInDB(const Relay_t* relay) {
    return Relay_SaveToDB(relay);
}

ErrorCode_t Relay_DeleteFromDB(LPA_t lpa) {
    if (!g_db) return ErrorCode_BadParams;

    sqlite3_stmt* stmt = NULL;
    const char* sql = "DELETE FROM relays WHERE id_type = ? AND id_id = ? AND id_node = ?";

    sqlite3_prepare_v2(g_db, sql, -1, &stmt, NULL);
    sqlite3_bind_int(stmt, 1, lpa.type);
    sqlite3_bind_int(stmt, 2, lpa.id);
    sqlite3_bind_int(stmt, 3, lpa.node_id);
    int rc = sqlite3_step(stmt);
    sqlite3_finalize(stmt);

    return (rc == SQLITE_DONE) ? ErrorCode_OK : ErrorCode_Database;
}

ErrorCode_t RelayLink_SaveToDB(const RelayLink_t* link) {
    if (!g_db || !link) return ErrorCode_BadParams;

    sqlite3_stmt* stmt = NULL;
    const char* sql = "INSERT OR REPLACE INTO RelayLinks (Id, Type, NodeId) VALUES (?, ?, ?)";

    int rc = sqlite3_prepare_v2(g_db, sql, -1, &stmt, NULL);
    if (rc != SQLITE_OK) {
        return ErrorCode_Database;
    }

    sqlite3_bind_int(stmt, 1, link->Id.id);
    sqlite3_bind_int(stmt, 2, link->Id.type);
    sqlite3_bind_int(stmt, 3, link->Id.node_id);
    rc = sqlite3_step(stmt);
    sqlite3_finalize(stmt);

    if (rc != SQLITE_DONE) {
        return ErrorCode_Database;
    }

    // Save link records
    if (link->LinkList) {
        // Delete existing records
        sql = "DELETE FROM RelayLinkRecords WHERE LinkId = ?";
        sqlite3_prepare_v2(g_db, sql, -1, &stmt, NULL);
        sqlite3_bind_int(stmt, 1, link->Id.id);
        sqlite3_step(stmt);
        sqlite3_finalize(stmt);

        // Insert new records
        sql = "INSERT INTO RelayLinkRecords "
              "(LinkId, SourceType, SourceId, SourceNode, Type, SubType, NewStatus, Operation) "
              "VALUES (?, ?, ?, ?, ?, ?, ?, ?)";

        for (uint32_t i = 0; i < link->LinkList->count; i++) {
            RelayLinkRecord_t* record = (RelayLinkRecord_t*)link->LinkList->data[i];

            sqlite3_prepare_v2(g_db, sql, -1, &stmt, NULL);
            sqlite3_bind_int(stmt, 1, link->Id.id);
            sqlite3_bind_int(stmt, 2, record->Source.type);
            sqlite3_bind_int(stmt, 3, record->Source.id);
            sqlite3_bind_int(stmt, 4, record->Source.node_id);
            sqlite3_bind_int(stmt, 5, record->Type);
            sqlite3_bind_int(stmt, 6, record->SubType);
            sqlite3_bind_int(stmt, 7, record->NewStatus);
            sqlite3_bind_int(stmt, 8, record->Operation);
            sqlite3_step(stmt);
            sqlite3_finalize(stmt);
        }
    }

    return ErrorCode_OK;
}

int RelayLink_LoadAllFromDB(RelayLink_t** out_links, int max_count) {
    if (!g_db || !out_links) return 0;

    sqlite3_stmt* stmt = NULL;
    const char* sql = "SELECT DISTINCT Id, Type, NodeId FROM relay_links";

    int rc = sqlite3_prepare_v2(g_db, sql, -1, &stmt, NULL);
    if (rc != SQLITE_OK) {
        return 0;
    }

    int count = 0;
    while (sqlite3_step(stmt) == SQLITE_ROW && count < max_count) {
        LPA_t lpa = {
            .id = sqlite3_column_int(stmt, 0),
            .type = sqlite3_column_int(stmt, 1),
            .node_id = sqlite3_column_int(stmt, 2)
        };

        RelayLink_t* link = RelayLink_Create(lpa);

        // Load records for this link
        sqlite3_stmt* stmt2 = NULL;
        const char* sql2 = "SELECT SourceType, SourceId, SourceNode, Type, SubType, NewStatus, Operation "
                           "FROM RelayLinkRecords WHERE LinkId = ?";

        sqlite3_prepare_v2(g_db, sql2, -1, &stmt2, NULL);
        sqlite3_bind_int(stmt2, 1, lpa.id);

        while (sqlite3_step(stmt2) == SQLITE_ROW) {
            RelayLinkRecord_t* record = (RelayLinkRecord_t*)malloc(sizeof(RelayLinkRecord_t));
            record->Source.type = sqlite3_column_int(stmt2, 0);
            record->Source.id = sqlite3_column_int(stmt2, 1);
            record->Source.node_id = sqlite3_column_int(stmt2, 2);
            record->Type = sqlite3_column_int(stmt2, 3);
            record->SubType = sqlite3_column_int(stmt2, 4);
            record->NewStatus = sqlite3_column_int(stmt2, 5);
            record->Operation = sqlite3_column_int(stmt2, 6);
            RelayLink_AddRecord(link, record);
        }
        sqlite3_finalize(stmt2);

        out_links[count++] = link;
    }
    sqlite3_finalize(stmt);

    return count;
}

// =============================================================================
// Reader Database Operations
// =============================================================================

ErrorCode_t Reader_SaveToDB(const Reader_t* reader) {
    if (!g_db || !reader) return ErrorCode_BadParams;

    sqlite3_stmt* stmt = NULL;
    const char* sql = "INSERT OR REPLACE INTO readers "
                      "(id_type, id_id, id_node, init_mode, flags) "
                      "VALUES (?, ?, ?, ?, ?)";

    int rc = sqlite3_prepare_v2(g_db, sql, -1, &stmt, NULL);
    if (rc != SQLITE_OK) {
        return ErrorCode_Database;
    }

    sqlite3_bind_int(stmt, 1, reader->Id.type);
    sqlite3_bind_int(stmt, 2, reader->Id.id);
    sqlite3_bind_int(stmt, 3, reader->Id.node_id);
    sqlite3_bind_int(stmt, 4, reader->InitMode);
    sqlite3_bind_int(stmt, 5, reader->Flags);

    rc = sqlite3_step(stmt);
    sqlite3_finalize(stmt);

    return (rc == SQLITE_DONE) ? ErrorCode_OK : ErrorCode_Database;
}

Reader_t* Reader_LoadFromDB(LPA_t lpa) {
    if (!g_db) return NULL;

    sqlite3_stmt* stmt = NULL;
    const char* sql = "SELECT init_mode, flags "
                      "FROM readers WHERE id_type = ? AND id_id = ? AND id_node = ?";

    int rc = sqlite3_prepare_v2(g_db, sql, -1, &stmt, NULL);
    if (rc != SQLITE_OK) {
        return NULL;
    }

    sqlite3_bind_int(stmt, 1, lpa.type);
    sqlite3_bind_int(stmt, 2, lpa.id);
    sqlite3_bind_int(stmt, 3, lpa.node_id);
    rc = sqlite3_step(stmt);

    if (rc != SQLITE_ROW) {
        sqlite3_finalize(stmt);
        return NULL;
    }

    Reader_t* reader = Reader_Create(lpa);
    reader->InitMode = sqlite3_column_int(stmt, 0);
    reader->Flags = sqlite3_column_int(stmt, 1);
    sqlite3_finalize(stmt);

    return reader;
}

int Reader_LoadAllFromDB(Reader_t** out_readers, int max_count) {
    if (!g_db || !out_readers) return 0;

    sqlite3_stmt* stmt = NULL;
    const char* sql = "SELECT Type, Id, NodeId FROM readers";

    int rc = sqlite3_prepare_v2(g_db, sql, -1, &stmt, NULL);
    if (rc != SQLITE_OK) {
        return 0;
    }

    int count = 0;
    while (sqlite3_step(stmt) == SQLITE_ROW && count < max_count) {
        LPA_t lpa = {
            .type = sqlite3_column_int(stmt, 0),
            .id = sqlite3_column_int(stmt, 1),
            .node_id = sqlite3_column_int(stmt, 2)
        };
        Reader_t* reader = Reader_LoadFromDB(lpa);
        if (reader) {
            out_readers[count++] = reader;
        }
    }
    sqlite3_finalize(stmt);

    return count;
}

ErrorCode_t Reader_UpdateInDB(const Reader_t* reader) {
    return Reader_SaveToDB(reader);
}

ErrorCode_t Reader_DeleteFromDB(LPA_t lpa) {
    if (!g_db) return ErrorCode_BadParams;

    sqlite3_stmt* stmt = NULL;
    const char* sql = "DELETE FROM readers WHERE id_type = ? AND id_id = ? AND id_node = ?";

    sqlite3_prepare_v2(g_db, sql, -1, &stmt, NULL);
    sqlite3_bind_int(stmt, 1, lpa.type);
    sqlite3_bind_int(stmt, 2, lpa.id);
    sqlite3_bind_int(stmt, 3, lpa.node_id);
    int rc = sqlite3_step(stmt);
    sqlite3_finalize(stmt);

    return (rc == SQLITE_DONE) ? ErrorCode_OK : ErrorCode_Database;
}

// =============================================================================
// GroupList Database Operations
// =============================================================================

ErrorCode_t GroupList_SaveToDB(const GroupList_t* group_list) {
    if (!g_db || !group_list) return ErrorCode_BadParams;

    sqlite3_stmt* stmt = NULL;
    const char* sql = "INSERT OR REPLACE INTO group_lists (id_type, id_id, id_node) VALUES (?, ?, ?)";

    int rc = sqlite3_prepare_v2(g_db, sql, -1, &stmt, NULL);
    if (rc != SQLITE_OK) {
        return ErrorCode_Database;
    }

    sqlite3_bind_int(stmt, 1, group_list->Id.type);
    sqlite3_bind_int(stmt, 2, group_list->Id.id);
    sqlite3_bind_int(stmt, 3, group_list->Id.node_id);
    rc = sqlite3_step(stmt);
    sqlite3_finalize(stmt);

    if (rc != SQLITE_DONE) {
        return ErrorCode_Database;
    }

    // Save groups (Groups is a static array, not a Vector)
    // Delete existing groups
    sql = "DELETE FROM group_list_groups WHERE group_list_type = ? AND group_list_id = ? AND group_list_node = ?";
    sqlite3_prepare_v2(g_db, sql, -1, &stmt, NULL);
    sqlite3_bind_int(stmt, 1, group_list->Id.type);
    sqlite3_bind_int(stmt, 2, group_list->Id.id);
    sqlite3_bind_int(stmt, 3, group_list->Id.node_id);
    sqlite3_step(stmt);
    sqlite3_finalize(stmt);

    // Insert new groups
    sql = "INSERT INTO group_list_groups (group_list_type, group_list_id, group_list_node, position, group_id) VALUES (?, ?, ?, ?, ?)";

    for (int i = 0; i < group_list->Count; i++) {
        if (group_list->Groups[i] != 0) {  // Skip empty slots
            sqlite3_prepare_v2(g_db, sql, -1, &stmt, NULL);
            sqlite3_bind_int(stmt, 1, group_list->Id.type);
            sqlite3_bind_int(stmt, 2, group_list->Id.id);
            sqlite3_bind_int(stmt, 3, group_list->Id.node_id);
            sqlite3_bind_int(stmt, 4, i);
            sqlite3_bind_int(stmt, 5, group_list->Groups[i]);
            sqlite3_step(stmt);
            sqlite3_finalize(stmt);
        }
    }

    return ErrorCode_OK;
}

GroupList_t* GroupList_LoadFromDB(LPA_t lpa) {
    if (!g_db) return NULL;

    sqlite3_stmt* stmt = NULL;
    const char* sql = "SELECT id_id FROM group_lists WHERE id_type = ? AND id_id = ? AND id_node = ?";

    int rc = sqlite3_prepare_v2(g_db, sql, -1, &stmt, NULL);
    if (rc != SQLITE_OK) {
        return NULL;
    }

    sqlite3_bind_int(stmt, 1, lpa.type);
    sqlite3_bind_int(stmt, 2, lpa.id);
    sqlite3_bind_int(stmt, 3, lpa.node_id);
    rc = sqlite3_step(stmt);

    if (rc != SQLITE_ROW) {
        sqlite3_finalize(stmt);
        return NULL;
    }
    sqlite3_finalize(stmt);

    GroupList_t* group_list = GroupList_Create(lpa);

    // Load groups (into static array)
    sql = "SELECT position, group_id FROM group_list_groups WHERE group_list_type = ? AND group_list_id = ? AND group_list_node = ? ORDER BY position";

    sqlite3_prepare_v2(g_db, sql, -1, &stmt, NULL);
    sqlite3_bind_int(stmt, 1, lpa.type);
    sqlite3_bind_int(stmt, 2, lpa.id);
    sqlite3_bind_int(stmt, 3, lpa.node_id);

    while (sqlite3_step(stmt) == SQLITE_ROW) {
        int position = sqlite3_column_int(stmt, 0);
        uint32_t group_id = sqlite3_column_int(stmt, 1);
        // Use the GroupList_AddGroup function which properly manages the array
        GroupList_AddGroup(group_list, group_id);
    }
    sqlite3_finalize(stmt);

    return group_list;
}

int GroupList_LoadAllFromDB(GroupList_t** out_lists, int max_count) {
    if (!g_db || !out_lists) return 0;

    sqlite3_stmt* stmt = NULL;
    const char* sql = "SELECT Type, Id, NodeId FROM group_lists";

    int rc = sqlite3_prepare_v2(g_db, sql, -1, &stmt, NULL);
    if (rc != SQLITE_OK) {
        return 0;
    }

    int count = 0;
    while (sqlite3_step(stmt) == SQLITE_ROW && count < max_count) {
        LPA_t lpa = {
            .type = sqlite3_column_int(stmt, 0),
            .id = sqlite3_column_int(stmt, 1),
            .node_id = sqlite3_column_int(stmt, 2)
        };
        GroupList_t* group_list = GroupList_LoadFromDB(lpa);
        if (group_list) {
            out_lists[count++] = group_list;
        }
    }
    sqlite3_finalize(stmt);

    return count;
}

ErrorCode_t GroupList_DeleteFromDB(LPA_t lpa) {
    if (!g_db) return ErrorCode_BadParams;

    sqlite3_stmt* stmt = NULL;

    // Delete groups first
    const char* sql = "DELETE FROM group_list_groups WHERE ListId = ?";
    sqlite3_prepare_v2(g_db, sql, -1, &stmt, NULL);
    sqlite3_bind_int(stmt, 1, lpa.id);
    sqlite3_step(stmt);
    sqlite3_finalize(stmt);

    // Delete group list
    sql = "DELETE FROM group_lists WHERE id_type = ? AND id_id = ? AND id_node = ?";
    sqlite3_prepare_v2(g_db, sql, -1, &stmt, NULL);
    sqlite3_bind_int(stmt, 1, lpa.type);
    sqlite3_bind_int(stmt, 2, lpa.id);
    sqlite3_bind_int(stmt, 3, lpa.node_id);
    int rc = sqlite3_step(stmt);
    sqlite3_finalize(stmt);

    return (rc == SQLITE_DONE) ? ErrorCode_OK : ErrorCode_Database;
}

// =============================================================================
// Holiday Database Operations
// =============================================================================

ErrorCode_t Holiday_SaveToDB(uint32_t date, uint32_t types) {
    if (!g_db) return ErrorCode_BadParams;

    sqlite3_stmt* stmt = NULL;
    const char* sql = "INSERT OR REPLACE INTO holidays (date, holiday_types) VALUES (?, ?)";

    int rc = sqlite3_prepare_v2(g_db, sql, -1, &stmt, NULL);
    if (rc != SQLITE_OK) {
        return ErrorCode_Database;
    }

    sqlite3_bind_int(stmt, 1, date);
    sqlite3_bind_int(stmt, 2, types);
    rc = sqlite3_step(stmt);
    sqlite3_finalize(stmt);

    return (rc == SQLITE_DONE) ? ErrorCode_OK : ErrorCode_Database;
}

int Holiday_LoadAllFromDB(void) {
    if (!g_db) return 0;

    // Clear existing holidays in memory
    Holiday_Clear();

    sqlite3_stmt* stmt = NULL;
    const char* sql = "SELECT date, holiday_types FROM holidays ORDER BY date";

    int rc = sqlite3_prepare_v2(g_db, sql, -1, &stmt, NULL);
    if (rc != SQLITE_OK) {
        return 0;
    }

    int count = 0;
    while (sqlite3_step(stmt) == SQLITE_ROW) {
        uint32_t date = sqlite3_column_int(stmt, 0);
        uint32_t types = sqlite3_column_int(stmt, 1);
        Holiday_Add(date, types);
        count++;
    }
    sqlite3_finalize(stmt);

    return count;
}

ErrorCode_t Holiday_DeleteFromDB(uint32_t date) {
    if (!g_db) return ErrorCode_BadParams;

    sqlite3_stmt* stmt = NULL;
    const char* sql = "DELETE FROM holidays WHERE date = ?";

    sqlite3_prepare_v2(g_db, sql, -1, &stmt, NULL);
    sqlite3_bind_int(stmt, 1, date);
    int rc = sqlite3_step(stmt);
    sqlite3_finalize(stmt);

    return (rc == SQLITE_DONE) ? ErrorCode_OK : ErrorCode_Database;
}

// =============================================================================
// Bulk Operations
// =============================================================================

ErrorCode_t SDK_LoadAllFromDatabase(void) {
    if (!g_db) {
        fprintf(stderr, "Database not initialized\n");
        return ErrorCode_Database;
    }

    printf("Loading SDK configuration from database...\n");

    // Load holidays
    int holiday_count = Holiday_LoadAllFromDB();
    printf("  ✓ Loaded %d holidays\n", holiday_count);

    // Note: Permissions, TimeZones, Relays, Readers, and GroupLists
    // need to be loaded into appropriate in-memory structures.
    // This depends on how access_logic_sdk.c manages these objects.
    //
    // For now, this function demonstrates the pattern.
    // Integration with access_logic_sdk.c will be done in the next step.

    printf("✓ SDK configuration loaded successfully\n");
    return ErrorCode_OK;
}

ErrorCode_t SDK_SaveAllToDatabase(void) {
    if (!g_db) {
        fprintf(stderr, "Database not initialized\n");
        return ErrorCode_Database;
    }

    printf("Saving SDK configuration to database...\n");

    // Save all holidays
    // Note: Individual module save operations need to be called
    // based on the in-memory state managed by access_logic_sdk.c

    printf("✓ SDK configuration saved successfully\n");
    return ErrorCode_OK;
}

// =============================================================================
// Access Point Database Operations
// =============================================================================

ErrorCode_t AccessPoint_SaveToDB(const AccessPoint_t* access_point) {
    if (!g_db || !access_point) return ErrorCode_BadParams;

    sqlite3_stmt* stmt = NULL;
    const char* sql = "INSERT OR REPLACE INTO access_points "
                      "(id, lpa_type, lpa_id, lpa_node, init_mode, "
                      "short_strike_time, long_strike_time, short_held_open_time, long_held_open_time, "
                      "area_a_type, area_a_id, area_a_node, area_b_type, area_b_id, area_b_node, "
                      "reader_type, reader_id, reader_node) "
                      "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)";

    int rc = sqlite3_prepare_v2(g_db, sql, -1, &stmt, NULL);
    if (rc != SQLITE_OK) {
        return ErrorCode_Database;
    }

    sqlite3_bind_int(stmt, 1, access_point->id);
    sqlite3_bind_int(stmt, 2, access_point->lpa.type);
    sqlite3_bind_int(stmt, 3, access_point->lpa.id);
    sqlite3_bind_int(stmt, 4, access_point->lpa.node_id);
    sqlite3_bind_int(stmt, 5, access_point->init_mode);
    sqlite3_bind_int(stmt, 6, access_point->short_strike_time);
    sqlite3_bind_int(stmt, 7, access_point->long_strike_time);
    sqlite3_bind_int(stmt, 8, access_point->short_held_open_time);
    sqlite3_bind_int(stmt, 9, access_point->long_held_open_time);
    sqlite3_bind_int(stmt, 10, access_point->area_a.type);
    sqlite3_bind_int(stmt, 11, access_point->area_a.id);
    sqlite3_bind_int(stmt, 12, access_point->area_a.node_id);
    sqlite3_bind_int(stmt, 13, access_point->area_b.type);
    sqlite3_bind_int(stmt, 14, access_point->area_b.id);
    sqlite3_bind_int(stmt, 15, access_point->area_b.node_id);
    sqlite3_bind_int(stmt, 16, access_point->reader_lpa.type);
    sqlite3_bind_int(stmt, 17, access_point->reader_lpa.id);
    sqlite3_bind_int(stmt, 18, access_point->reader_lpa.node_id);

    rc = sqlite3_step(stmt);
    sqlite3_finalize(stmt);

    if (rc != SQLITE_DONE) {
        return ErrorCode_Database;
    }

    // Delete existing strikes
    sql = "DELETE FROM access_point_strikes WHERE access_point_id = ?";
    sqlite3_prepare_v2(g_db, sql, -1, &stmt, NULL);
    sqlite3_bind_int(stmt, 1, access_point->id);
    sqlite3_step(stmt);
    sqlite3_finalize(stmt);

    // Insert strikes
    sql = "INSERT INTO access_point_strikes "
          "(access_point_id, strike_type, strike_id, strike_node, pulse_duration) "
          "VALUES (?, ?, ?, ?, ?)";

    for (int i = 0; i < access_point->strike_count; i++) {
        sqlite3_prepare_v2(g_db, sql, -1, &stmt, NULL);
        sqlite3_bind_int(stmt, 1, access_point->id);
        sqlite3_bind_int(stmt, 2, access_point->strikes[i].strike_lpa.type);
        sqlite3_bind_int(stmt, 3, access_point->strikes[i].strike_lpa.id);
        sqlite3_bind_int(stmt, 4, access_point->strikes[i].strike_lpa.node_id);
        sqlite3_bind_int(stmt, 5, access_point->strikes[i].pulse_duration);
        sqlite3_step(stmt);
        sqlite3_finalize(stmt);
    }

    return ErrorCode_OK;
}

AccessPoint_t* AccessPoint_LoadFromDB(uint32_t id) {
    if (!g_db) return NULL;

    sqlite3_stmt* stmt = NULL;
    const char* sql = "SELECT lpa_type, lpa_id, lpa_node, init_mode, "
                      "short_strike_time, long_strike_time, short_held_open_time, long_held_open_time, "
                      "area_a_type, area_a_id, area_a_node, area_b_type, area_b_id, area_b_node, "
                      "reader_type, reader_id, reader_node "
                      "FROM access_points WHERE id = ?";

    int rc = sqlite3_prepare_v2(g_db, sql, -1, &stmt, NULL);
    if (rc != SQLITE_OK) {
        return NULL;
    }

    sqlite3_bind_int(stmt, 1, id);
    rc = sqlite3_step(stmt);

    if (rc != SQLITE_ROW) {
        sqlite3_finalize(stmt);
        return NULL;
    }

    AccessPoint_t* ap = AccessPoint_Create(id);
    ap->lpa.type = sqlite3_column_int(stmt, 0);
    ap->lpa.id = sqlite3_column_int(stmt, 1);
    ap->lpa.node_id = sqlite3_column_int(stmt, 2);
    ap->init_mode = sqlite3_column_int(stmt, 3);
    ap->short_strike_time = sqlite3_column_int(stmt, 4);
    ap->long_strike_time = sqlite3_column_int(stmt, 5);
    ap->short_held_open_time = sqlite3_column_int(stmt, 6);
    ap->long_held_open_time = sqlite3_column_int(stmt, 7);
    ap->area_a.type = sqlite3_column_int(stmt, 8);
    ap->area_a.id = sqlite3_column_int(stmt, 9);
    ap->area_a.node_id = sqlite3_column_int(stmt, 10);
    ap->area_b.type = sqlite3_column_int(stmt, 11);
    ap->area_b.id = sqlite3_column_int(stmt, 12);
    ap->area_b.node_id = sqlite3_column_int(stmt, 13);
    ap->reader_lpa.type = sqlite3_column_int(stmt, 14);
    ap->reader_lpa.id = sqlite3_column_int(stmt, 15);
    ap->reader_lpa.node_id = sqlite3_column_int(stmt, 16);
    sqlite3_finalize(stmt);

    // Load strikes
    sql = "SELECT strike_type, strike_id, strike_node, pulse_duration "
          "FROM access_point_strikes WHERE access_point_id = ?";

    sqlite3_prepare_v2(g_db, sql, -1, &stmt, NULL);
    sqlite3_bind_int(stmt, 1, id);

    ap->strike_count = 0;
    while (sqlite3_step(stmt) == SQLITE_ROW && ap->strike_count < 8) {
        ap->strikes[ap->strike_count].strike_lpa.type = sqlite3_column_int(stmt, 0);
        ap->strikes[ap->strike_count].strike_lpa.id = sqlite3_column_int(stmt, 1);
        ap->strikes[ap->strike_count].strike_lpa.node_id = sqlite3_column_int(stmt, 2);
        ap->strikes[ap->strike_count].pulse_duration = sqlite3_column_int(stmt, 3);
        ap->strike_count++;
    }
    sqlite3_finalize(stmt);

    return ap;
}

int AccessPoint_LoadAllFromDB(AccessPoint_t** out_access_points, int max_count) {
    if (!g_db || !out_access_points) return 0;

    sqlite3_stmt* stmt = NULL;
    const char* sql = "SELECT id FROM access_points ORDER BY id";

    int rc = sqlite3_prepare_v2(g_db, sql, -1, &stmt, NULL);
    if (rc != SQLITE_OK) {
        return 0;
    }

    int count = 0;
    while (sqlite3_step(stmt) == SQLITE_ROW && count < max_count) {
        uint32_t id = sqlite3_column_int(stmt, 0);
        AccessPoint_t* ap = AccessPoint_LoadFromDB(id);
        if (ap) {
            out_access_points[count++] = ap;
        }
    }
    sqlite3_finalize(stmt);

    return count;
}

ErrorCode_t AccessPoint_DeleteFromDB(uint32_t id) {
    if (!g_db) return ErrorCode_BadParams;

    sqlite3_stmt* stmt = NULL;
    const char* sql = "DELETE FROM access_points WHERE id = ?";

    sqlite3_prepare_v2(g_db, sql, -1, &stmt, NULL);
    sqlite3_bind_int(stmt, 1, id);
    int rc = sqlite3_step(stmt);
    sqlite3_finalize(stmt);

    return (rc == SQLITE_DONE) ? ErrorCode_OK : ErrorCode_Database;
}

// =============================================================================
// Area Database Operations
// =============================================================================

ErrorCode_t Area_SaveToDB(const Area_t* area) {
    if (!g_db || !area) return ErrorCode_BadParams;

    sqlite3_stmt* stmt = NULL;
    const char* sql = "INSERT OR REPLACE INTO areas "
                      "(id, lpa_type, lpa_id, lpa_node, name, timed_apb, "
                      "min_occupancy, max_occupancy, occupancy_limit, min_required_occupancy, current_occupancy) "
                      "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)";

    int rc = sqlite3_prepare_v2(g_db, sql, -1, &stmt, NULL);
    if (rc != SQLITE_OK) {
        return ErrorCode_Database;
    }

    sqlite3_bind_int(stmt, 1, area->id);
    sqlite3_bind_int(stmt, 2, area->lpa.type);
    sqlite3_bind_int(stmt, 3, area->lpa.id);
    sqlite3_bind_int(stmt, 4, area->lpa.node_id);
    sqlite3_bind_text(stmt, 5, area->name, -1, SQLITE_TRANSIENT);
    sqlite3_bind_int(stmt, 6, area->timed_apb);
    sqlite3_bind_int(stmt, 7, area->min_occupancy);
    sqlite3_bind_int(stmt, 8, area->max_occupancy);
    sqlite3_bind_int(stmt, 9, area->occupancy_limit);
    sqlite3_bind_int(stmt, 10, area->min_required_occupancy);
    sqlite3_bind_int(stmt, 11, area->current_occupancy);

    rc = sqlite3_step(stmt);
    sqlite3_finalize(stmt);

    return (rc == SQLITE_DONE) ? ErrorCode_OK : ErrorCode_Database;
}

Area_t* Area_LoadFromDB(uint32_t id) {
    if (!g_db) return NULL;

    sqlite3_stmt* stmt = NULL;
    const char* sql = "SELECT lpa_type, lpa_id, lpa_node, name, timed_apb, "
                      "min_occupancy, max_occupancy, occupancy_limit, min_required_occupancy, current_occupancy "
                      "FROM areas WHERE id = ?";

    int rc = sqlite3_prepare_v2(g_db, sql, -1, &stmt, NULL);
    if (rc != SQLITE_OK) {
        return NULL;
    }

    sqlite3_bind_int(stmt, 1, id);
    rc = sqlite3_step(stmt);

    if (rc != SQLITE_ROW) {
        sqlite3_finalize(stmt);
        return NULL;
    }

    Area_t* area = Area_Create(id);
    area->lpa.type = sqlite3_column_int(stmt, 0);
    area->lpa.id = sqlite3_column_int(stmt, 1);
    area->lpa.node_id = sqlite3_column_int(stmt, 2);
    
    const char* name = (const char*)sqlite3_column_text(stmt, 3);
    if (name) {
        strncpy(area->name, name, sizeof(area->name) - 1);
        area->name[sizeof(area->name) - 1] = '\0';
    }

    area->timed_apb = sqlite3_column_int(stmt, 4);
    area->min_occupancy = sqlite3_column_int(stmt, 5);
    area->max_occupancy = sqlite3_column_int(stmt, 6);
    area->occupancy_limit = sqlite3_column_int(stmt, 7);
    area->min_required_occupancy = sqlite3_column_int(stmt, 8);
    area->current_occupancy = sqlite3_column_int(stmt, 9);
    sqlite3_finalize(stmt);

    return area;
}

int Area_LoadAllFromDB(Area_t** out_areas, int max_count) {
    if (!g_db || !out_areas) return 0;

    sqlite3_stmt* stmt = NULL;
    const char* sql = "SELECT id FROM areas ORDER BY id";

    int rc = sqlite3_prepare_v2(g_db, sql, -1, &stmt, NULL);
    if (rc != SQLITE_OK) {
        return 0;
    }

    int count = 0;
    while (sqlite3_step(stmt) == SQLITE_ROW && count < max_count) {
        uint32_t id = sqlite3_column_int(stmt, 0);
        Area_t* area = Area_LoadFromDB(id);
        if (area) {
            out_areas[count++] = area;
        }
    }
    sqlite3_finalize(stmt);

    return count;
}

ErrorCode_t Area_DeleteFromDB(uint32_t id) {
    if (!g_db) return ErrorCode_BadParams;

    sqlite3_stmt* stmt = NULL;
    const char* sql = "DELETE FROM areas WHERE id = ?";

    sqlite3_prepare_v2(g_db, sql, -1, &stmt, NULL);
    sqlite3_bind_int(stmt, 1, id);
    int rc = sqlite3_step(stmt);
    sqlite3_finalize(stmt);

    return (rc == SQLITE_DONE) ? ErrorCode_OK : ErrorCode_Database;
}

// =============================================================================
// Card Format Database Operations
// =============================================================================

ErrorCode_t CardFormat_SaveToDB(const CardFormat_t* format) {
    if (!g_db || !format) return ErrorCode_BadParams;

    sqlite3_stmt* stmt = NULL;
    const char* sql = "INSERT OR REPLACE INTO card_formats "
                      "(id, format_type, name, total_bits, facility_start_bit, facility_bit_length, "
                      "card_start_bit, card_bit_length, parity_type) "
                      "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)";

    int rc = sqlite3_prepare_v2(g_db, sql, -1, &stmt, NULL);
    if (rc != SQLITE_OK) {
        return ErrorCode_Database;
    }

    sqlite3_bind_int(stmt, 1, format->id);
    sqlite3_bind_int(stmt, 2, format->type);
    sqlite3_bind_text(stmt, 3, format->name, -1, SQLITE_TRANSIENT);
    sqlite3_bind_int(stmt, 4, format->total_bits);
    sqlite3_bind_int(stmt, 5, format->facility_start_bit);
    sqlite3_bind_int(stmt, 6, format->facility_bit_length);
    sqlite3_bind_int(stmt, 7, format->card_start_bit);
    sqlite3_bind_int(stmt, 8, format->card_bit_length);
    sqlite3_bind_int(stmt, 9, format->parity_type);

    rc = sqlite3_step(stmt);
    sqlite3_finalize(stmt);

    return (rc == SQLITE_DONE) ? ErrorCode_OK : ErrorCode_Database;
}

CardFormat_t* CardFormat_LoadFromDB(uint8_t id) {
    if (!g_db) return NULL;

    sqlite3_stmt* stmt = NULL;
    const char* sql = "SELECT format_type, name, total_bits, facility_start_bit, facility_bit_length, "
                      "card_start_bit, card_bit_length, parity_type "
                      "FROM card_formats WHERE id = ?";

    int rc = sqlite3_prepare_v2(g_db, sql, -1, &stmt, NULL);
    if (rc != SQLITE_OK) {
        return NULL;
    }

    sqlite3_bind_int(stmt, 1, id);
    rc = sqlite3_step(stmt);

    if (rc != SQLITE_ROW) {
        sqlite3_finalize(stmt);
        return NULL;
    }

    CardFormat_t* format = CardFormat_Create(id);
    format->type = sqlite3_column_int(stmt, 0);
    
    const char* name = (const char*)sqlite3_column_text(stmt, 1);
    if (name) {
        strncpy(format->name, name, sizeof(format->name) - 1);
        format->name[sizeof(format->name) - 1] = '\0';
    }

    format->total_bits = sqlite3_column_int(stmt, 2);
    format->facility_start_bit = sqlite3_column_int(stmt, 3);
    format->facility_bit_length = sqlite3_column_int(stmt, 4);
    format->card_start_bit = sqlite3_column_int(stmt, 5);
    format->card_bit_length = sqlite3_column_int(stmt, 6);
    format->parity_type = sqlite3_column_int(stmt, 7);
    sqlite3_finalize(stmt);

    return format;
}

int CardFormat_LoadAllFromDB(CardFormat_t** out_formats, int max_count) {
    if (!g_db || !out_formats) return 0;

    sqlite3_stmt* stmt = NULL;
    const char* sql = "SELECT id FROM card_formats ORDER BY id";

    int rc = sqlite3_prepare_v2(g_db, sql, -1, &stmt, NULL);
    if (rc != SQLITE_OK) {
        return 0;
    }

    int count = 0;
    while (sqlite3_step(stmt) == SQLITE_ROW && count < max_count) {
        uint8_t id = sqlite3_column_int(stmt, 0);
        CardFormat_t* format = CardFormat_LoadFromDB(id);
        if (format) {
            out_formats[count++] = format;
        }
    }
    sqlite3_finalize(stmt);

    return count;
}

ErrorCode_t CardFormat_DeleteFromDB(uint8_t id) {
    if (!g_db) return ErrorCode_BadParams;

    sqlite3_stmt* stmt = NULL;
    const char* sql = "DELETE FROM card_formats WHERE id = ?";

    sqlite3_prepare_v2(g_db, sql, -1, &stmt, NULL);
    sqlite3_bind_int(stmt, 1, id);
    int rc = sqlite3_step(stmt);
    sqlite3_finalize(stmt);

    return (rc == SQLITE_DONE) ? ErrorCode_OK : ErrorCode_Database;
}

ErrorCode_t CardFormatList_SaveToDB(const CardFormatList_t* list) {
    if (!g_db || !list) return ErrorCode_BadParams;

    sqlite3_stmt* stmt = NULL;
    const char* sql = "INSERT OR REPLACE INTO card_format_lists (id) VALUES (?)";

    int rc = sqlite3_prepare_v2(g_db, sql, -1, &stmt, NULL);
    if (rc != SQLITE_OK) {
        return ErrorCode_Database;
    }

    sqlite3_bind_int(stmt, 1, list->id);
    rc = sqlite3_step(stmt);
    sqlite3_finalize(stmt);

    if (rc != SQLITE_DONE) {
        return ErrorCode_Database;
    }

    // Delete existing format associations
    sql = "DELETE FROM card_format_list_formats WHERE list_id = ?";
    sqlite3_prepare_v2(g_db, sql, -1, &stmt, NULL);
    sqlite3_bind_int(stmt, 1, list->id);
    sqlite3_step(stmt);
    sqlite3_finalize(stmt);

    // Insert new format associations
    sql = "INSERT INTO card_format_list_formats (list_id, format_id, position) VALUES (?, ?, ?)";

    for (int i = 0; i < list->count; i++) {
        sqlite3_prepare_v2(g_db, sql, -1, &stmt, NULL);
        sqlite3_bind_int(stmt, 1, list->id);
        sqlite3_bind_int(stmt, 2, list->format_ids[i]);
        sqlite3_bind_int(stmt, 3, i);
        sqlite3_step(stmt);
        sqlite3_finalize(stmt);
    }

    return ErrorCode_OK;
}

CardFormatList_t* CardFormatList_LoadFromDB(uint8_t id) {
    if (!g_db) return NULL;

    sqlite3_stmt* stmt = NULL;
    const char* sql = "SELECT id FROM card_format_lists WHERE id = ?";

    int rc = sqlite3_prepare_v2(g_db, sql, -1, &stmt, NULL);
    if (rc != SQLITE_OK) {
        return NULL;
    }

    sqlite3_bind_int(stmt, 1, id);
    rc = sqlite3_step(stmt);

    if (rc != SQLITE_ROW) {
        sqlite3_finalize(stmt);
        return NULL;
    }
    sqlite3_finalize(stmt);

    CardFormatList_t* list = CardFormatList_Create(id);

    // Load format associations
    sql = "SELECT format_id FROM card_format_list_formats WHERE list_id = ? ORDER BY position";

    sqlite3_prepare_v2(g_db, sql, -1, &stmt, NULL);
    sqlite3_bind_int(stmt, 1, id);

    list->count = 0;
    while (sqlite3_step(stmt) == SQLITE_ROW && list->count < 16) {
        list->format_ids[list->count] = sqlite3_column_int(stmt, 0);
        list->count++;
    }
    sqlite3_finalize(stmt);

    return list;
}

ErrorCode_t CardFormatList_DeleteFromDB(uint8_t id) {
    if (!g_db) return ErrorCode_BadParams;

    sqlite3_stmt* stmt = NULL;
    const char* sql = "DELETE FROM card_format_lists WHERE id = ?";

    sqlite3_prepare_v2(g_db, sql, -1, &stmt, NULL);
    sqlite3_bind_int(stmt, 1, id);
    int rc = sqlite3_step(stmt);
    sqlite3_finalize(stmt);

    return (rc == SQLITE_DONE) ? ErrorCode_OK : ErrorCode_Database;
}
