/**
 * @file config.c
 * @brief Forwarder configuration implementation
 *
 * @author FAM-HAL-v1.0-001
 * @date February 10, 2026
 */

#include "config.h"
#include "logger.h"
#include "cJSON.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* ============================================================================
 * Public Functions
 * ========================================================================== */

void forwarder_config_defaults(forwarder_config_t* config) {
    if (!config) return;

    memset(config, 0, sizeof(forwarder_config_t));

    /* IPC defaults */
    strcpy(config->ipc_socket_path, "/tmp/hal_events.sock");
    config->ipc_reconnect_delay_ms = 5000;

    /* Ambient defaults */
    strcpy(config->ambient_endpoint, "https://pacs-ingestion.ambient.ai/api/generic-cloud/event");
    config->ambient_timeout_ms = 10000;
    config->ambient_verify_ssl = true;
    strcpy(config->user_agent, "HAL-Forwarder/1.0");

    /* Retry defaults */
    strcpy(config->retry_db_path, "/var/lib/hal/retry_queue.db");
    config->retry_max_queue_size = 10000;
    config->retry_interval_sec = 30;
    config->retry_max_attempts = 10;

    /* UUID registry */
    strcpy(config->devices_config_path, "/etc/hal/devices.json");

    /* Logging defaults */
    strcpy(config->log_file, "/var/log/hal/forwarder.log");
    config->log_level = 2;  /* LOG_INFO */
    config->log_max_files = 5;
    config->log_max_size = 10 * 1024 * 1024;
}

