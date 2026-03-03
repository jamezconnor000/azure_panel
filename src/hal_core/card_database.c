#include "card_database.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

// Global database connection
static sqlite3* g_card_db = NULL;

// =============================================================================
// Database Initialization
// =============================================================================

ErrorCode_t CardDatabase_Initialize(const char* db_path) {
    if (g_card_db) {
        return ErrorCode_OK; // Already initialized
    }

    int rc = sqlite3_open(db_path, &g_card_db);
    if (rc != SQLITE_OK) {
        fprintf(stderr, "Cannot open card database: %s\n", sqlite3_errmsg(g_card_db));
        return ErrorCode_Database;
    }

    // Create cards table if it doesn't exist
    const char* create_table_sql =
        "CREATE TABLE IF NOT EXISTS Cards ("
        "    CardNumber INTEGER PRIMARY KEY,"
        "    PermissionId INTEGER NOT NULL,"
        "    CardHolderName TEXT,"
        "    ActivationDate INTEGER,"
        "    ExpirationDate INTEGER,"
        "    IsActive INTEGER DEFAULT 1,"
        "    PIN INTEGER DEFAULT 0"
        ");";

    char* err_msg = NULL;
    rc = sqlite3_exec(g_card_db, create_table_sql, NULL, NULL, &err_msg);
    if (rc != SQLITE_OK) {
        fprintf(stderr, "Failed to create cards table: %s\n", err_msg);
        sqlite3_free(err_msg);
        return ErrorCode_Database;
    }

    // Create index on permission_id for fast lookups
    const char* create_index_sql =
        "CREATE INDEX IF NOT EXISTS idx_cards_permission ON Cards(PermissionId);";

    rc = sqlite3_exec(g_card_db, create_index_sql, NULL, NULL, &err_msg);
    if (rc != SQLITE_OK) {
        fprintf(stderr, "Failed to create index: %s\n", err_msg);
        sqlite3_free(err_msg);
    }

    printf("✓ Card Database initialized: %s\n", db_path);
    return ErrorCode_OK;
}

void CardDatabase_Shutdown(void) {
    if (g_card_db) {
        sqlite3_close(g_card_db);
        g_card_db = NULL;
        printf("✓ Card Database closed\n");
    }
}

sqlite3* CardDatabase_GetConnection(void) {
    return g_card_db;
}

// =============================================================================
// Card CRUD Operations
// =============================================================================

ErrorCode_t CardDatabase_AddCard(const CardRecord_t* card) {
    if (!g_card_db || !card) return ErrorCode_BadParams;

    sqlite3_stmt* stmt = NULL;
    const char* sql =
        "INSERT INTO Cards (CardNumber, PermissionId, CardHolderName, "
        "ActivationDate, ExpirationDate, IsActive, PIN) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)";

    int rc = sqlite3_prepare_v2(g_card_db, sql, -1, &stmt, NULL);
    if (rc != SQLITE_OK) {
        fprintf(stderr, "Failed to prepare statement: %s\n", sqlite3_errmsg(g_card_db));
        return ErrorCode_Database;
    }

    sqlite3_bind_int(stmt, 1, card->card_number);
    sqlite3_bind_int(stmt, 2, card->permission_id);
    sqlite3_bind_text(stmt, 3, card->card_holder_name, -1, SQLITE_TRANSIENT);
    sqlite3_bind_int64(stmt, 4, card->activation_date);
    sqlite3_bind_int64(stmt, 5, card->expiration_date);
    sqlite3_bind_int(stmt, 6, card->is_active ? 1 : 0);
    sqlite3_bind_int(stmt, 7, card->pin);

    rc = sqlite3_step(stmt);
    sqlite3_finalize(stmt);

    if (rc != SQLITE_DONE) {
        fprintf(stderr, "Failed to insert card: %s\n", sqlite3_errmsg(g_card_db));
        return ErrorCode_Database;
    }

    return ErrorCode_OK;
}

ErrorCode_t CardDatabase_GetCard(uint32_t card_number, CardRecord_t* out_card) {
    if (!g_card_db || !out_card) return ErrorCode_BadParams;

    sqlite3_stmt* stmt = NULL;
    const char* sql =
        "SELECT CardNumber, PermissionId, CardHolderName, ActivationDate, "
        "ExpirationDate, IsActive, PIN FROM Cards WHERE CardNumber = ?";

    int rc = sqlite3_prepare_v2(g_card_db, sql, -1, &stmt, NULL);
    if (rc != SQLITE_OK) {
        return ErrorCode_Database;
    }

    sqlite3_bind_int(stmt, 1, card_number);
    rc = sqlite3_step(stmt);

    if (rc != SQLITE_ROW) {
        sqlite3_finalize(stmt);
        return ErrorCode_ObjectNotFound;
    }

    out_card->card_number = sqlite3_column_int(stmt, 0);
    out_card->permission_id = sqlite3_column_int(stmt, 1);

    const char* name = (const char*)sqlite3_column_text(stmt, 2);
    if (name) {
        strncpy(out_card->card_holder_name, name, sizeof(out_card->card_holder_name) - 1);
        out_card->card_holder_name[sizeof(out_card->card_holder_name) - 1] = '\0';
    } else {
        out_card->card_holder_name[0] = '\0';
    }

    out_card->activation_date = sqlite3_column_int64(stmt, 3);
    out_card->expiration_date = sqlite3_column_int64(stmt, 4);
    out_card->is_active = sqlite3_column_int(stmt, 5) != 0;
    out_card->pin = sqlite3_column_int(stmt, 6);

    sqlite3_finalize(stmt);
    return ErrorCode_OK;
}

