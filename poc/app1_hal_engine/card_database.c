/**
 * @file card_database.c
 * @brief Card database implementation
 *
 * @author FAM-HAL-v1.0-001
 * @date February 10, 2026
 */

#include "card_database.h"
#include "uuid_utils.h"
#include "logger.h"
#include <sqlite3.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

/* ============================================================================
 * Static State
 * ========================================================================== */

static sqlite3* s_db = NULL;

/* SQL Statements */
static const char* SQL_CREATE_TABLE =
    "CREATE TABLE IF NOT EXISTS cards ("
    "  id INTEGER PRIMARY KEY AUTOINCREMENT,"
    "  card_number INTEGER NOT NULL UNIQUE,"
    "  facility_code INTEGER NOT NULL DEFAULT 0,"
    "  card_uid TEXT NOT NULL,"
    "  person_uid TEXT,"
    "  first_name TEXT,"
    "  last_name TEXT,"
    "  enabled INTEGER NOT NULL DEFAULT 1,"
    "  valid_from INTEGER,"
    "  valid_until INTEGER,"
    "  permission_group INTEGER DEFAULT 0,"
    "  created_at INTEGER NOT NULL,"
    "  updated_at INTEGER NOT NULL"
    ");";

static const char* SQL_CREATE_INDEX =
    "CREATE INDEX IF NOT EXISTS idx_cards_card_number ON cards(card_number);"
    "CREATE INDEX IF NOT EXISTS idx_cards_fc_cn ON cards(facility_code, card_number);";

static const char* SQL_LOOKUP =
    "SELECT id, card_number, facility_code, card_uid, person_uid, "
    "       first_name, last_name, enabled, valid_from, valid_until, permission_group "
    "FROM cards WHERE card_number = ?;";

static const char* SQL_LOOKUP_FC_CN =
    "SELECT id, card_number, facility_code, card_uid, person_uid, "
    "       first_name, last_name, enabled, valid_from, valid_until, permission_group "
    "FROM cards WHERE facility_code = ? AND card_number = ?;";

static const char* SQL_INSERT =
    "INSERT INTO cards (card_number, facility_code, card_uid, person_uid, "
    "                   first_name, last_name, enabled, valid_from, valid_until, "
    "                   permission_group, created_at, updated_at) "
    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);";

static const char* SQL_UPDATE =
    "UPDATE cards SET facility_code = ?, card_uid = ?, person_uid = ?, "
    "                 first_name = ?, last_name = ?, enabled = ?, "
    "                 valid_from = ?, valid_until = ?, permission_group = ?, "
    "                 updated_at = ? "
    "WHERE card_number = ?;";

static const char* SQL_DELETE =
    "DELETE FROM cards WHERE card_number = ?;";

static const char* SQL_COUNT =
    "SELECT COUNT(*) FROM cards;";

/* ============================================================================
 * Internal Functions
 * ========================================================================== */

static int extract_card_info(sqlite3_stmt* stmt, card_info_t* card) {
    card->id = sqlite3_column_int64(stmt, 0);
    card->card_number = (uint32_t)sqlite3_column_int(stmt, 1);
    card->facility_code = (uint32_t)sqlite3_column_int(stmt, 2);

    const char* card_uid = (const char*)sqlite3_column_text(stmt, 3);
    if (card_uid) {
        strncpy(card->card_uid, card_uid, UUID_STRING_LEN - 1);
    }

    const char* person_uid = (const char*)sqlite3_column_text(stmt, 4);
    if (person_uid) {
        strncpy(card->person_uid, person_uid, UUID_STRING_LEN - 1);
    }

    const char* first_name = (const char*)sqlite3_column_text(stmt, 5);
    if (first_name) {
        strncpy(card->first_name, first_name, sizeof(card->first_name) - 1);
    }

    const char* last_name = (const char*)sqlite3_column_text(stmt, 6);
    if (last_name) {
        strncpy(card->last_name, last_name, sizeof(card->last_name) - 1);
    }

    card->enabled = sqlite3_column_int(stmt, 7) != 0;
    card->valid_from = sqlite3_column_int64(stmt, 8);
    card->valid_until = sqlite3_column_int64(stmt, 9);
    card->permission_group = sqlite3_column_int(stmt, 10);

    return 0;
}

/* ============================================================================
 * Public Functions
 * ========================================================================== */

