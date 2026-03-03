/**
 * @file json_serializer.h
 * @brief JSON serialization/deserialization for HAL events
 *
 * Provides functions to convert hal_event_t structures to/from JSON
 * for IPC communication and Ambient.ai API calls.
 *
 * @author FAM-HAL-v1.0-001
 * @date February 10, 2026
 */

#ifndef POC_JSON_SERIALIZER_H
#define POC_JSON_SERIALIZER_H

#include "event_types.h"
#include "cJSON.h"

#ifdef __cplusplus
extern "C" {
#endif

/* ============================================================================
 * Event Serialization
 * ========================================================================== */

/**
 * @brief Serialize a HAL event to JSON string
 *
 * Creates a JSON object representing the event and returns it as a string.
 * The caller is responsible for freeing the returned string.
 *
 * @param event     Pointer to the event to serialize
 * @return          Allocated JSON string, or NULL on error. Caller must free().
 */
char* event_to_json(const hal_event_t* event);

/**
 * @brief Serialize a HAL event to cJSON object
 *
 * Creates a cJSON object representing the event. Caller owns the object.
 *
 * @param event     Pointer to the event to serialize
 * @return          cJSON object, or NULL on error. Caller must cJSON_Delete().
 */
cJSON* event_to_cjson(const hal_event_t* event);

/**
 * @brief Deserialize a JSON string to HAL event
 *
 * Parses a JSON string and populates the event structure.
 *
 * @param json      JSON string to parse
 * @param event     Pointer to event structure to populate
 * @return          0 on success, -1 on error
 */
int json_to_event(const char* json, hal_event_t* event);

/**
 * @brief Deserialize a cJSON object to HAL event
 *
 * @param json_obj  cJSON object to parse
 * @param event     Pointer to event structure to populate
 * @return          0 on success, -1 on error
 */
int cjson_to_event(const cJSON* json_obj, hal_event_t* event);

/* ============================================================================
 * IPC Message Serialization
 * ========================================================================== */

/**
 * @brief Wrap an event in an IPC message envelope
 *
 * Creates a complete IPC message with type, version, and payload.
 *
 * @param event     Pointer to the event
 * @param msg_type  IPC message type
 * @return          Allocated JSON string, or NULL on error. Caller must free().
 */
char* create_ipc_message(const hal_event_t* event, ipc_msg_type_t msg_type);

/**
 * @brief Parse an IPC message and extract the event
 *
 * @param json      JSON string of the IPC message
 * @param event     Pointer to event structure to populate
 * @param msg_type  Output: the message type (can be NULL)
 * @return          0 on success, -1 on error
 */
int parse_ipc_message(const char* json, hal_event_t* event, ipc_msg_type_t* msg_type);

/* ============================================================================
 * Ambient.ai Format Serialization
 * ========================================================================== */

/**
 * @brief Serialize event to Ambient.ai API format
 *
 * Creates JSON matching the Ambient.ai Generic Cloud Event Ingestion spec.
 *
 * @param event             Pointer to the event
 * @param source_system_uid Source system UUID
 * @return                  Allocated JSON string, or NULL on error. Caller must free().
 */
char* event_to_ambient_json(const hal_event_t* event, const char* source_system_uid);

/* ============================================================================
 * Card/Device Serialization
 * ========================================================================== */

/**
 * @brief Serialize card info to JSON string
 *
 * @param card      Pointer to card info structure
 * @return          Allocated JSON string, or NULL on error. Caller must free().
 */
char* card_info_to_json(const card_info_t* card);

/**
 * @brief Deserialize JSON to card info
 *
 * @param json      JSON string to parse
 * @param card      Pointer to card info structure to populate
 * @return          0 on success, -1 on error
 */
int json_to_card_info(const char* json, card_info_t* card);

/**
 * @brief Serialize device entry to JSON string
 *
 * @param device    Pointer to device entry structure
 * @return          Allocated JSON string, or NULL on error. Caller must free().
 */
char* device_entry_to_json(const device_entry_t* device);

/* ============================================================================
 * Utility Functions
 * ========================================================================== */

/**
 * @brief Get a string value from a cJSON object safely
 *
 * @param obj       Parent cJSON object
 * @param key       Key name to look up
 * @param dest      Destination buffer
 * @param max_len   Maximum length of destination buffer
 * @return          0 on success, -1 if key not found or not a string
 */
int json_get_string(const cJSON* obj, const char* key, char* dest, size_t max_len);

/**
 * @brief Get an integer value from a cJSON object safely
 *
 * @param obj       Parent cJSON object
 * @param key       Key name to look up
 * @param dest      Pointer to destination integer
 * @return          0 on success, -1 if key not found or not a number
 */
int json_get_int(const cJSON* obj, const char* key, int* dest);

/**
 * @brief Get a 64-bit integer value from a cJSON object safely
 *
 * @param obj       Parent cJSON object
 * @param key       Key name to look up
 * @param dest      Pointer to destination 64-bit integer
 * @return          0 on success, -1 if key not found or not a number
 */
int json_get_int64(const cJSON* obj, const char* key, int64_t* dest);

/**
 * @brief Get a boolean value from a cJSON object safely
 *
 * @param obj       Parent cJSON object
 * @param key       Key name to look up
 * @param dest      Pointer to destination boolean
 * @return          0 on success, -1 if key not found or not a boolean
 */
int json_get_bool(const cJSON* obj, const char* key, bool* dest);

#ifdef __cplusplus
}
#endif

#endif /* POC_JSON_SERIALIZER_H */
