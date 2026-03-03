/**
 * @file access_logic.c
 * @brief Access decision logic implementation
 *
 * @author FAM-HAL-v1.0-001
 * @date February 10, 2026
 */

#include "access_logic.h"
#include "logger.h"
#include <stdio.h>
#include <string.h>
#include <sys/time.h>

/**
 * Get current time in microseconds
 */
static int64_t get_time_us(void) {
    struct timeval tv;
    gettimeofday(&tv, NULL);
    return (int64_t)tv.tv_sec * 1000000 + tv.tv_usec;
}

bool access_check_validity(const card_info_t* card_info, time_t timestamp) {
    if (!card_info) {
        return false;
    }

    /* Check valid_from */
    if (card_info->valid_from > 0 && timestamp < card_info->valid_from) {
        return false;
    }

    /* Check valid_until */
    if (card_info->valid_until > 0 && timestamp > card_info->valid_until) {
        return false;
    }

    return true;
}

access_result_t access_check(const card_info_t* card_info, time_t timestamp,
                             access_decision_t* decision) {
    int64_t start_time = get_time_us();

    if (!decision) {
        return ACCESS_RESULT_UNKNOWN;
    }

    memset(decision, 0, sizeof(access_decision_t));

    if (!card_info) {
        decision->result = ACCESS_RESULT_DENIED_NO_CARD;
        decision->card_found = false;
        decision->decision_time_us = get_time_us() - start_time;
        return decision->result;
    }

    decision->card_found = true;

    /* Check if card is enabled */
    if (!card_info->enabled) {
        decision->result = ACCESS_RESULT_DENIED_DISABLED;
        decision->card_enabled = false;
        decision->decision_time_us = get_time_us() - start_time;
        LOG_DEBUG("Access denied: card %u is disabled", card_info->card_number);
        return decision->result;
    }
    decision->card_enabled = true;

    /* Check validity period */
    if (!access_check_validity(card_info, timestamp)) {
        decision->result = ACCESS_RESULT_DENIED_EXPIRED;
        decision->validity_ok = false;
        decision->decision_time_us = get_time_us() - start_time;
        LOG_DEBUG("Access denied: card %u is expired", card_info->card_number);
        return decision->result;
    }
    decision->validity_ok = true;

    /* TODO: Timezone checks would go here */
    decision->timezone_valid = true;

    /* TODO: Anti-passback checks would go here */
    decision->apb_valid = true;

    /* All checks passed - grant access */
    decision->result = ACCESS_RESULT_GRANTED;
    decision->decision_time_us = get_time_us() - start_time;

    LOG_DEBUG("Access granted: card %u (%s %s) in %ldus",
              card_info->card_number,
              card_info->first_name,
              card_info->last_name,
              (long)decision->decision_time_us);

    return decision->result;
}

access_result_t access_check_unknown(uint32_t card_number,
                                     access_decision_t* decision) {
    int64_t start_time = get_time_us();

    if (!decision) {
        return ACCESS_RESULT_DENIED_NO_CARD;
    }

    memset(decision, 0, sizeof(access_decision_t));
    decision->result = ACCESS_RESULT_DENIED_NO_CARD;
    decision->card_found = false;
    decision->decision_time_us = get_time_us() - start_time;

    LOG_DEBUG("Access denied: card %u not found", card_number);

    return decision->result;
}

int access_decision_to_string(const access_decision_t* decision,
                              char* buf, size_t buf_size) {
    if (!decision || !buf || buf_size == 0) {
        return 0;
    }

    const char* result_str = access_result_to_string(decision->result);

    return snprintf(buf, buf_size,
                    "Result: %s | Card Found: %s | Enabled: %s | "
                    "Validity: %s | Timezone: %s | APB: %s | Time: %ldus",
                    result_str,
                    decision->card_found ? "Y" : "N",
                    decision->card_enabled ? "Y" : "N",
                    decision->validity_ok ? "Y" : "N",
                    decision->timezone_valid ? "Y" : "N",
                    decision->apb_valid ? "Y" : "N",
                    (long)decision->decision_time_us);
}
