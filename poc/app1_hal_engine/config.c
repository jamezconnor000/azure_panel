/**
 * @file config.c
 * @brief Configuration loader implementation
 *
 * @author FAM-HAL-v1.0-001
 * @date February 10, 2026
 */

#include "config.h"
#include "cJSON.h"
#include "json_serializer.h"
#include "logger.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

void config_get_defaults(hal_engine_config_t* config) {
    if (!config) return;

    memset(config, 0, sizeof(hal_engine_config_t));

    /* Database */
    strcpy(config->db_path, "./data/cards.db");

    /* IPC */
    strcpy(config->socket_path, "/tmp/hal_events.sock");
    config->buffer_size = 4096;

    /* Reader */
    strcpy(config->device_uid, "62023ea7-3968-4f74-b948-1e3d821dc939");
    strcpy(config->device_name, "Front Door Reader");
    config->reader_port = 1;

    /* Alarm UUIDs */
    strcpy(config->alarm_uid_granted, "12634ea7-3968-4f74-b948-1e3d821dc939");
    strcpy(config->alarm_uid_denied, "22634ea7-3968-4f74-b948-1e3d821dc939");

    /* Wiegand */
    config->default_facility_code = 100;
    config->facility_code_check = false;

    /* Access logic */
    config->check_timezone = false;
    config->check_anti_passback = false;
    config->grant_time_ms = 5000;

    /* Simulation */
    config->simulation_enabled = true;
    strcpy(config->sim_fifo_path, "/tmp/hal_sim_wiegand");

    /* Logging */
    strcpy(config->log_file, "./logs/hal_engine.log");
    config->log_level = LOG_LEVEL_DEBUG;
    config->log_console = true;
}

int config_load(const char* config_path, hal_engine_config_t* config) {
    if (!config_path || !config) {
        return -1;
    }

    /* Start with defaults */
    config_get_defaults(config);

    /* Read file */
    FILE* fp = fopen(config_path, "r");
    if (!fp) {
        LOG_WARN("Config file not found: %s, using defaults", config_path);
        return 0;  /* Not an error, just use defaults */
    }

    fseek(fp, 0, SEEK_END);
    long file_size = ftell(fp);
    fseek(fp, 0, SEEK_SET);

    char* json_str = malloc(file_size + 1);
    if (!json_str) {
        fclose(fp);
        return -1;
    }

    size_t read = fread(json_str, 1, file_size, fp);
    json_str[read] = '\0';
    fclose(fp);

    /* Parse JSON */
    cJSON* root = cJSON_Parse(json_str);
    free(json_str);

    if (!root) {
        LOG_ERROR("Failed to parse config file");
        return -1;
    }

    /* Database section */
    cJSON* db = cJSON_GetObjectItem(root, "database");
    if (db) {
        json_get_string(db, "path", config->db_path, sizeof(config->db_path));
    }

    /* IPC section */
    cJSON* ipc = cJSON_GetObjectItem(root, "ipc");
    if (ipc) {
        json_get_string(ipc, "socket_path", config->socket_path, sizeof(config->socket_path));
        json_get_int(ipc, "buffer_size", &config->buffer_size);
    }

    /* Reader section */
    cJSON* reader = cJSON_GetObjectItem(root, "reader");
    if (reader) {
        json_get_string(reader, "device_uid", config->device_uid, sizeof(config->device_uid));
        json_get_string(reader, "device_name", config->device_name, sizeof(config->device_name));
        json_get_int(reader, "port", &config->reader_port);
    }

    /* Alarm UUIDs section */
    cJSON* alarms = cJSON_GetObjectItem(root, "alarm_uids");
    if (alarms) {
        json_get_string(alarms, "access_granted", config->alarm_uid_granted, sizeof(config->alarm_uid_granted));
        json_get_string(alarms, "access_denied", config->alarm_uid_denied, sizeof(config->alarm_uid_denied));
    }

    /* Wiegand section */
    cJSON* wiegand = cJSON_GetObjectItem(root, "wiegand");
    if (wiegand) {
        json_get_int(wiegand, "default_facility_code", &config->default_facility_code);
        json_get_bool(wiegand, "facility_code_check", &config->facility_code_check);
    }

    /* Access logic section */
    cJSON* access = cJSON_GetObjectItem(root, "access_logic");
    if (access) {
        json_get_bool(access, "check_timezone", &config->check_timezone);
        json_get_bool(access, "check_anti_passback", &config->check_anti_passback);
        json_get_int(access, "default_grant_time_ms", &config->grant_time_ms);
    }

    /* Simulation section */
    cJSON* sim = cJSON_GetObjectItem(root, "simulation");
    if (sim) {
        json_get_bool(sim, "enabled", &config->simulation_enabled);
        json_get_string(sim, "fifo_path", config->sim_fifo_path, sizeof(config->sim_fifo_path));
    }

    /* Logging section */
    cJSON* logging = cJSON_GetObjectItem(root, "logging");
    if (logging) {
        json_get_string(logging, "file", config->log_file, sizeof(config->log_file));
        json_get_bool(logging, "console", &config->log_console);

        char level_str[16] = {0};
        if (json_get_string(logging, "level", level_str, sizeof(level_str)) == 0) {
            config->log_level = logger_parse_level(level_str);
        }
    }

    cJSON_Delete(root);
    LOG_INFO("Configuration loaded from %s", config_path);
    return 0;
}

void config_print(const hal_engine_config_t* config) {
    if (!config) return;

    LOG_INFO("=== HAL Engine Configuration ===");
    LOG_INFO("Database: %s", config->db_path);
    LOG_INFO("IPC Socket: %s", config->socket_path);
    LOG_INFO("Reader: %s (port %d)", config->device_name, config->reader_port);
    LOG_INFO("Device UID: %s", config->device_uid);
    LOG_INFO("Default FC: %d", config->default_facility_code);
    LOG_INFO("Simulation: %s", config->simulation_enabled ? "enabled" : "disabled");
    LOG_INFO("Log level: %s", logger_level_name(config->log_level));
    LOG_INFO("================================");
}
