/**
 * @file uuid_utils.h
 * @brief UUID generation and handling utilities
 *
 * Provides UUID v4 generation and validation functions.
 * Works on macOS, Linux, and embedded systems.
 *
 * @author FAM-HAL-v1.0-001
 * @date February 10, 2026
 */

#ifndef POC_UUID_UTILS_H
#define POC_UUID_UTILS_H

#include <stdbool.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

/* UUID string length including null terminator */
#define UUID_STR_LEN 37

/* UUID binary length (16 bytes) */
#define UUID_BIN_LEN 16

/**
 * @brief Generate a new UUID v4 (random)
 *
 * Generates a random UUID following the UUID v4 specification.
 * The result is written as a 36-character string plus null terminator.
 *
 * @param uuid_out  Buffer to receive UUID string (must be at least 37 bytes)
 * @return          0 on success, -1 on error
 */
int uuid_generate(char* uuid_out);

/**
 * @brief Generate a new UUID v4 and copy to fixed-size buffer
 *
 * Same as uuid_generate but for use with fixed-size char arrays.
 *
 * @param uuid_out  Buffer to receive UUID string
 * @param buf_size  Size of the buffer
 * @return          0 on success, -1 on error
 */
int uuid_generate_safe(char* uuid_out, size_t buf_size);

/**
 * @brief Validate a UUID string format
 *
 * Checks if the string is a valid UUID format (xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx).
 *
 * @param uuid      UUID string to validate
 * @return          true if valid, false otherwise
 */
bool uuid_is_valid(const char* uuid);

/**
 * @brief Check if a UUID string is empty/null
 *
 * @param uuid      UUID string to check
 * @return          true if empty or null, false if contains valid data
 */
bool uuid_is_empty(const char* uuid);

/**
 * @brief Compare two UUIDs
 *
 * @param uuid1     First UUID string
 * @param uuid2     Second UUID string
 * @return          0 if equal, non-zero if different
 */
int uuid_compare(const char* uuid1, const char* uuid2);

/**
 * @brief Copy a UUID string safely
 *
 * @param dest      Destination buffer
 * @param src       Source UUID string
 * @param dest_size Size of destination buffer
 * @return          0 on success, -1 on error
 */
int uuid_copy(char* dest, const char* src, size_t dest_size);

/**
 * @brief Create a null/empty UUID string
 *
 * Sets the buffer to "00000000-0000-0000-0000-000000000000"
 *
 * @param uuid_out  Buffer to receive null UUID
 * @param buf_size  Size of the buffer
 * @return          0 on success, -1 on error
 */
int uuid_set_null(char* uuid_out, size_t buf_size);

/**
 * @brief Initialize the UUID generator
 *
 * Seeds the random number generator. Should be called once at startup.
 * If not called, uuid_generate will auto-initialize on first use.
 */
void uuid_init(void);

#ifdef __cplusplus
}
#endif

#endif /* POC_UUID_UTILS_H */
