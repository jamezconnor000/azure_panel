/**
 * @file hal_engine.h
 * @brief HAL Access Engine - Main interface
 *
 * Provides the core HAL engine functionality for processing Wiegand
 * badge reads and generating access events.
 *
 * @author FAM-HAL-v1.0-001
 * @date February 10, 2026
 */

#ifndef POC_HAL_ENGINE_H
#define POC_HAL_ENGINE_H

#include "event_types.h"
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

/* ============================================================================
 * Engine Configuration
 * ========================================================================== */

/**
 * @brief HAL engine configuration
 */
typedef struct {
    /* Database */
    char db_path[256];

    /* IPC */
    char socket_path[108];
    int buffer_size;

    /* Reader */
    char device_uid[UUID_STRING_LEN];
    char device_name[DEVICE_NAME_MAX_LEN];
    int reader_port;

    /* Alarm UUIDs */
    char alarm_uid_granted[UUID_STRING_LEN];
    char alarm_uid_denied[UUID_STRING_LEN];

    /* Wiegand */
    int default_facility_code;
    bool facility_code_check;

    /* Access logic */
    bool check_timezone;
    bool check_anti_passback;
    int grant_time_ms;

    /* Simulation */
    bool simulation_enabled;
    char sim_fifo_path[256];

    /* Logging */
    char log_file[256];
    int log_level;
    bool log_console;
} hal_engine_config_t;

/* ============================================================================
 * Engine Lifecycle
 * ========================================================================== */

/**
 * @brief Initialize the HAL engine
 *
 * @param config    Engine configuration
 * @return          0 on success, -1 on error
 */
int hal_engine_init(const hal_engine_config_t* config);

/**
 * @brief Start the HAL engine
 *
 * Starts the event processing loop. This function blocks until
 * hal_engine_stop() is called.
 *
 * @return          0 on normal exit, -1 on error
 */
int hal_engine_run(void);

/**
 * @brief Signal the engine to stop
 *
 * Thread-safe. Can be called from a signal handler.
 */
void hal_engine_stop(void);

/**
 * @brief Shutdown the HAL engine
 *
 * Releases all resources.
 */
void hal_engine_shutdown(void);

/**
 * @brief Check if engine is running
 *
 * @return          true if running
 */
bool hal_engine_is_running(void);

/* ============================================================================
 * Event Processing
 * ========================================================================== */

/**
 * @brief Process a Wiegand card read
 *
 * This is the main entry point for card reads. It will:
 * 1. Parse the Wiegand data
 * 2. Look up the card in the database
 * 3. Make an access decision
 * 4. Generate and publish an event
 *
 * @param facility_code     Wiegand facility code
 * @param card_number       Wiegand card number
 * @return                  0 on success, -1 on error
 */
int hal_engine_process_card(uint32_t facility_code, uint32_t card_number);

/**
 * @brief Inject a simulated card read
 *
 * For testing purposes. Simulates a badge read.
 *
 * @param facility_code     Wiegand facility code
 * @param card_number       Wiegand card number
 * @return                  0 on success, -1 on error
 */
int hal_engine_simulate_badge(uint32_t facility_code, uint32_t card_number);

/* ============================================================================
 * Statistics
 * ========================================================================== */

/**
 * @brief Engine statistics
 */
typedef struct {
    uint64_t cards_processed;       /* Total cards processed */
    uint64_t access_granted;        /* Access granted count */
    uint64_t access_denied;         /* Access denied count */
    uint64_t events_published;      /* Events sent to IPC */
    uint64_t events_failed;         /* Failed event publishes */
    int64_t uptime_seconds;         /* Engine uptime */
    int64_t last_event_time;        /* Timestamp of last event */
} hal_engine_stats_t;

/**
 * @brief Get engine statistics
 *
 * @param stats     Output: statistics structure
 */
void hal_engine_get_stats(hal_engine_stats_t* stats);

/**
 * @brief Reset engine statistics
 */
void hal_engine_reset_stats(void);

#ifdef __cplusplus
}
#endif

#endif /* POC_HAL_ENGINE_H */
