#ifndef CARD_DATABASE_H
#define CARD_DATABASE_H

#include <sqlite3.h>
#include <stdint.h>
#include <stdbool.h>
#include "../../include/hal_types.h"

/**
 * Card Database Module
 *
 * Manages card records with permission associations.
 * Links physical cards to permission IDs for access control.
 */

// Card record structure
typedef struct {
    uint32_t card_number;
    uint32_t permission_id;
    char card_holder_name[128];
    uint64_t activation_date;
    uint64_t expiration_date;
    bool is_active;
    uint32_t pin;  // Optional PIN (0 if not set)
} CardRecord_t;

// =============================================================================
// Database Initialization
// =============================================================================

/**
 * Initialize card database
 *
 * @param db_path Path to SQLite database file
 * @return ErrorCode_OK on success
 */
ErrorCode_t CardDatabase_Initialize(const char* db_path);

/**
 * Shutdown card database
 */
void CardDatabase_Shutdown(void);

/**
 * Get database connection
 */
sqlite3* CardDatabase_GetConnection(void);

// =============================================================================
// Card CRUD Operations
// =============================================================================

/**
 * Add a new card to database
 *
 * @param card Card record to add
 * @return ErrorCode_OK on success
 */
ErrorCode_t CardDatabase_AddCard(const CardRecord_t* card);

/**
 * Get card record by card number
 *
 * @param card_number Card number to lookup
 * @param out_card Output card record
 * @return ErrorCode_OK if found, ErrorCode_NotFound otherwise
 */
ErrorCode_t CardDatabase_GetCard(uint32_t card_number, CardRecord_t* out_card);

/**
 * Update existing card record
 *
 * @param card Card record with updated data
 * @return ErrorCode_OK on success
 */
ErrorCode_t CardDatabase_UpdateCard(const CardRecord_t* card);

/**
 * Delete card from database
 *
 * @param card_number Card number to delete
 * @return ErrorCode_OK on success
 */
ErrorCode_t CardDatabase_DeleteCard(uint32_t card_number);

/**
 * Get all cards for a permission
 *
 * @param permission_id Permission ID
 * @param out_cards Array to store card records
 * @param max_count Maximum number of cards to return
 * @return Number of cards found
 */
int CardDatabase_GetCardsForPermission(uint32_t permission_id, CardRecord_t* out_cards, int max_count);

/**
 * Get permission ID for a card number (fast lookup)
 *
 * @param card_number Card number
 * @return Permission ID or 0 if not found
 */
uint32_t CardDatabase_GetPermissionForCard(uint32_t card_number);

/**
 * Check if card is active (not expired, is_active flag set)
 *
 * @param card_number Card number
 * @return true if active, false otherwise
 */
bool CardDatabase_IsCardActive(uint32_t card_number);

/**
 * Validate card PIN
 *
 * @param card_number Card number
 * @param pin PIN to validate
 * @return true if PIN matches, false otherwise
 */
bool CardDatabase_ValidatePIN(uint32_t card_number, uint32_t pin);

/**
 * Get total number of cards in database
 */
int CardDatabase_GetCardCount(void);

/**
 * Load all cards from database
 *
 * @param out_cards Array to store card records
 * @param max_count Maximum number of cards to load
 * @return Number of cards loaded
 */
int CardDatabase_LoadAllCards(CardRecord_t* out_cards, int max_count);

#endif // CARD_DATABASE_H