int card_db_init(const char* db_path) {
    if (s_db) {
        LOG_WARN("Database already initialized");
        return 0;
    }

    int rc = sqlite3_open(db_path, &s_db);
    if (rc != SQLITE_OK) {
        LOG_ERROR("Failed to open database: %s", sqlite3_errmsg(s_db));
        sqlite3_close(s_db);
        s_db = NULL;
        return -1;
    }

    /* Enable WAL mode for better concurrency */
    sqlite3_exec(s_db, "PRAGMA journal_mode=WAL;", NULL, NULL, NULL);
    sqlite3_exec(s_db, "PRAGMA busy_timeout=5000;", NULL, NULL, NULL);

    /* Create tables */
    char* err_msg = NULL;
    rc = sqlite3_exec(s_db, SQL_CREATE_TABLE, NULL, NULL, &err_msg);
    if (rc != SQLITE_OK) {
        LOG_ERROR("Failed to create table: %s", err_msg);
        sqlite3_free(err_msg);
        sqlite3_close(s_db);
        s_db = NULL;
        return -1;
    }

    /* Create indexes */
    rc = sqlite3_exec(s_db, SQL_CREATE_INDEX, NULL, NULL, &err_msg);
    if (rc != SQLITE_OK) {
        LOG_ERROR("Failed to create indexes: %s", err_msg);
        sqlite3_free(err_msg);
        /* Continue anyway - indexes are optional */
    }

    LOG_INFO("Card database initialized: %s", db_path);
    return 0;
}

void card_db_close(void) {
    if (s_db) {
        sqlite3_close(s_db);
        s_db = NULL;
        LOG_INFO("Card database closed");
    }
}

bool card_db_is_open(void) {
    return s_db != NULL;
}

int card_db_lookup(uint32_t card_number, card_info_t* card_info) {
    if (!s_db || !card_info) {
        return -1;
    }

    memset(card_info, 0, sizeof(card_info_t));

    sqlite3_stmt* stmt = NULL;
    int rc = sqlite3_prepare_v2(s_db, SQL_LOOKUP, -1, &stmt, NULL);
    if (rc != SQLITE_OK) {
        LOG_ERROR("Failed to prepare lookup statement: %s", sqlite3_errmsg(s_db));
        return -1;
    }

    sqlite3_bind_int(stmt, 1, (int)card_number);

    rc = sqlite3_step(stmt);
    if (rc == SQLITE_ROW) {
        extract_card_info(stmt, card_info);
        sqlite3_finalize(stmt);
        return 0;  /* Found */
    } else if (rc == SQLITE_DONE) {
        sqlite3_finalize(stmt);
        return 1;  /* Not found */
    } else {
        LOG_ERROR("Lookup failed: %s", sqlite3_errmsg(s_db));
        sqlite3_finalize(stmt);
        return -1;
    }
}

int card_db_lookup_fc_cn(uint32_t facility_code, uint32_t card_number,
                         card_info_t* card_info) {
    if (!s_db || !card_info) {
        return -1;
    }

    memset(card_info, 0, sizeof(card_info_t));

    sqlite3_stmt* stmt = NULL;
    int rc = sqlite3_prepare_v2(s_db, SQL_LOOKUP_FC_CN, -1, &stmt, NULL);
    if (rc != SQLITE_OK) {
        LOG_ERROR("Failed to prepare lookup statement: %s", sqlite3_errmsg(s_db));
        return -1;
    }

    sqlite3_bind_int(stmt, 1, (int)facility_code);
    sqlite3_bind_int(stmt, 2, (int)card_number);

    rc = sqlite3_step(stmt);
    if (rc == SQLITE_ROW) {
        extract_card_info(stmt, card_info);
        sqlite3_finalize(stmt);
        return 0;  /* Found */
    } else if (rc == SQLITE_DONE) {
        sqlite3_finalize(stmt);
        return 1;  /* Not found */
    } else {
        LOG_ERROR("Lookup failed: %s", sqlite3_errmsg(s_db));
        sqlite3_finalize(stmt);
        return -1;
    }
}

int card_db_add(const card_info_t* card_info) {
    if (!s_db || !card_info) {
        return -1;
    }

    sqlite3_stmt* stmt = NULL;
    int rc = sqlite3_prepare_v2(s_db, SQL_INSERT, -1, &stmt, NULL);
    if (rc != SQLITE_OK) {
        LOG_ERROR("Failed to prepare insert statement: %s", sqlite3_errmsg(s_db));
        return -1;
    }

    int64_t now = time(NULL);

    sqlite3_bind_int(stmt, 1, (int)card_info->card_number);
    sqlite3_bind_int(stmt, 2, (int)card_info->facility_code);
    sqlite3_bind_text(stmt, 3, card_info->card_uid, -1, SQLITE_STATIC);
    sqlite3_bind_text(stmt, 4, card_info->person_uid[0] ? card_info->person_uid : NULL, -1, SQLITE_STATIC);
    sqlite3_bind_text(stmt, 5, card_info->first_name, -1, SQLITE_STATIC);
    sqlite3_bind_text(stmt, 6, card_info->last_name, -1, SQLITE_STATIC);
    sqlite3_bind_int(stmt, 7, card_info->enabled ? 1 : 0);
    sqlite3_bind_int64(stmt, 8, card_info->valid_from);
    sqlite3_bind_int64(stmt, 9, card_info->valid_until);
    sqlite3_bind_int(stmt, 10, card_info->permission_group);
    sqlite3_bind_int64(stmt, 11, now);
    sqlite3_bind_int64(stmt, 12, now);

    rc = sqlite3_step(stmt);
    sqlite3_finalize(stmt);

    if (rc != SQLITE_DONE) {
        LOG_ERROR("Failed to insert card: %s", sqlite3_errmsg(s_db));
        return -1;
    }

    LOG_DEBUG("Added card: %u", card_info->card_number);
    return 0;
}

