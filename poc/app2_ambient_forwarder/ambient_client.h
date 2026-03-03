/**
 * @file ambient_client.h
 * @brief Ambient.ai HTTP client
 *
 * @author FAM-HAL-v1.0-001
 * @date February 10, 2026
 */

#ifndef POC_AMBIENT_CLIENT_H
#define POC_AMBIENT_CLIENT_H

#include "event_types.h"
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief Ambient client configuration
 */
typedef struct {
    char endpoint[256];                 /* API endpoint URL */
    char api_key[128];                  /* API key */
    int timeout_ms;                     /* Request timeout */
    char user_agent[64];                /* User-Agent header */
    bool verify_ssl;                    /* Verify SSL certificates */
    char source_system_uid[UUID_STRING_LEN];  /* Source system UUID */
} ambient_client_config_t;

/**
 * @brief HTTP response
 */
typedef struct {
    int status_code;                    /* HTTP status code */
    char error_message[256];            /* Error message if failed */
    int64_t latency_ms;                 /* Request latency */
} ambient_response_t;

/**
 * @brief Initialize the Ambient client
 *
 * @param config    Client configuration
 * @return          0 on success, -1 on error
 */
int ambient_client_init(const ambient_client_config_t* config);

/**
 * @brief Shutdown the Ambient client
 */
void ambient_client_shutdown(void);

/**
 * @brief Send an event to Ambient.ai
 *
 * @param event     Event to send
 * @param response  Output: HTTP response (can be NULL)
 * @return          0 on success (HTTP 2xx), -1 on error
 */
int ambient_client_send_event(const hal_event_t* event, ambient_response_t* response);

/**
 * @brief Send raw JSON to Ambient.ai
 *
 * @param json      JSON payload
 * @param response  Output: HTTP response (can be NULL)
 * @return          0 on success (HTTP 2xx), -1 on error
 */
int ambient_client_send_json(const char* json, ambient_response_t* response);

/**
 * @brief Test connectivity to Ambient.ai
 *
 * Sends a simple request to verify API connectivity.
 *
 * @param latency_ms    Output: connection latency (can be NULL)
 * @return              0 if reachable, -1 if not
 */
int ambient_client_test_connection(int64_t* latency_ms);

/**
 * @brief Get client statistics
 *
 * @param requests_sent     Output: total requests sent
 * @param requests_success  Output: successful requests
 * @param requests_failed   Output: failed requests
 * @param avg_latency_ms    Output: average latency
 */
void ambient_client_get_stats(uint64_t* requests_sent, uint64_t* requests_success,
                              uint64_t* requests_failed, int64_t* avg_latency_ms);

#ifdef __cplusplus
}
#endif

#endif /* POC_AMBIENT_CLIENT_H */
