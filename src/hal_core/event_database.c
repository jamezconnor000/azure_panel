#include "event_database.h"
#include <sqlite3.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static sqlite3* db = NULL;

ErrorCode_t EventDatabase_Initialize(const char* db_path) {
    int rc = sqlite3_open(db_path, &db);
    if (rc != SQLITE_OK) {
        printf("Failed to open database: %s\n", sqlite3_errmsg(db));
        return -1;
    }
    
    const char* sql = 
        "CREATE TABLE IF NOT EXISTS access_events ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT,"
        "event_id TEXT UNIQUE NOT NULL,"
        "event_type TEXT NOT NULL,"
        "card_number TEXT,"
        "door_number INTEGER,"
        "granted BOOLEAN,"
        "timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,"
        "sent_to_ambient BOOLEAN DEFAULT 0);";
    
    char* err = NULL;
    rc = sqlite3_exec(db, sql, NULL, NULL, &err);
    if (rc != SQLITE_OK) {
        printf("Failed to create table: %s\n", err);
        sqlite3_free(err);
        return -1;
    }
    
    printf("Event Database initialized at %s\n", db_path);
    return ErrorCode_OK;
}

ErrorCode_t EventDatabase_StoreEvent(AccessEvent_t* event) {
    if (!db || !event) return -1;
    
    const char* sql = "INSERT INTO access_events (event_id, event_type, card_number, door_number, granted) "
                      "VALUES (?, ?, ?, ?, ?);";
    
    sqlite3_stmt* stmt;
    int rc = sqlite3_prepare_v2(db, sql, -1, &stmt, NULL);
    if (rc != SQLITE_OK) return -1;
    
    sqlite3_bind_text(stmt, 1, event->eventId, -1, SQLITE_STATIC);
    sqlite3_bind_int(stmt, 2, event->type);
    sqlite3_bind_text(stmt, 3, event->cardNumber, -1, SQLITE_STATIC);
    sqlite3_bind_int(stmt, 4, event->doorNumber);
    sqlite3_bind_int(stmt, 5, event->granted ? 1 : 0);
    
    rc = sqlite3_step(stmt);
    sqlite3_finalize(stmt);
    
    if (rc == SQLITE_DONE) {
        printf("Event stored in database: %s\n", event->eventId);
        return ErrorCode_OK;
    }
    
    return -1;
}

int EventDatabase_GetUnsentCount(void) {
    if (!db) return 0;
    
    const char* sql = "SELECT COUNT(*) FROM access_events WHERE sent_to_ambient = 0;";
    sqlite3_stmt* stmt;
    
    if (sqlite3_prepare_v2(db, sql, -1, &stmt, NULL) != SQLITE_OK) return 0;
    
    int count = 0;
    if (sqlite3_step(stmt) == SQLITE_ROW) {
        count = sqlite3_column_int(stmt, 0);
    }
    
    sqlite3_finalize(stmt);
    return count;
}

ErrorCode_t EventDatabase_MarkAsSent(const char* event_id) {
    if (!db || !event_id) return -1;
    
    const char* sql = "UPDATE access_events SET sent_to_ambient = 1 WHERE event_id = ?;";
    sqlite3_stmt* stmt;
    
    if (sqlite3_prepare_v2(db, sql, -1, &stmt, NULL) != SQLITE_OK) return -1;
    
    sqlite3_bind_text(stmt, 1, event_id, -1, SQLITE_STATIC);
    int rc = sqlite3_step(stmt);
    sqlite3_finalize(stmt);
    
    return (rc == SQLITE_DONE) ? ErrorCode_OK : -1;
}

void EventDatabase_Shutdown(void) {
    if (db) {
        sqlite3_close(db);
        db = NULL;
        printf("Event Database closed\n");
    }
}