int card_db_update(const card_info_t* card_info) {
    if (!s_db || !card_info) {
        return -1;
    }

    sqlite3_stmt* stmt = NULL;
    int rc = sqlite3_prepare_v2(s_db, SQL_UPDATE, -1, &stmt, NULL);
    if (rc != SQLITE_OK) {
        LOG_ERROR("Failed to prepare update statement: %s", sqlite3_errmsg(s_db));
        return -1;
    }

    int64_t now = time(NULL);

    sqlite3_bind_int(stmt, 1, (int)card_info->facility_code);
    sqlite3_bind_text(stmt, 2, card_info->card_uid, -1, SQLITE_STATIC);
    sqlite3_bind_text(stmt, 3, card_info->person_uid[0] ? card_info->person_uid : NULL, -1, SQLITE_STATIC);
    sqlite3_bind_text(stmt, 4, card_info->first_name, -1, SQLITE_STATIC);
    sqlite3_bind_text(stmt, 5, card_info->last_name, -1, SQLITE_STATIC);
    sqlite3_bind_int(stmt, 6, card_info->enabled ? 1 : 0);
    sqlite3_bind_int64(stmt, 7, card_info->valid_from);
    sqlite3_bind_int64(stmt, 8, card_info->valid_until);
    sqlite3_bind_int(stmt, 9, card_info->permission_group);
    sqlite3_bind_int64(stmt, 10, now);
    sqlite3_bind_int(stmt, 11, (int)card_info->card_number);

    rc = sqlite3_step(stmt);
    sqlite3_finalize(stmt);

    if (rc != SQLITE_DONE) {
        LOG_ERROR("Failed to update card: %s", sqlite3_errmsg(s_db));
        return -1;
    }

    return 0;
}

int card_db_delete(uint32_t card_number) {
    if (!s_db) {
        return -1;
    }

    sqlite3_stmt* stmt = NULL;
    int rc = sqlite3_prepare_v2(s_db, SQL_DELETE, -1, &stmt, NULL);
    if (rc != SQLITE_OK) {
        LOG_ERROR("Failed to prepare delete statement: %s", sqlite3_errmsg(s_db));
        return -1;
    }

    sqlite3_bind_int(stmt, 1, (int)card_number);

    rc = sqlite3_step(stmt);
    sqlite3_finalize(stmt);

    if (rc != SQLITE_DONE) {
        LOG_ERROR("Failed to delete card: %s", sqlite3_errmsg(s_db));
        return -1;
    }

    return 0;
}

int card_db_count(void) {
    if (!s_db) {
        return -1;
    }

    sqlite3_stmt* stmt = NULL;
    int rc = sqlite3_prepare_v2(s_db, SQL_COUNT, -1, &stmt, NULL);
    if (rc != SQLITE_OK) {
        return -1;
    }

    int count = 0;
    if (sqlite3_step(stmt) == SQLITE_ROW) {
        count = sqlite3_column_int(stmt, 0);
    }

    sqlite3_finalize(stmt);
    return count;
}

int card_db_seed_test_data(void) {
    if (!s_db) {
        return -1;
    }

    /* Test cardholders */
    struct {
        uint32_t card_number;
        uint32_t facility_code;
        const char* first_name;
        const char* last_name;
        bool enabled;
    } test_cards[] = {
        { 12345, 100, "John", "Smith", true },
        { 12346, 100, "Jane", "Doe", true },
        { 12347, 100, "Bob", "Wilson", true },
        { 12348, 100, "Alice", "Brown", true },
        { 12349, 100, "Charlie", "Davis", true },
        { 12350, 100, "Disabled", "User", false },  /* Disabled card */
        { 54321, 200, "Other", "Facility", true },   /* Different FC */
        { 99999, 100, "Test", "Card", true },
        { 11111, 100, "Emergency", "Access", true },
        { 22222, 100, "Maintenance", "Staff", true },
    };

    int count = sizeof(test_cards) / sizeof(test_cards[0]);
    int added = 0;

    for (int i = 0; i < count; i++) {
        card_info_t card = {0};
        card.card_number = test_cards[i].card_number;
        card.facility_code = test_cards[i].facility_code;
        strncpy(card.first_name, test_cards[i].first_name, sizeof(card.first_name) - 1);
        strncpy(card.last_name, test_cards[i].last_name, sizeof(card.last_name) - 1);
        card.enabled = test_cards[i].enabled;
        card.valid_from = time(NULL) - 86400;  /* Valid from yesterday */
        card.valid_until = time(NULL) + 86400 * 365;  /* Valid for 1 year */

        /* Generate UUIDs */
        uuid_generate(card.card_uid);
        uuid_generate(card.person_uid);

        if (card_db_add(&card) == 0) {
            added++;
        }
    }

    LOG_INFO("Seeded %d test cards", added);
    return added;
}
