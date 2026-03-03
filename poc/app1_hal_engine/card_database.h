/**
 * @file card_database.h
 * @brief Card database interface
 *
 * SQLite-based card database for storing and looking up cardholders.
 *
 * @author FAM-HAL-v1.0-001
 * @date February 10, 2026
 */

#ifndef POC_CARD_DATABASE_H
#define POC_CARD_DATABASE_H

#include "event_types.h"
#include <stdbool.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief Initialize the card database
 *
 * Opens or creates the SQLite database file.
 *
 * @param db_path       Path to database file
 * @return              0 on success, -1 on error
 */
int card_db_init(const char* db_path);

/**
 * @brief Close the card database
 */
void card_db_close(void);

/**
 * @brief Check if database is initialized
 *
 * @return              true if database is open
 */
bool card_db_is_open(void);

/**
 * @brief Look up a card by card number
 *
 * @param card_number   Card number to search for
 * @param card_info     Output: card information if found
 * @return              0 if found, 1 if not found, -1 on error
 */
int card_db_lookup(uint32_t card_number, card_info_t* card_info);

/**
 * @brief Look up a card by facility code and card number
 *
 * @param facility_code Facility code
 * @param card_number   Card number
 * @param card_info     Output: card information if found
 * @return              0 if found, 1 if not found, -1 on error
 */
int card_db_lookup_fc_cn(uint32_t facility_code, uint32_t card_number,
                         card_info_t* card_info);

/**
 * @brief Add a card to the database
 *
 * @param card_info     Card information to add
 * @return              0 on success, -1 on error
 */
int card_db_add(const card_info_t* card_info);

/**
 * @brief Update an existing card
 *
 * @param card_info     Card information to update (matched by card_number)
 * @return              0 on success, -1 on error
 */
int card_db_update(const card_info_t* card_info);

/**
 * @brief Delete a card from the database
 *
 * @param card_number   Card number to delete
 * @return              0 on success, -1 on error
 */
int card_db_delete(uint32_t card_number);

/**
 * @brief Get the total number of cards in the database
 *
 * @return              Card count, or -1 on error
 */
int card_db_count(void);

/**
 * @brief Seed the database with test cards
 *
 * Adds a set of test cards for development/testing.
 *
 * @return              Number of cards added, or -1 on error
 */
int card_db_seed_test_data(void);

#ifdef __cplusplus
}
#endif

#endif /* POC_CARD_DATABASE_H */
