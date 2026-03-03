#include "config.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static char* read_file(const char* path) {
    FILE* fp = fopen(path, "r");
    if (!fp) return NULL;
    
    fseek(fp, 0, SEEK_END);
    long size = ftell(fp);
    fseek(fp, 0, SEEK_SET);
    
    char* buffer = malloc(size + 1);
    fread(buffer, 1, size, fp);
    buffer[size] = '\0';
    fclose(fp);
    
    return buffer;
}

static char* find_value(const char* json, const char* key) {
    char search[100];
    snprintf(search, sizeof(search), "\"%s\":", key);
    
    char* pos = strstr(json, search);
    if (!pos) return NULL;
    
    pos = strchr(pos, ':');
    if (!pos) return NULL;
    pos++;
    
    while (*pos == ' ' || *pos == '\t' || *pos == '\n') pos++;
    
    static char value[256];
    memset(value, 0, sizeof(value));
    
    if (*pos == '"') {
        pos++;
        int i = 0;
        while (*pos && *pos != '"' && i < 255) {
            value[i++] = *pos++;
        }
    } else {
        int i = 0;
        while (*pos && *pos != ',' && *pos != '}' && i < 255) {
            if (*pos != ' ' && *pos != '\n' && *pos != '\r')
                value[i++] = *pos;
            pos++;
        }
    }
    
    return value;
}

HALConfig_t* Config_Load(const char* config_path) {
    char* json = read_file(config_path);
    if (!json) {
        printf("Error: Cannot read config file: %s\n", config_path);
        return NULL;
    }
    
    HALConfig_t* config = calloc(1, sizeof(HALConfig_t));
    
    char* val = find_value(json, "name");
    if (val) strncpy(config->system.name, val, 49);
    
    val = find_value(json, "location");
    if (val) strncpy(config->system.location, val, 99);
    
    val = find_value(json, "events_db_path");
    if (val) strncpy(config->database.events_db_path, val, 255);
    else strcpy(config->database.events_db_path, "hal_events.db");
    
    val = find_value(json, "buffer_size");
    if (val) config->database.buffer_size = atoi(val);
    else config->database.buffer_size = 10000;
    
    val = find_value(json, "server_url");
    if (val) strncpy(config->ambient_ai.server_url, val, 255);
    
    val = find_value(json, "api_endpoint");
    if (val) strncpy(config->ambient_ai.api_endpoint, val, 255);
    
    val = find_value(json, "door_unlock_time_ms");
    if (val) config->hardware.door_unlock_time_ms = atoi(val);
    else config->hardware.door_unlock_time_ms = 5000;
    
    config->door_count = 3;
    config->doors[0].id = 1;
    strcpy(config->doors[0].name, "Main Entrance");
    config->doors[0].relay_id = 1;
    
    config->doors[1].id = 2;
    strcpy(config->doors[1].name, "Server Room");
    config->doors[1].relay_id = 2;
    
    config->doors[2].id = 3;
    strcpy(config->doors[2].name, "Back Door");
    config->doors[2].relay_id = 3;
    
    config->ambient_ai.enabled = true;
    
    free(json);
    printf("Configuration loaded from %s\n", config_path);
    return config;
}

void Config_Print(HALConfig_t* config) {
    if (!config) return;
    
    printf("\n=== HAL Configuration ===\n");
    printf("System Name: %s\n", config->system.name);
    printf("Location: %s\n", config->system.location);
    printf("Database: %s\n", config->database.events_db_path);
    printf("Buffer Size: %d\n", config->database.buffer_size);
    printf("Ambient.ai: %s\n", config->ambient_ai.enabled ? "Enabled" : "Disabled");
    if (config->ambient_ai.enabled) {
        printf("  Server: %s%s\n", config->ambient_ai.server_url, config->ambient_ai.api_endpoint);
    }
    printf("Door Unlock Time: %dms\n", config->hardware.door_unlock_time_ms);
    printf("\nDoors Configured: %d\n", config->door_count);
    for (int i = 0; i < config->door_count; i++) {
        printf("  Door %d: %s (Relay %d)\n", 
               config->doors[i].id, 
               config->doors[i].name, 
               config->doors[i].relay_id);
    }
    printf("========================\n\n");
}

void Config_Free(HALConfig_t* config) {
    if (config) free(config);
}
