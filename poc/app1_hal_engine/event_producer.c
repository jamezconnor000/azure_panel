/**
 * @file event_producer.c
 * @brief Event production implementation
 *
 * @author FAM-HAL-v1.0-001
 * @date February 10, 2026
 */

#include "event_producer.h"
#include "uuid_utils.h"
#include "logger.h"
#include <string.h>
#include <time.h>
#include <stdio.h>

/* ============================================================================
 * Static State
 * ========================================================================== */

static event_producer_config_t s_config;
static bool s_initialized = false;

/* ============================================================================
 * Public Functions
 * ========================================================================== */

int event_producer_init(const event_producer_config_t* config) {
    if (!config) {
        LOG_ERROR("Event producer config is NULL");
        return -1;
    }

    memcpy(&s_config, config, sizeof(event_producer_config_t));
    s_initialized = true;

    LOG_INFO("Event producer initialized: device=%s port=%d",
             s_config.device_name, s_config.reader_port);

    return 0;
}

void event_producer_shutdown(void) {
    s_initialized = false;
    LOG_INFO("Event producer shutdown");
}

int event_producer_create_access_event(
    const card_info_t* card_info,
    const access_decision_t* decision,
    uint32_t facility_code,
    uint32_t card_number,
    hal_event_t* event)
{
    if (!decision || !event) {
        return -1;
    }

    if (!s_initialized) {
        LOG_ERROR("Event producer not initialized");
        return -1;
    }

    /* Initialize event */
    event_init(event);

    /* Generate event UUID */
    uuid_generate(event->event_uid);

    /* Set event type based on decision */
    if (decision->result == ACCESS_RESULT_GRANTED) {
        event->event_type = EVENT_TYPE_ACCESS_GRANTED;
        strncpy(event->alarm_name, "Access Granted", ALARM_NAME_MAX_LEN - 1);
        strncpy(event->alarm_uid, s_config.alarm_uid_granted, UUID_STRING_LEN - 1);
    } else {
        event->event_type = EVENT_TYPE_ACCESS_DENIED;
        strncpy(event->alarm_name, "Access Denied", ALARM_NAME_MAX_LEN - 1);
        strncpy(event->alarm_uid, s_config.alarm_uid_denied, UUID_STRING_LEN - 1);
    }

    /* Set device info */
    strncpy(event->device_uid, s_config.device_uid, UUID_STRING_LEN - 1);
    strncpy(event->device_name, s_config.device_name, DEVICE_NAME_MAX_LEN - 1);
    strncpy(event->device_type, "Reader", DEVICE_TYPE_MAX_LEN - 1);
    event->reader_port = s_config.reader_port;

    /* Set timestamps */
    event->occurred_timestamp = time(NULL);
    event->published_timestamp = event->occurred_timestamp;

    /* Set access result */
    event->access_result = decision->result;

    /* Set Wiegand data */
    event->facility_code = facility_code;
    event->card_number = card_number;
    snprintf(event->access_item_key, ACCESS_ITEM_KEY_MAX_LEN - 1, "%u", card_number);

    /* Set cardholder info if available */
    if (card_info && card_info->person_uid[0] != '\0') {
        strncpy(event->person_uid, card_info->person_uid, UUID_STRING_LEN - 1);
        event->has_person = true;
    } else {
        event->has_person = false;
    }

    LOG_DEBUG("Created event: %s uid=%s card=%u",
              event->alarm_name, event->event_uid, card_number);

    return 0;
}

int event_producer_create_event(
    event_type_t event_type,
    const char* alarm_name,
    const char* alarm_uid,
    hal_event_t* event)
{
    if (!event) {
        return -1;
    }

    if (!s_initialized) {
        LOG_ERROR("Event producer not initialized");
        return -1;
    }

    /* Initialize event */
    event_init(event);

    /* Generate event UUID */
    uuid_generate(event->event_uid);

    /* Set event type and alarm */
    event->event_type = event_type;
    if (alarm_name) {
        strncpy(event->alarm_name, alarm_name, ALARM_NAME_MAX_LEN - 1);
    }
    if (alarm_uid) {
        strncpy(event->alarm_uid, alarm_uid, UUID_STRING_LEN - 1);
    }

    /* Set device info */
    strncpy(event->device_uid, s_config.device_uid, UUID_STRING_LEN - 1);
    strncpy(event->device_name, s_config.device_name, DEVICE_NAME_MAX_LEN - 1);
    strncpy(event->device_type, "Reader", DEVICE_TYPE_MAX_LEN - 1);
    event->reader_port = s_config.reader_port;

    /* Set timestamps */
    event->occurred_timestamp = time(NULL);
    event->published_timestamp = event->occurred_timestamp;

    LOG_DEBUG("Created event: %s uid=%s", alarm_name, event->event_uid);

    return 0;
}
