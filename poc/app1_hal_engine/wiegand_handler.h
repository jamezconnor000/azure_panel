/**
 * @file wiegand_handler.h
 * @brief Wiegand protocol handler
 *
 * Parses 26-bit Wiegand data format.
 *
 * @author FAM-HAL-v1.0-001
 * @date February 10, 2026
 */

#ifndef POC_WIEGAND_HANDLER_H
#define POC_WIEGAND_HANDLER_H

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief Wiegand card data structure
 */
typedef struct {
    uint32_t facility_code;     /* 8-bit facility code (0-255) */
    uint32_t card_number;       /* 16-bit card number (0-65535) */
    uint32_t raw_data;          /* Raw 26-bit data */
    bool valid;                 /* Parity check passed */
} wiegand_data_t;

/**
 * @brief Parse 26-bit Wiegand data
 *
 * Standard 26-bit Wiegand format:
 * - Bit 0: Even parity (bits 1-12)
 * - Bits 1-8: Facility code (8 bits)
 * - Bits 9-24: Card number (16 bits)
 * - Bit 25: Odd parity (bits 13-24)
 *
 * @param raw_data      26-bit raw Wiegand data
 * @param result        Output: parsed data
 * @return              0 on success, -1 on parity error
 */
int wiegand_parse_26bit(uint32_t raw_data, wiegand_data_t* result);

/**
 * @brief Create 26-bit Wiegand data from FC and CN
 *
 * @param facility_code     8-bit facility code
 * @param card_number       16-bit card number
 * @return                  26-bit Wiegand data with parity
 */
uint32_t wiegand_create_26bit(uint8_t facility_code, uint16_t card_number);

/**
 * @brief Verify Wiegand parity bits
 *
 * @param raw_data      26-bit raw Wiegand data
 * @return              true if parity is valid
 */
bool wiegand_verify_parity(uint32_t raw_data);

/**
 * @brief Format Wiegand data as string
 *
 * @param data          Parsed Wiegand data
 * @param buf           Output buffer
 * @param buf_size      Buffer size
 * @return              Number of characters written
 */
int wiegand_format_string(const wiegand_data_t* data, char* buf, size_t buf_size);

#ifdef __cplusplus
}
#endif

#endif /* POC_WIEGAND_HANDLER_H */
