/**
 * @file event_producer.h
 * @brief Event production for access events
 *
 * Creates hal_event_t structures from access decisions.
 *
 * @author FAM-HAL-v1.0-001
 * @date February 10, 2026
 */

#ifndef POC_EVENT_PRODUCER_H
#define POC_EVENT_PRODUCER_H

#include "event_types.h"
#include "access_logic.h"

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief Event producer configuration
 */
typedef struct {
    char device_uid[UUID_STRING_LEN];           /* Reader device UUID */
    char device_name[DEVICE_NAME_MAX_LEN];      /* Reader name */
    int reader_port;                            /* Physical port (1-2) */
    char alarm_uid_granted[UUID_STRING_LEN];    /* Access Granted alarm UUID */
    char alarm_uid_denied[UUID_STRING_LEN];     /* Access Denied alarm UUID */
} event_producer_config_t;

/**
 * @brief Initialize the event producer
 *
 * @param config    Producer configuration
 * @return          0 on success, -1 on error
 */
int event_producer_init(const event_producer_config_t* config);

/**
 * @brief Shutdown the event producer
 */
void event_producer_shutdown(void);

/**
 * @brief Create an access event from a decision
 *
 * @param card_info     Card information (can be NULL for unknown cards)
 * @param decision      Access decision
 * @param facility_code Wiegand facility code
 * @param card_number   Wiegand card number
 * @param event         Output: populated event structure
 * @return              0 on success, -1 on error
 */
int event_producer_create_access_event(
    const card_info_t* card_info,
    const access_decision_t* decision,
    uint32_t facility_code,
    uint32_t card_number,
    hal_event_t* event);

/**
 * @brief Create a generic event
 *
 * @param event_type    Event type
 * @param alarm_name    Alarm name
 * @param alarm_uid     Alarm UUID
 * @param event         Output: populated event structure
 * @return              0 on success, -1 on error
 */
int event_producer_create_event(
    event_type_t event_type,
    const char* alarm_name,
    const char* alarm_uid,
    hal_event_t* event);

#ifdef __cplusplus
}
#endif

#endif /* POC_EVENT_PRODUCER_H */
