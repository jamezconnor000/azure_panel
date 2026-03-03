#ifndef EVENT_EXPORTER_H
#define EVENT_EXPORTER_H

#include "../../include/hal_types.h"
#include <stdbool.h>

/**
 * Event Exporter Module
 *
 * Automatically exports HAL events to external systems (Ambient.ai, etc.)
 * Features:
 * - Batched event delivery
 * - Configurable retry logic
 * - API key authentication
 * - Automatic acknowledgment
 */

// Export destination configuration
typedef struct {
    bool enabled;
    char server_url[256];
    char api_endpoint[256];
    char api_key[256];
    int timeout_seconds;
    int retry_attempts;
    int batch_size;
} ExportConfig_t;

// Event exporter instance
typedef struct EventExporter_t EventExporter_t;

/**
 * Create event exporter instance
 *
 * @param config Export destination configuration
 * @return Exporter instance or NULL on failure
 */
EventExporter_t* EventExporter_Create(const ExportConfig_t* config);

/**
 * Destroy event exporter
 */
void EventExporter_Destroy(EventExporter_t* exporter);

/**
 * Start the export pipeline
 * Connects to HAL and begins monitoring events
 *
 * @param exporter Exporter instance
 * @param hal_address HAL controller address
 * @param hal_port HAL controller port
 * @return ErrorCode_OK on success
 */
ErrorCode_t EventExporter_Start(EventExporter_t* exporter, const char* hal_address, uint16_t hal_port);

/**
 * Stop the export pipeline
 */
void EventExporter_Stop(EventExporter_t* exporter);

/**
 * Process events (call in main loop)
 * Retrieves events, batches them, and sends to destination
 *
 * @param exporter Exporter instance
 * @return Number of events processed, -1 on error
 */
int EventExporter_ProcessEvents(EventExporter_t* exporter);

/**
 * Get export statistics
 */
typedef struct {
    uint64_t events_received;
    uint64_t events_sent;
    uint64_t events_failed;
    uint64_t batches_sent;
    uint64_t retries_attempted;
    uint32_t last_error_code;
    char last_error_msg[256];
} ExportStats_t;

ErrorCode_t EventExporter_GetStats(EventExporter_t* exporter, ExportStats_t* stats);

/**
 * Load configuration from JSON file
 *
 * @param config_file Path to hal_config.json
 * @param out_config Output configuration
 * @return ErrorCode_OK on success
 */
ErrorCode_t EventExporter_LoadConfig(const char* config_file, ExportConfig_t* out_config);

#endif // EVENT_EXPORTER_H
