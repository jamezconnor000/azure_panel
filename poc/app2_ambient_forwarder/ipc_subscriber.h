/**
 * @file ipc_subscriber.h
 * @brief IPC subscriber for receiving events
 *
 * @author FAM-HAL-v1.0-001
 * @date February 10, 2026
 */

#ifndef POC_IPC_SUBSCRIBER_H
#define POC_IPC_SUBSCRIBER_H

#include "event_types.h"
#include "ipc_common.h"
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief Event callback function type
 */
typedef void (*event_callback_fn)(const hal_event_t* event);

/**
 * @brief Initialize the IPC subscriber
 *
 * @param callback      Callback for received events
 * @return              0 on success, -1 on error
 */
int ipc_subscriber_init(event_callback_fn callback);

/**
 * @brief Shutdown the IPC subscriber
 */
void ipc_subscriber_shutdown(void);

/**
 * @brief Connect to the publisher
 *
 * @param socket_path   Path to socket
 * @return              0 on success, -1 on error
 */
int ipc_subscriber_connect(const char* socket_path);

/**
 * @brief Poll for events with timeout
 *
 * @param timeout_ms    Timeout in milliseconds
 * @return              0 on success, -1 on error
 */
int ipc_subscriber_poll(int timeout_ms);

/**
 * @brief Disconnect from the publisher
 */
void ipc_subscriber_disconnect(void);

/**
 * @brief Check if connected to publisher
 *
 * @return              true if connected
 */
bool ipc_subscriber_is_connected(void);

/**
 * @brief Receive an event (blocking)
 *
 * @param event         Output: received event
 * @param timeout_ms    Timeout in milliseconds (0 = no timeout)
 * @return              0 on success, 1 on timeout, -1 on error
 */
int ipc_subscriber_receive(hal_event_t* event, int timeout_ms);

/**
 * @brief Receive raw JSON message (blocking)
 *
 * @param buffer        Output buffer for JSON
 * @param buf_size      Buffer size
 * @param timeout_ms    Timeout in milliseconds (0 = no timeout)
 * @return              Number of bytes received, 0 on timeout, -1 on error
 */
int ipc_subscriber_receive_raw(char* buffer, size_t buf_size, int timeout_ms);

/**
 * @brief Set event callback
 *
 * @param callback      Callback function for received events
 * @param user_data     User data passed to callback
 */
void ipc_subscriber_set_callback(ipc_event_callback_t callback, void* user_data);

/**
 * @brief Get subscriber statistics
 *
 * @param messages_received     Output: total messages received
 * @param bytes_received        Output: total bytes received
 * @param reconnects            Output: number of reconnection attempts
 */
void ipc_subscriber_get_stats(uint64_t* messages_received, uint64_t* bytes_received,
                              int* reconnects);

#ifdef __cplusplus
}
#endif

#endif /* POC_IPC_SUBSCRIBER_H */
