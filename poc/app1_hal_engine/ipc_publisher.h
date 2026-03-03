/**
 * @file ipc_publisher.h
 * @brief IPC publisher for event distribution
 *
 * Server-side Unix Domain Socket implementation for publishing
 * events to subscribers.
 *
 * @author FAM-HAL-v1.0-001
 * @date February 10, 2026
 */

#ifndef POC_IPC_PUBLISHER_H
#define POC_IPC_PUBLISHER_H

#include "event_types.h"
#include "ipc_common.h"
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief Initialize the IPC publisher
 *
 * Creates and binds the Unix Domain Socket.
 *
 * @param socket_path   Path to the socket file
 * @return              0 on success, -1 on error
 */
int ipc_publisher_init(const char* socket_path);

/**
 * @brief Shutdown the IPC publisher
 *
 * Closes all connections and removes the socket file.
 */
void ipc_publisher_shutdown(void);

/**
 * @brief Accept pending connections
 *
 * Non-blocking check for new subscriber connections.
 * Should be called periodically from the main loop.
 *
 * @return              Number of new connections accepted
 */
int ipc_publisher_accept(void);

/**
 * @brief Publish an event to all subscribers
 *
 * @param event         Event to publish
 * @return              Number of subscribers that received the event
 */
int ipc_publisher_publish(const hal_event_t* event);

/**
 * @brief Publish raw JSON message to all subscribers
 *
 * @param json          JSON message to publish
 * @return              Number of subscribers that received the message
 */
int ipc_publisher_publish_raw(const char* json);

/**
 * @brief Get the number of connected subscribers
 *
 * @return              Number of active connections
 */
int ipc_publisher_subscriber_count(void);

/**
 * @brief Check if publisher is initialized
 *
 * @return              true if initialized and listening
 */
bool ipc_publisher_is_ready(void);

/**
 * @brief Get publisher statistics
 *
 * @param messages_sent     Output: total messages sent
 * @param bytes_sent        Output: total bytes sent
 * @param subscribers       Output: current subscriber count
 */
void ipc_publisher_get_stats(uint64_t* messages_sent, uint64_t* bytes_sent,
                             int* subscribers);

#ifdef __cplusplus
}
#endif

#endif /* POC_IPC_PUBLISHER_H */
