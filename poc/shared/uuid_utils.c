/**
 * @file uuid_utils.c
 * @brief UUID generation and handling implementation
 *
 * @author FAM-HAL-v1.0-001
 * @date February 10, 2026
 */

#include "uuid_utils.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <time.h>
#include <stdbool.h>
#include <unistd.h>

#ifdef __APPLE__
#include <CommonCrypto/CommonRandom.h>
#elif defined(__linux__)
#include <fcntl.h>
#endif

/* Static initialization flag */
static bool s_uuid_initialized = false;

/**
 * @brief Get random bytes from system
 */
static int get_random_bytes(unsigned char* buf, size_t len) {
#ifdef __APPLE__
    /* Use Apple's secure random on macOS */
    if (CCRandomGenerateBytes(buf, len) == kCCSuccess) {
        return 0;
    }
    return -1;

#elif defined(__linux__)
    /* Use /dev/urandom on Linux */
    int fd = open("/dev/urandom", O_RDONLY);
    if (fd < 0) {
        return -1;
    }

    ssize_t bytes_read = read(fd, buf, len);
    close(fd);

    if (bytes_read != (ssize_t)len) {
        return -1;
    }
    return 0;

#else
    /* Fallback: use rand() - less secure but works everywhere */
    if (!s_uuid_initialized) {
        uuid_init();
    }
    for (size_t i = 0; i < len; i++) {
        buf[i] = (unsigned char)(rand() & 0xFF);
    }
    return 0;
#endif
}

void uuid_init(void) {
    if (!s_uuid_initialized) {
        /* Seed with time and process info */
        unsigned int seed = (unsigned int)time(NULL);
#ifdef __APPLE__
        seed ^= (unsigned int)getpid();
#endif
        srand(seed);
        s_uuid_initialized = true;
    }
}

int uuid_generate(char* uuid_out) {
    if (!uuid_out) {
        return -1;
    }

    unsigned char bytes[16];

    /* Get random bytes */
    if (get_random_bytes(bytes, sizeof(bytes)) != 0) {
        /* Fallback to rand() */
        uuid_init();
        for (int i = 0; i < 16; i++) {
            bytes[i] = (unsigned char)(rand() & 0xFF);
        }
    }

    /* Set UUID version to 4 (random) */
    bytes[6] = (bytes[6] & 0x0F) | 0x40;

    /* Set variant to RFC 4122 */
    bytes[8] = (bytes[8] & 0x3F) | 0x80;

    /* Format as string: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx */
    snprintf(uuid_out, UUID_STR_LEN,
             "%02x%02x%02x%02x-%02x%02x-%02x%02x-%02x%02x-%02x%02x%02x%02x%02x%02x",
             bytes[0], bytes[1], bytes[2], bytes[3],
             bytes[4], bytes[5],
             bytes[6], bytes[7],
             bytes[8], bytes[9],
             bytes[10], bytes[11], bytes[12], bytes[13], bytes[14], bytes[15]);

    return 0;
}

int uuid_generate_safe(char* uuid_out, size_t buf_size) {
    if (!uuid_out || buf_size < UUID_STR_LEN) {
        return -1;
    }
    return uuid_generate(uuid_out);
}

bool uuid_is_valid(const char* uuid) {
    if (!uuid) {
        return false;
    }

    size_t len = strlen(uuid);
    if (len != 36) {
        return false;
    }

    /* Check format: 8-4-4-4-12 with hyphens */
    const int hyphen_positions[] = {8, 13, 18, 23};
    for (int i = 0; i < 4; i++) {
        if (uuid[hyphen_positions[i]] != '-') {
            return false;
        }
    }

    /* Check that all other characters are hex digits */
    for (int i = 0; i < 36; i++) {
        if (i == 8 || i == 13 || i == 18 || i == 23) {
            continue; /* Skip hyphens */
        }
        if (!isxdigit((unsigned char)uuid[i])) {
            return false;
        }
    }

    return true;
}

bool uuid_is_empty(const char* uuid) {
    if (!uuid || uuid[0] == '\0') {
        return true;
    }

    /* Check for null UUID */
    static const char* null_uuid = "00000000-0000-0000-0000-000000000000";
    return (strcmp(uuid, null_uuid) == 0);
}

int uuid_compare(const char* uuid1, const char* uuid2) {
    if (!uuid1 && !uuid2) {
        return 0;
    }
    if (!uuid1) {
        return -1;
    }
    if (!uuid2) {
        return 1;
    }
    return strcasecmp(uuid1, uuid2);
}

int uuid_copy(char* dest, const char* src, size_t dest_size) {
    if (!dest || dest_size == 0) {
        return -1;
    }

    if (!src) {
        dest[0] = '\0';
        return 0;
    }

    size_t src_len = strlen(src);
    if (src_len >= dest_size) {
        /* Source too long, truncate */
        memcpy(dest, src, dest_size - 1);
        dest[dest_size - 1] = '\0';
        return -1;
    }

    memcpy(dest, src, src_len + 1);
    return 0;
}

int uuid_set_null(char* uuid_out, size_t buf_size) {
    if (!uuid_out || buf_size < UUID_STR_LEN) {
        return -1;
    }

    strncpy(uuid_out, "00000000-0000-0000-0000-000000000000", buf_size - 1);
    uuid_out[buf_size - 1] = '\0';
    return 0;
}
