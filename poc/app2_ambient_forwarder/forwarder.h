/**
 * @file forwarder.h
 * @brief Ambient.ai Event Forwarder - Main interface
 *
 * @author FAM-HAL-v1.0-001
 * @date February 10, 2026
 */

#ifndef POC_FORWARDER_H
#define POC_FORWARDER_H

#include "event_types.h"
#include <stdbool.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief Forwarder configuration
 */
typedef struct {
    /* IPC Settings */
    char ipc_socket_path[256];
    int ipc_reconnect_delay_ms;

    /* Ambient.ai Settings */
    char ambient_endpoint[256];
    char ambient_api_key[128];
    int ambient_timeout_ms;
    bool ambient_verify_ssl;
    char user_agent[64];

    /* Retry Settings */
    bool retry_enabled;
    char retry_db_path[256];
    int retry_max_queue_size;
    int retry_interval_sec;
    int retry_max_attempts;

    /* UUID Registry */
    char devices_config_path[256];

    /* Logging */
    char log_file[256];
    int log_level;
    int log_max_files;
    size_t log_max_size;
} forwarder_config_t;

/**
 * @brief Forwarder statistics
 */
typedef struct {
    uint64_t events_received;       /* Events received from IPC */
    uint64_t events_forwarded;      /* Successfully forwarded to Ambient.ai */
    uint64_t events_queued;         /* Events pushed to retry queue */
    uint64_t events_dropped;        /* Events that were dropped */
    uint64_t retries_attempted;     /* Total retry attempts */
    uint64_t retries_success;       /* Successful retries */
    int queue_size;                 /* Current retry queue size */
    bool connected;                 /* Connected to HAL engine */
} forwarder_stats_t;

/**
 * @brief Initialize the forwarder
 *
 * @param config    Forwarder configuration
 * @return          0 on success, -1 on error
 */
int forwarder_init(const forwarder_config_t* config);

/**
 * @brief Start the forwarder threads
 *
 * @return          0 on success, -1 on error
 */
int forwarder_start(void);

/**
 * @brief Signal the forwarder to stop
 */
void forwarder_stop(void);

/**
 * @brief Shutdown the forwarder and cleanup
 */
void forwarder_shutdown(void);

/**
 * @brief Check if forwarder is running
 */
bool forwarder_is_running(void);

/**
 * @brief Get forwarder statistics
 *
 * @param stats     Output: statistics
 */
void forwarder_get_stats(forwarder_stats_t* stats);

/**
 * @brief Print forwarder statistics to stdout
 */
void forwarder_print_stats(void);

#ifdef __cplusplus
}
#endif

#endif /* POC_FORWARDER_H */
