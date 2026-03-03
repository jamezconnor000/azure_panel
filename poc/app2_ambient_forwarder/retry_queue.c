/**
 * @file retry_queue.c
 * @brief Retry queue implementation
 *
 * @author FAM-HAL-v1.0-001
 * @date February 10, 2026
 */

#include "retry_queue.h"
#include "json_serializer.h"
#include "logger.h"

#include <sqlite3.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

/* ============================================================================
 * Static State
 * ========================================================================== */

static sqlite3* s_db = NULL;
static int s_max_size = 10000;

static const char* SQL_CREATE =
    "CREATE TABLE IF NOT EXISTS retry_queue ("
    "  id INTEGER PRIMARY KEY AUTOINCREMENT,"
    "  event_json TEXT NOT NULL,"
    "  created_at INTEGER NOT NULL,"
    "  attempts INTEGER DEFAULT 0"
    ");";

static const char* SQL_PUSH =
    "INSERT INTO retry_queue (event_json, created_at, attempts) VALUES (?, ?, 0);";

static const char* SQL_PEEK =
    "SELECT id, event_json FROM retry_queue ORDER BY id LIMIT 1;";

static const char* SQL_REMOVE =
    "DELETE FROM retry_queue WHERE id = ?;";

static const char* SQL_COUNT =
    "SELECT COUNT(*) FROM retry_queue;";

static const char* SQL_CLEAR =
    "DELETE FROM retry_queue;";

/* ============================================================================
 * Public Functions
 * ========================================================================== */

int retry_queue_init(const char* db_path, int max_size) {
    if (s_db) {
        return 0;
    }

    if (!db_path) {
        LOG_ERROR("Retry queue database path is NULL");
        return -1;
    }

    s_max_size = max_size > 0 ? max_size : 10000;

    int rc = sqlite3_open(db_path, &s_db);
    if (rc != SQLITE_OK) {
        LOG_ERROR("Failed to open retry queue database: %s", sqlite3_errmsg(s_db));
        sqlite3_close(s_db);
        s_db = NULL;
        return -1;
    }

    /* Create table */
    char* err_msg = NULL;
    rc = sqlite3_exec(s_db, SQL_CREATE, NULL, NULL, &err_msg);
    if (rc != SQLITE_OK) {
        LOG_ERROR("Failed to create retry queue table: %s", err_msg);
        sqlite3_free(err_msg);
        sqlite3_close(s_db);
        s_db = NULL;
        return -1;
    }

    LOG_INFO("Retry queue initialized: %s (max %d)", db_path, s_max_size);
    return 0;
}

void retry_queue_close(void) {
    if (s_db) {
        sqlite3_close(s_db);
        s_db = NULL;
        LOG_INFO("Retry queue closed");
    }
}

bool retry_queue_is_open(void) {
    return s_db != NULL;
}

int retry_queue_push(const hal_event_t* event) {
    if (!s_db || !event) {
        return -1;
    }

    /* Check size limit */
    int current_size = retry_queue_size();
    if (current_size >= s_max_size) {
        LOG_WARN("Retry queue full (%d), dropping event", s_max_size);
        return -1;
    }

    /* Serialize event */
    char* json = event_to_json(event);
    if (!json) {
        LOG_ERROR("Failed to serialize event for retry queue");
        return -1;
    }

    sqlite3_stmt* stmt = NULL;
    int rc = sqlite3_prepare_v2(s_db, SQL_PUSH, -1, &stmt, NULL);
    if (rc != SQLITE_OK) {
        LOG_ERROR("Failed to prepare push statement: %s", sqlite3_errmsg(s_db));
        free(json);
        return -1;
    }

    sqlite3_bind_text(stmt, 1, json, -1, SQLITE_TRANSIENT);
    sqlite3_bind_int64(stmt, 2, time(NULL));

    rc = sqlite3_step(stmt);
    sqlite3_finalize(stmt);
    free(json);

    if (rc != SQLITE_DONE) {
        LOG_ERROR("Failed to insert into retry queue: %s", sqlite3_errmsg(s_db));
        return -1;
    }

    LOG_DEBUG("Event queued for retry");
    return 0;
}

int retry_queue_peek(hal_event_t* event, int64_t* id) {
    if (!s_db || !event || !id) {
        return -1;
    }

    sqlite3_stmt* stmt = NULL;
    int rc = sqlite3_prepare_v2(s_db, SQL_PEEK, -1, &stmt, NULL);
    if (rc != SQLITE_OK) {
        return -1;
    }

    rc = sqlite3_step(stmt);
    if (rc == SQLITE_ROW) {
        *id = sqlite3_column_int64(stmt, 0);
        const char* json = (const char*)sqlite3_column_text(stmt, 1);

        if (json_to_event(json, event) != 0) {
            sqlite3_finalize(stmt);
            return -1;
        }

        sqlite3_finalize(stmt);
        return 0;
    } else if (rc == SQLITE_DONE) {
        sqlite3_finalize(stmt);
        return 1;  /* Queue empty */
    }

    sqlite3_finalize(stmt);
    return -1;
}

int retry_queue_remove(int64_t id) {
    if (!s_db) {
        return -1;
    }

    sqlite3_stmt* stmt = NULL;
    int rc = sqlite3_prepare_v2(s_db, SQL_REMOVE, -1, &stmt, NULL);
    if (rc != SQLITE_OK) {
        return -1;
    }

    sqlite3_bind_int64(stmt, 1, id);
    rc = sqlite3_step(stmt);
    sqlite3_finalize(stmt);

    return (rc == SQLITE_DONE) ? 0 : -1;
}

int retry_queue_size(void) {
    if (!s_db) {
        return 0;
    }

    sqlite3_stmt* stmt = NULL;
    int rc = sqlite3_prepare_v2(s_db, SQL_COUNT, -1, &stmt, NULL);
    if (rc != SQLITE_OK) {
        return 0;
    }

    int count = 0;
    if (sqlite3_step(stmt) == SQLITE_ROW) {
        count = sqlite3_column_int(stmt, 0);
    }

    sqlite3_finalize(stmt);
    return count;
}

int retry_queue_clear(void) {
    if (!s_db) {
        return 0;
    }

    int count = retry_queue_size();
    sqlite3_exec(s_db, SQL_CLEAR, NULL, NULL, NULL);
    LOG_INFO("Retry queue cleared: %d events removed", count);
    return count;
}
