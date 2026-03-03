/**
 * @file config.h
 * @brief Configuration loader for HAL engine
 *
 * @author FAM-HAL-v1.0-001
 * @date February 10, 2026
 */

#ifndef POC_HAL_ENGINE_CONFIG_H
#define POC_HAL_ENGINE_CONFIG_H

#include "hal_engine.h"

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief Load HAL engine configuration from JSON file
 *
 * @param config_path   Path to JSON configuration file
 * @param config        Output: populated configuration structure
 * @return              0 on success, -1 on error
 */
int config_load(const char* config_path, hal_engine_config_t* config);

/**
 * @brief Get default configuration values
 *
 * @param config        Output: configuration with defaults
 */
void config_get_defaults(hal_engine_config_t* config);

/**
 * @brief Print configuration to log
 *
 * @param config        Configuration to print
 */
void config_print(const hal_engine_config_t* config);

#ifdef __cplusplus
}
#endif

#endif /* POC_HAL_ENGINE_CONFIG_H */