ErrorCode_t CardDatabase_UpdateCard(const CardRecord_t* card) {
    if (!g_card_db || !card) return ErrorCode_BadParams;

    sqlite3_stmt* stmt = NULL;
    const char* sql =
        "UPDATE Cards SET PermissionId = ?, CardHolderName = ?, "
        "ActivationDate = ?, ExpirationDate = ?, IsActive = ?, PIN = ? "
        "WHERE CardNumber = ?";

    int rc = sqlite3_prepare_v2(g_card_db, sql, -1, &stmt, NULL);
    if (rc != SQLITE_OK) {
        return ErrorCode_Database;
    }

    sqlite3_bind_int(stmt, 1, card->permission_id);
    sqlite3_bind_text(stmt, 2, card->card_holder_name, -1, SQLITE_TRANSIENT);
    sqlite3_bind_int64(stmt, 3, card->activation_date);
    sqlite3_bind_int64(stmt, 4, card->expiration_date);
    sqlite3_bind_int(stmt, 5, card->is_active ? 1 : 0);
    sqlite3_bind_int(stmt, 6, card->pin);
    sqlite3_bind_int(stmt, 7, card->card_number);

    rc = sqlite3_step(stmt);
    sqlite3_finalize(stmt);

    return (rc == SQLITE_DONE) ? ErrorCode_OK : ErrorCode_Database;
}

ErrorCode_t CardDatabase_DeleteCard(uint32_t card_number) {
    if (!g_card_db) return ErrorCode_BadParams;

    sqlite3_stmt* stmt = NULL;
    const char* sql = "DELETE FROM Cards WHERE CardNumber = ?";

    sqlite3_prepare_v2(g_card_db, sql, -1, &stmt, NULL);
    sqlite3_bind_int(stmt, 1, card_number);
    int rc = sqlite3_step(stmt);
    sqlite3_finalize(stmt);

    return (rc == SQLITE_DONE) ? ErrorCode_OK : ErrorCode_Database;
}

int CardDatabase_GetCardsForPermission(uint32_t permission_id, CardRecord_t* out_cards, int max_count) {
    if (!g_card_db || !out_cards) return 0;

    sqlite3_stmt* stmt = NULL;
    const char* sql =
        "SELECT CardNumber, PermissionId, CardHolderName, ActivationDate, "
        "ExpirationDate, IsActive, PIN FROM Cards WHERE PermissionId = ?";

    int rc = sqlite3_prepare_v2(g_card_db, sql, -1, &stmt, NULL);
    if (rc != SQLITE_OK) {
        return 0;
    }

    sqlite3_bind_int(stmt, 1, permission_id);

    int count = 0;
    while (sqlite3_step(stmt) == SQLITE_ROW && count < max_count) {
        out_cards[count].card_number = sqlite3_column_int(stmt, 0);
        out_cards[count].permission_id = sqlite3_column_int(stmt, 1);

        const char* name = (const char*)sqlite3_column_text(stmt, 2);
        if (name) {
            strncpy(out_cards[count].card_holder_name, name, sizeof(out_cards[count].card_holder_name) - 1);
            out_cards[count].card_holder_name[sizeof(out_cards[count].card_holder_name) - 1] = '\0';
        } else {
            out_cards[count].card_holder_name[0] = '\0';
        }

        out_cards[count].activation_date = sqlite3_column_int64(stmt, 3);
        out_cards[count].expiration_date = sqlite3_column_int64(stmt, 4);
        out_cards[count].is_active = sqlite3_column_int(stmt, 5) != 0;
        out_cards[count].pin = sqlite3_column_int(stmt, 6);
        count++;
    }

    sqlite3_finalize(stmt);
    return count;
}

