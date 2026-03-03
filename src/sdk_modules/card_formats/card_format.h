#ifndef CARD_FORMAT_H
#define CARD_FORMAT_H

#include "../../../include/hal_types.h"
#include <stdint.h>
#include <stdbool.h>

/**
 * Card Format Module
 *
 * Manages Wiegand and other card format definitions.
 * Defines how card data is interpreted from readers.
 */

// Card Format Types
typedef enum {
    CardFormatType_Wiegand = 0,
    CardFormatType_SmartCard = 1,
    CardFormatType_MagStripe = 2
} CardFormatType_t;

// Wiegand Format structure
typedef struct {
    uint8_t id;                     // Format ID (1-255)
    CardFormatType_t type;          // Format type
    char name[64];                  // Format name

    // Wiegand-specific fields
    uint8_t total_bits;             // Total bits in format (26, 35, 37, etc.)
    uint8_t facility_start_bit;     // Facility code start bit
    uint8_t facility_bit_length;    // Facility code bit length
    uint8_t card_start_bit;         // Card number start bit
    uint8_t card_bit_length;        // Card number bit length
    uint8_t parity_type;            // Parity type (0=none, 1=even/odd)

} CardFormat_t;

// Card Format List structure
typedef struct {
    uint8_t id;                     // List ID
    uint8_t format_ids[16];         // Up to 16 format IDs
    uint8_t count;                  // Number of formats in list

} CardFormatList_t;

// =============================================================================
// Card Format Functions
// =============================================================================

/**
 * Create a new card format
 */
CardFormat_t* CardFormat_Create(uint8_t id);

/**
 * Destroy card format
 */
void CardFormat_Destroy(CardFormat_t* format);

/**
 * Set Wiegand format parameters
 */
ErrorCode_t CardFormat_SetWiegand(CardFormat_t* format,
                                   uint8_t total_bits,
                                   uint8_t facility_start, uint8_t facility_length,
                                   uint8_t card_start, uint8_t card_length);

/**
 * Create a card format list
 */
CardFormatList_t* CardFormatList_Create(uint8_t id);

/**
 * Destroy card format list
 */
void CardFormatList_Destroy(CardFormatList_t* list);

/**
 * Add format to list
 */
ErrorCode_t CardFormatList_AddFormat(CardFormatList_t* list, uint8_t format_id);

#endif // CARD_FORMAT_H
