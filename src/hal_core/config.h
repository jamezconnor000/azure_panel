#ifndef HAL_CONFIG_H
#define HAL_CONFIG_H

#include <stdbool.h>
#include <stdint.h>

typedef struct {
    char name[50];
    char location[100];
    char timezone[50];
} SystemConfig_t;

typedef struct {
    char events_db_path[256];
    char cards_db_path[256];
    int buffer_size;
    int retention_days;
} DatabaseConfig_t;

typedef struct {
    bool enabled;
    char server_url[256];
    char api_endpoint[256];
    char api_key[256];
    int timeout_seconds;
    int retry_attempts;
    int batch_size;
} AmbientConfig_t;

typedef struct {
    int relay_count;
    int door_unlock_time_ms;
    int reader_count;
} HardwareConfig_t;

typedef struct {
    int id;
    char name[50];
    int relay_id;
    int reader_id;
} DoorConfig_t;

typedef struct {
    SystemConfig_t system;
    DatabaseConfig_t database;
    AmbientConfig_t ambient_ai;
    HardwareConfig_t hardware;
    DoorConfig_t doors[10];
    int door_count;
} HALConfig_t;

HALConfig_t* Config_Load(const char* config_path);
void Config_Free(HALConfig_t* config);
void Config_Print(HALConfig_t* config);

#endif
