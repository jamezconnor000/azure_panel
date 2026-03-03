/**
 * @file wiegand_handler.c
 * @brief Wiegand protocol handler implementation
 *
 * @author FAM-HAL-v1.0-001
 * @date February 10, 2026
 */

#include "wiegand_handler.h"
#include <stdio.h>
#include <string.h>

/**
 * Count set bits in a value
 */
static int popcount(uint32_t x) {
    int count = 0;
    while (x) {
        count += x & 1;
        x >>= 1;
    }
    return count;
}

bool wiegand_verify_parity(uint32_t raw_data) {
    /*
     * 26-bit Wiegand format:
     * Bit 25 (MSB): Even parity for bits 24-13 (upper 12 data bits)
     * Bits 24-17: Facility code (8 bits)
     * Bits 16-1: Card number (16 bits)
     * Bit 0 (LSB): Odd parity for bits 12-1 (lower 12 data bits)
     */

    /* Extract parity bits */
    int even_parity_bit = (raw_data >> 25) & 1;  /* Bit 25 */
    int odd_parity_bit = raw_data & 1;            /* Bit 0 */

    /* Upper 12 data bits (bits 24-13) */
    uint32_t upper_12 = (raw_data >> 13) & 0xFFF;

    /* Lower 12 data bits (bits 12-1) */
    uint32_t lower_12 = (raw_data >> 1) & 0xFFF;

    /* Even parity: total set bits should be even */
    int upper_ones = popcount(upper_12);
    bool even_ok = ((upper_ones + even_parity_bit) % 2) == 0;

    /* Odd parity: total set bits should be odd */
    int lower_ones = popcount(lower_12);
    bool odd_ok = ((lower_ones + odd_parity_bit) % 2) == 1;

    return even_ok && odd_ok;
}

int wiegand_parse_26bit(uint32_t raw_data, wiegand_data_t* result) {
    if (!result) {
        return -1;
    }

    memset(result, 0, sizeof(wiegand_data_t));
    result->raw_data = raw_data;

    /* Verify parity */
    result->valid = wiegand_verify_parity(raw_data);

    /* Extract facility code (bits 24-17, 8 bits) */
    result->facility_code = (raw_data >> 17) & 0xFF;

    /* Extract card number (bits 16-1, 16 bits) */
    result->card_number = (raw_data >> 1) & 0xFFFF;

    return result->valid ? 0 : -1;
}

uint32_t wiegand_create_26bit(uint8_t facility_code, uint16_t card_number) {
    uint32_t raw_data = 0;

    /* Place facility code in bits 24-17 */
    raw_data |= ((uint32_t)facility_code << 17);

    /* Place card number in bits 16-1 */
    raw_data |= ((uint32_t)card_number << 1);

    /* Calculate upper 12 bits parity (even) - bits 24-13 */
    uint32_t upper_12 = (raw_data >> 13) & 0xFFF;
    int upper_ones = popcount(upper_12);
    if (upper_ones % 2 != 0) {
        raw_data |= (1 << 25);  /* Set even parity bit */
    }

    /* Calculate lower 12 bits parity (odd) - bits 12-1 */
    uint32_t lower_12 = (raw_data >> 1) & 0xFFF;
    int lower_ones = popcount(lower_12);
    if (lower_ones % 2 == 0) {
        raw_data |= 1;  /* Set odd parity bit */
    }

    return raw_data;
}

int wiegand_format_string(const wiegand_data_t* data, char* buf, size_t buf_size) {
    if (!data || !buf || buf_size == 0) {
        return 0;
    }

    return snprintf(buf, buf_size, "FC=%u CN=%u (0x%06X) %s",
                    data->facility_code,
                    data->card_number,
                    data->raw_data,
                    data->valid ? "VALID" : "PARITY_ERROR");
}