uint32_t CardDatabase_GetPermissionForCard(uint32_t card_number) {
    if (!g_card_db) return 0;

    sqlite3_stmt* stmt = NULL;
    const char* sql = "SELECT PermissionId FROM Cards WHERE CardNumber = ? AND IsActive = 1";

    int rc = sqlite3_prepare_v2(g_card_db, sql, -1, &stmt, NULL);
    if (rc != SQLITE_OK) {
        return 0;
    }

    sqlite3_bind_int(stmt, 1, card_number);
    rc = sqlite3_step(stmt);

    uint32_t permission_id = 0;
    if (rc == SQLITE_ROW) {
        permission_id = sqlite3_column_int(stmt, 0);
    }

    sqlite3_finalize(stmt);
    return permission_id;
}

bool CardDatabase_IsCardActive(uint32_t card_number) {
    if (!g_card_db) return false;

    sqlite3_stmt* stmt = NULL;
    const char* sql =
        "SELECT IsActive, ActivationDate, ExpirationDate "
        "FROM Cards WHERE CardNumber = ?";

    int rc = sqlite3_prepare_v2(g_card_db, sql, -1, &stmt, NULL);
    if (rc != SQLITE_OK) {
        return false;
    }

    sqlite3_bind_int(stmt, 1, card_number);
    rc = sqlite3_step(stmt);

    if (rc != SQLITE_ROW) {
        sqlite3_finalize(stmt);
        return false;
    }

    bool is_active = sqlite3_column_int(stmt, 0) != 0;
    uint64_t activation_date = sqlite3_column_int64(stmt, 1);
    uint64_t expiration_date = sqlite3_column_int64(stmt, 2);
    sqlite3_finalize(stmt);

    // Check flag
    if (!is_active) return false;

    // Check dates
    time_t now = time(NULL);
    if (activation_date > 0 && now < activation_date) return false;
    if (expiration_date > 0 && now > expiration_date) return false;

    return true;
}

bool CardDatabase_ValidatePIN(uint32_t card_number, uint32_t pin) {
    if (!g_card_db) return false;

    sqlite3_stmt* stmt = NULL;
    const char* sql = "SELECT PIN FROM Cards WHERE CardNumber = ? AND IsActive = 1";

    int rc = sqlite3_prepare_v2(g_card_db, sql, -1, &stmt, NULL);
    if (rc != SQLITE_OK) {
        return false;
    }

    sqlite3_bind_int(stmt, 1, card_number);
    rc = sqlite3_step(stmt);

    if (rc != SQLITE_ROW) {
        sqlite3_finalize(stmt);
        return false;
    }

    uint32_t stored_pin = sqlite3_column_int(stmt, 0);
    sqlite3_finalize(stmt);

    // PIN of 0 means no PIN set
    if (stored_pin == 0) return false;

    return (stored_pin == pin);
}

int CardDatabase_GetCardCount(void) {
    if (!g_card_db) return 0;

    sqlite3_stmt* stmt = NULL;
    const char* sql = "SELECT COUNT(*) FROM Cards";

    int rc = sqlite3_prepare_v2(g_card_db, sql, -1, &stmt, NULL);
    if (rc != SQLITE_OK) {
        return 0;
    }

    rc = sqlite3_step(stmt);
    int count = 0;
    if (rc == SQLITE_ROW) {
        count = sqlite3_column_int(stmt, 0);
    }

    sqlite3_finalize(stmt);
    return count;
}

int CardDatabase_LoadAllCards(CardRecord_t* out_cards, int max_count) {
    if (!g_card_db || !out_cards) return 0;

    sqlite3_stmt* stmt = NULL;
    const char* sql =
        "SELECT CardNumber, PermissionId, CardHolderName, ActivationDate, "
        "ExpirationDate, IsActive, PIN FROM Cards ORDER BY CardNumber";

    int rc = sqlite3_prepare_v2(g_card_db, sql, -1, &stmt, NULL);
    if (rc != SQLITE_OK) {
        return 0;
    }

    int count = 0;
    while (sqlite3_step(stmt) == SQLITE_ROW && count < max_count) {
        out_cards[count].card_number = sqlite3_column_int(stmt, 0);
        out_cards[count].permission_id = sqlite3_column_int(stmt, 1);

        const char* name = (const char*)sqlite3_column_text(stmt, 2);
        if (name) {
            strncpy(out_cards[count].card_holder_name, name, sizeof(out_cards[count].card_holder_name) - 1);
            out_cards[count].card_holder_name[sizeof(out_cards[count].card_holder_name) - 1] = '\0';
        } else {
            out_cards[count].card_holder_name[0] = '\0';
        }

        out_cards[count].activation_date = sqlite3_column_int64(stmt, 3);
        out_cards[count].expiration_date = sqlite3_column_int64(stmt, 4);
        out_cards[count].is_active = sqlite3_column_int(stmt, 5) != 0;
        out_cards[count].pin = sqlite3_column_int(stmt, 6);
        count++;
    }

    sqlite3_finalize(stmt);
    return count;
}
