#ifndef JSON_CONFIG_H
#define JSON_CONFIG_H

#include "../include/hal_types.h"
#include <stdint.h>

/**
 * JSON Configuration Module
 *
 * Provides JSON export/import functionality for IntegrationApp compatibility.
 * Exports HAL database to JSON format matching Azure Panel IntegrationApp schema.
 */

// =============================================================================
// JSON Export Functions
// =============================================================================

/**
 * Export entire HAL configuration to JSON file
 *
 * Exports all data from the HAL database to a JSON file in the format
 * expected by the Azure Panel IntegrationApp.
 *
 * @param output_file Path to output JSON file
 * @return ErrorCode_OK on success
 */
ErrorCode_t HAL_ExportToJSON(const char* output_file);

/**
 * Export configuration to JSON string
 *
 * @param out_json Output buffer for JSON string (caller must free)
 * @return ErrorCode_OK on success
 */
ErrorCode_t HAL_ExportToJSONString(char** out_json);

// =============================================================================
// JSON Import Functions
// =============================================================================

/**
 * Import HAL configuration from JSON file
 *
 * Reads a JSON file in IntegrationApp format and loads it into the
 * HAL database.
 *
 * @param input_file Path to input JSON file
 * @return ErrorCode_OK on success
 */
ErrorCode_t HAL_ImportFromJSON(const char* input_file);

/**
 * Import configuration from JSON string
 *
 * @param json_string JSON string to parse
 * @return ErrorCode_OK on success
 */
ErrorCode_t HAL_ImportFromJSONString(const char* json_string);

#endif // JSON_CONFIG_H
