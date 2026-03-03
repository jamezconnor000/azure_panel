/**
 * @file retry_queue.h
 * @brief Retry queue for failed events
 *
 * SQLite-based persistent queue for events that failed to send.
 *
 * @author FAM-HAL-v1.0-001
 * @date February 10, 2026
 */

#ifndef POC_RETRY_QUEUE_H
#define POC_RETRY_QUEUE_H

#include "event_types.h"
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief Initialize the retry queue
 *
 * @param db_path       Path to SQLite database
 * @param max_size      Maximum queue size
 * @return              0 on success, -1 on error
 */
int retry_queue_init(const char* db_path, int max_size);

/**
 * @brief Close the retry queue
 */
void retry_queue_close(void);

/**
 * @brief Add an event to the retry queue
 *
 * @param event         Event to queue
 * @return              0 on success, -1 on error
 */
int retry_queue_push(const hal_event_t* event);

/**
 * @brief Get the next event to retry
 *
 * @param event         Output: event data
 * @param id            Output: queue entry ID (for removal)
 * @return              0 if event available, 1 if queue empty, -1 on error
 */
int retry_queue_peek(hal_event_t* event, int64_t* id);

/**
 * @brief Remove an event from the queue
 *
 * @param id            Queue entry ID
 * @return              0 on success, -1 on error
 */
int retry_queue_remove(int64_t id);

/**
 * @brief Get queue size
 *
 * @return              Number of events in queue
 */
int retry_queue_size(void);

/**
 * @brief Clear all events from queue
 *
 * @return              Number of events removed
 */
int retry_queue_clear(void);

/**
 * @brief Check if queue is initialized
 */
bool retry_queue_is_open(void);

#ifdef __cplusplus
}
#endif

#endif /* POC_RETRY_QUEUE_H */
