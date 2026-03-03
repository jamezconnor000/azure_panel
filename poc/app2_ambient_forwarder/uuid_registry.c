/**
 * @file uuid_registry.c
 * @brief UUID registry implementation
 *
 * @author FAM-HAL-v1.0-001
 * @date February 10, 2026
 */

#include "uuid_registry.h"
#include "logger.h"
#include "cJSON.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* ============================================================================
 * Static State
 * ========================================================================== */

#define MAX_DEVICES 64
#define MAX_ALARMS  16

typedef struct {
    event_type_t event_type;
    char uid[UUID_STRING_LEN];
    char name[64];
} alarm_mapping_t;

static char s_source_system_uid[UUID_STRING_LEN] = {0};
static char s_source_system_name[64] = {0};

static device_entry_t s_devices[MAX_DEVICES];
static int s_device_count = 0;

static alarm_mapping_t s_alarms[MAX_ALARMS];
static int s_alarm_count = 0;

static bool s_initialized = false;

/* ============================================================================
 * Internal Functions
 * ========================================================================== */

static event_type_t parse_event_type(const char* type_str) {
    if (!type_str) return EVENT_UNKNOWN;

    if (strcmp(type_str, "access_granted") == 0) return EVENT_ACCESS_GRANTED;
    if (strcmp(type_str, "access_denied") == 0) return EVENT_ACCESS_DENIED;
    if (strcmp(type_str, "door_held_open") == 0) return EVENT_DOOR_HELD_OPEN;
    if (strcmp(type_str, "door_forced") == 0) return EVENT_DOOR_FORCED;
    if (strcmp(type_str, "tamper") == 0) return EVENT_TAMPER;
    if (strcmp(type_str, "heartbeat") == 0) return EVENT_HEARTBEAT;

    return EVENT_UNKNOWN;
}

static int load_config_file(const char* path, cJSON** root) {
    FILE* f = fopen(path, "r");
    if (!f) {
        LOG_ERROR("Failed to open config file: %s", path);
        return -1;
    }

    fseek(f, 0, SEEK_END);
    long size = ftell(f);
    fseek(f, 0, SEEK_SET);

    char* buffer = malloc(size + 1);
    if (!buffer) {
        fclose(f);
        return -1;
    }

    fread(buffer, 1, size, f);
    buffer[size] = '\0';
    fclose(f);

    *root = cJSON_Parse(buffer);
    free(buffer);

    if (!*root) {
        LOG_ERROR("Failed to parse JSON: %s", path);
        return -1;
    }

    return 0;
}

/* ============================================================================
 * Public Functions
 * ========================================================================== */

int uuid_registry_init(const char* config_path) {
    if (s_initialized) {
        return 0;
    }

    if (!config_path) {
        LOG_ERROR("UUID registry config path is NULL");
        return -1;
    }

    cJSON* root = NULL;
    if (load_config_file(config_path, &root) != 0) {
        return -1;
    }

    /* Parse source system */
    cJSON* source = cJSON_GetObjectItem(root, "source_system");
    if (source) {
        cJSON* uid = cJSON_GetObjectItem(source, "uid");
        cJSON* name = cJSON_GetObjectItem(source, "name");

        if (uid && cJSON_IsString(uid)) {
            strncpy(s_source_system_uid, uid->valuestring, UUID_STRING_LEN - 1);
        }
        if (name && cJSON_IsString(name)) {
            strncpy(s_source_system_name, name->valuestring, sizeof(s_source_system_name) - 1);
        }
    }

    /* Parse devices */
    cJSON* devices = cJSON_GetObjectItem(root, "devices");
    if (devices && cJSON_IsArray(devices)) {
        s_device_count = 0;
        cJSON* device;
        cJSON_ArrayForEach(device, devices) {
            if (s_device_count >= MAX_DEVICES) break;

            device_entry_t* entry = &s_devices[s_device_count];
            memset(entry, 0, sizeof(device_entry_t));

            cJSON* port = cJSON_GetObjectItem(device, "port");
            cJSON* uid = cJSON_GetObjectItem(device, "uid");
            cJSON* name = cJSON_GetObjectItem(device, "name");
            cJSON* type = cJSON_GetObjectItem(device, "type");

            if (port && cJSON_IsNumber(port)) {
                entry->port = port->valueint;
            }
            if (uid && cJSON_IsString(uid)) {
                strncpy(entry->device_uid, uid->valuestring, UUID_STRING_LEN - 1);
            }
            if (name && cJSON_IsString(name)) {
                strncpy(entry->device_name, name->valuestring, DEVICE_NAME_MAX_LEN - 1);
            }
            if (type && cJSON_IsString(type)) {
                /* Parse device type - for now, default to READER */
                entry->device_type = DEVICE_TYPE_READER;
            }
            entry->enabled = true;

            s_device_count++;
        }
    }

    /* Parse alarm mappings */
    cJSON* alarms = cJSON_GetObjectItem(root, "alarms");
    if (alarms && cJSON_IsArray(alarms)) {
        s_alarm_count = 0;
        cJSON* alarm;
        cJSON_ArrayForEach(alarm, alarms) {
            if (s_alarm_count >= MAX_ALARMS) break;

            alarm_mapping_t* mapping = &s_alarms[s_alarm_count];
            memset(mapping, 0, sizeof(alarm_mapping_t));

            cJSON* type = cJSON_GetObjectItem(alarm, "type");
            cJSON* uid = cJSON_GetObjectItem(alarm, "uid");
            cJSON* name = cJSON_GetObjectItem(alarm, "name");

            if (type && cJSON_IsString(type)) {
                mapping->event_type = parse_event_type(type->valuestring);
            }
            if (uid && cJSON_IsString(uid)) {
                strncpy(mapping->uid, uid->valuestring, UUID_STRING_LEN - 1);
            }
            if (name && cJSON_IsString(name)) {
                strncpy(mapping->name, name->valuestring, sizeof(mapping->name) - 1);
            }

            s_alarm_count++;
        }
    }

    cJSON_Delete(root);

    s_initialized = true;
    LOG_INFO("UUID registry initialized: %d devices, %d alarms", s_device_count, s_alarm_count);

    return 0;
}

void uuid_registry_shutdown(void) {
    if (!s_initialized) {
        return;
    }

    s_device_count = 0;
    s_alarm_count = 0;
    s_initialized = false;

    LOG_INFO("UUID registry shutdown");
}

const char* uuid_registry_get_source_system(void) {
    return s_source_system_uid;
}

const char* uuid_registry_get_source_name(void) {
    return s_source_system_name;
}

const char* uuid_registry_get_alarm_uid(event_type_t event_type) {
    for (int i = 0; i < s_alarm_count; i++) {
        if (s_alarms[i].event_type == event_type) {
            return s_alarms[i].uid;
        }
    }
    return NULL;
}

const char* uuid_registry_get_alarm_name(event_type_t event_type) {
    for (int i = 0; i < s_alarm_count; i++) {
        if (s_alarms[i].event_type == event_type) {
            return s_alarms[i].name;
        }
    }
    return NULL;
}

int uuid_registry_get_device(int port, device_entry_t* device) {
    for (int i = 0; i < s_device_count; i++) {
        if (s_devices[i].port == port) {
            if (device) {
                memcpy(device, &s_devices[i], sizeof(device_entry_t));
            }
            return 0;
        }
    }
    return -1;
}