int forwarder_config_load(const char* path, forwarder_config_t* config) {
    if (!path || !config) {
        return -1;
    }

    /* Start with defaults */
    forwarder_config_defaults(config);

    FILE* f = fopen(path, "r");
    if (!f) {
        LOG_WARN("Config file not found: %s, using defaults", path);
        return 0;
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

    cJSON* root = cJSON_Parse(buffer);
    free(buffer);

    if (!root) {
        LOG_ERROR("Failed to parse config JSON");
        return -1;
    }

    /* Parse IPC section */
    cJSON* ipc = cJSON_GetObjectItem(root, "ipc");
    if (ipc) {
        cJSON* item;
        if ((item = cJSON_GetObjectItem(ipc, "socket_path")) && cJSON_IsString(item)) {
            strncpy(config->ipc_socket_path, item->valuestring, sizeof(config->ipc_socket_path) - 1);
        }
        if ((item = cJSON_GetObjectItem(ipc, "reconnect_delay_ms")) && cJSON_IsNumber(item)) {
            config->ipc_reconnect_delay_ms = item->valueint;
        }
    }

    /* Parse Ambient section */
    cJSON* ambient = cJSON_GetObjectItem(root, "ambient");
    if (ambient) {
        cJSON* item;
        if ((item = cJSON_GetObjectItem(ambient, "endpoint")) && cJSON_IsString(item)) {
            strncpy(config->ambient_endpoint, item->valuestring, sizeof(config->ambient_endpoint) - 1);
        }
        if ((item = cJSON_GetObjectItem(ambient, "api_key")) && cJSON_IsString(item)) {
            strncpy(config->ambient_api_key, item->valuestring, sizeof(config->ambient_api_key) - 1);
        }
        if ((item = cJSON_GetObjectItem(ambient, "timeout_ms")) && cJSON_IsNumber(item)) {
            config->ambient_timeout_ms = item->valueint;
        }
        if ((item = cJSON_GetObjectItem(ambient, "verify_ssl")) && cJSON_IsBool(item)) {
            config->ambient_verify_ssl = cJSON_IsTrue(item);
        }
        if ((item = cJSON_GetObjectItem(ambient, "user_agent")) && cJSON_IsString(item)) {
            strncpy(config->user_agent, item->valuestring, sizeof(config->user_agent) - 1);
        }
    }

    /* Parse Retry section */
    cJSON* retry = cJSON_GetObjectItem(root, "retry");
    if (retry) {
        cJSON* item;
        if ((item = cJSON_GetObjectItem(retry, "db_path")) && cJSON_IsString(item)) {
            strncpy(config->retry_db_path, item->valuestring, sizeof(config->retry_db_path) - 1);
        }
        if ((item = cJSON_GetObjectItem(retry, "max_queue_size")) && cJSON_IsNumber(item)) {
            config->retry_max_queue_size = item->valueint;
        }
        if ((item = cJSON_GetObjectItem(retry, "interval_sec")) && cJSON_IsNumber(item)) {
            config->retry_interval_sec = item->valueint;
        }
        if ((item = cJSON_GetObjectItem(retry, "max_attempts")) && cJSON_IsNumber(item)) {
            config->retry_max_attempts = item->valueint;
        }
    }

    /* Parse UUID registry path */
    cJSON* devices = cJSON_GetObjectItem(root, "devices_config");
    if (devices && cJSON_IsString(devices)) {
        strncpy(config->devices_config_path, devices->valuestring, sizeof(config->devices_config_path) - 1);
    }

    /* Parse Logging section */
    cJSON* logging = cJSON_GetObjectItem(root, "logging");
    if (logging) {
        cJSON* item;
        if ((item = cJSON_GetObjectItem(logging, "file")) && cJSON_IsString(item)) {
            strncpy(config->log_file, item->valuestring, sizeof(config->log_file) - 1);
        }
        if ((item = cJSON_GetObjectItem(logging, "level")) && cJSON_IsNumber(item)) {
            config->log_level = item->valueint;
        }
        if ((item = cJSON_GetObjectItem(logging, "max_files")) && cJSON_IsNumber(item)) {
            config->log_max_files = item->valueint;
        }
        if ((item = cJSON_GetObjectItem(logging, "max_size_mb")) && cJSON_IsNumber(item)) {
            config->log_max_size = (size_t)item->valueint * 1024 * 1024;
        }
    }

    cJSON_Delete(root);

    LOG_INFO("Configuration loaded: %s", path);
    return 0;
}

int forwarder_config_validate(const forwarder_config_t* config) {
    if (!config) {
        return -1;
    }

    if (strlen(config->ipc_socket_path) == 0) {
        LOG_ERROR("IPC socket path is required");
        return -1;
    }

    if (strlen(config->ambient_endpoint) == 0) {
        LOG_ERROR("Ambient endpoint is required");
        return -1;
    }

    if (strlen(config->ambient_api_key) == 0) {
        LOG_ERROR("Ambient API key is required");
        return -1;
    }

    if (config->ambient_timeout_ms < 100) {
        LOG_WARN("Ambient timeout too low, using 100ms");
    }

    return 0;
}

void forwarder_config_print(const forwarder_config_t* config) {
    if (!config) return;

    printf("=== Forwarder Configuration ===\n");
    printf("IPC:\n");
    printf("  Socket Path: %s\n", config->ipc_socket_path);
    printf("  Reconnect Delay: %d ms\n", config->ipc_reconnect_delay_ms);
    printf("Ambient:\n");
    printf("  Endpoint: %s\n", config->ambient_endpoint);
    printf("  API Key: %s***\n", config->ambient_api_key[0] ? "[SET]" : "[MISSING]");
    printf("  Timeout: %d ms\n", config->ambient_timeout_ms);
    printf("  Verify SSL: %s\n", config->ambient_verify_ssl ? "yes" : "no");
    printf("Retry:\n");
    printf("  DB Path: %s\n", config->retry_db_path);
    printf("  Max Queue: %d\n", config->retry_max_queue_size);
    printf("  Interval: %d sec\n", config->retry_interval_sec);
    printf("Logging:\n");
    printf("  File: %s\n", config->log_file);
    printf("  Level: %d\n", config->log_level);
    printf("================================\n");
}
