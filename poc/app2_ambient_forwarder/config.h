/**
 * @file config.h
 * @brief Forwarder configuration management
 *
 * @author FAM-HAL-v1.0-001
 * @date February 10, 2026
 */

#ifndef POC_FORWARDER_CONFIG_H
#define POC_FORWARDER_CONFIG_H

#include "forwarder.h"
#include <stdbool.h>
#include <stdint.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

/* forwarder_config_t is defined in forwarder.h */

/**
 * @brief Load forwarder configuration
 *
 * @param path      Path to config file
 * @param config    Output configuration
 * @return          0 on success, -1 on error
 */
int forwarder_config_load(const char* path, forwarder_config_t* config);

/**
 * @brief Initialize default configuration
 *
 * @param config    Configuration to initialize
 */
void forwarder_config_defaults(forwarder_config_t* config);

/**
 * @brief Validate configuration
 *
 * @param config    Configuration to validate
 * @return          0 if valid, -1 if invalid
 */
int forwarder_config_validate(const forwarder_config_t* config);

/**
 * @brief Print configuration (for debugging)
 *
 * @param config    Configuration to print
 */
void forwarder_config_print(const forwarder_config_t* config);

#ifdef __cplusplus
}
#endif

#endif /* POC_FORWARDER_CONFIG_H */
