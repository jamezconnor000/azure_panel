/**
 * @file access_logic.h
 * @brief Access decision logic
 *
 * Determines whether access should be granted or denied.
 *
 * @author FAM-HAL-v1.0-001
 * @date February 10, 2026
 */

#ifndef POC_ACCESS_LOGIC_H
#define POC_ACCESS_LOGIC_H

#include "event_types.h"
#include <stdbool.h>
#include <time.h>

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief Access decision result with details
 */
typedef struct {
    access_result_t result;         /* Access decision */
    bool card_found;                /* Card was in database */
    bool card_enabled;              /* Card is enabled */
    bool timezone_valid;            /* Within valid timezone */
    bool apb_valid;                 /* Anti-passback check passed */
    bool validity_ok;               /* Within valid date range */
    int64_t decision_time_us;       /* Decision latency in microseconds */
} access_decision_t;

/**
 * @brief Check access for a card
 *
 * @param card_info     Card information from database
 * @param timestamp     Current timestamp
 * @param decision      Output: access decision details
 * @return              The access result
 */
access_result_t access_check(const card_info_t* card_info, time_t timestamp,
                             access_decision_t* decision);

/**
 * @brief Check access for an unknown card
 *
 * Called when the card is not found in the database.
 *
 * @param card_number   Card number
 * @param decision      Output: access decision details
 * @return              The access result (always DENIED_NO_CARD)
 */
access_result_t access_check_unknown(uint32_t card_number,
                                     access_decision_t* decision);

/**
 * @brief Check if a card is within its validity period
 *
 * @param card_info     Card information
 * @param timestamp     Current timestamp
 * @return              true if valid
 */
bool access_check_validity(const card_info_t* card_info, time_t timestamp);

/**
 * @brief Get human-readable access decision description
 *
 * @param decision      Access decision
 * @param buf           Output buffer
 * @param buf_size      Buffer size
 * @return              Number of characters written
 */
int access_decision_to_string(const access_decision_t* decision,
                              char* buf, size_t buf_size);

#ifdef __cplusplus
}
#endif

#endif /* POC_ACCESS_LOGIC_H */
