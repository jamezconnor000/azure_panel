/**
 * @file uuid_registry.h
 * @brief UUID registry for device and alarm mappings
 *
 * @author FAM-HAL-v1.0-001
 * @date February 10, 2026
 */

#ifndef POC_UUID_REGISTRY_H
#define POC_UUID_REGISTRY_H

#include "event_types.h"
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief Initialize the UUID registry from config file
 *
 * @param config_path   Path to devices.json
 * @return              0 on success, -1 on error
 */
int uuid_registry_init(const char* config_path);

/**
 * @brief Shutdown the UUID registry
 */
void uuid_registry_shutdown(void);

/**
 * @brief Get source system UUID
 *
 * @return              Source system UUID string
 */
const char* uuid_registry_get_source_system(void);

/**
 * @brief Get source system name
 *
 * @return              Source system name
 */
const char* uuid_registry_get_source_name(void);

/**
 * @brief Get alarm UUID by event type
 *
 * @param event_type    Event type
 * @return              Alarm UUID string, or NULL if not found
 */
const char* uuid_registry_get_alarm_uid(event_type_t event_type);

/**
 * @brief Get alarm name by event type
 *
 * @param event_type    Event type
 * @return              Alarm name string, or NULL if not found
 */
const char* uuid_registry_get_alarm_name(event_type_t event_type);

/**
 * @brief Get device info by port
 *
 * @param port          Physical port number
 * @param device        Output: device entry (can be NULL)
 * @return              0 if found, -1 if not found
 */
int uuid_registry_get_device(int port, device_entry_t* device);

#ifdef __cplusplus
}
#endif

#endif /* POC_UUID_REGISTRY_H */
