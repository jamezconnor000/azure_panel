/**
 * @file test_uuid.c
 * @brief UUID Utilities Tests
 *
 * @author FAM-HAL-v1.0-001
 * @date February 10, 2026
 */

#include "uuid_utils.h"
#include "event_types.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

#define TEST_PASS(name) printf("  ✓ %s\n", name)
#define TEST_FAIL(name, msg) do { printf("  ✗ %s: %s\n", name, msg); return 1; } while(0)

static int test_uuid_generate(void) {
    char uuid[UUID_STRING_LEN];

    int result = uuid_generate(uuid);
    if (result != 0) {
        TEST_FAIL("uuid_generate", "returned non-zero");
    }

    /* Check length */
    if (strlen(uuid) != 36) {
        TEST_FAIL("uuid_generate", "incorrect length");
    }

    TEST_PASS("uuid_generate");
    return 0;
}

static int test_uuid_format(void) {
    char uuid[UUID_STRING_LEN];
    uuid_generate(uuid);

    /* UUID format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx */
    /* Positions:   01234567-9012-4567-9012-456789012345 */

    if (uuid[8] != '-' || uuid[13] != '-' ||
        uuid[18] != '-' || uuid[23] != '-') {
        TEST_FAIL("uuid_format", "incorrect hyphen positions");
    }

    /* Check that other positions are hex digits */
    for (int i = 0; i < 36; i++) {
        if (i == 8 || i == 13 || i == 18 || i == 23) continue;
        if (!isxdigit((unsigned char)uuid[i])) {
            TEST_FAIL("uuid_format", "non-hex character found");
        }
    }

    TEST_PASS("uuid_format");
    return 0;
}

static int test_uuid_version4(void) {
    char uuid[UUID_STRING_LEN];
    uuid_generate(uuid);

    /* Version 4 UUID: character at position 14 should be '4' */
    if (uuid[14] != '4') {
        char msg[64];
        snprintf(msg, sizeof(msg), "expected version 4, got '%c'", uuid[14]);
        TEST_FAIL("uuid_version4", msg);
    }

    /* Variant: character at position 19 should be 8, 9, a, or b */
    char variant = tolower((unsigned char)uuid[19]);
    if (variant != '8' && variant != '9' &&
        variant != 'a' && variant != 'b') {
        char msg[64];
        snprintf(msg, sizeof(msg), "invalid variant '%c'", uuid[19]);
        TEST_FAIL("uuid_version4", msg);
    }

    TEST_PASS("uuid_version4");
    return 0;
}

static int test_uuid_uniqueness(void) {
    #define NUM_UUIDS 100
    char uuids[NUM_UUIDS][UUID_STRING_LEN];

    /* Generate multiple UUIDs */
    for (int i = 0; i < NUM_UUIDS; i++) {
        uuid_generate(uuids[i]);
    }

    /* Check for duplicates */
    for (int i = 0; i < NUM_UUIDS; i++) {
        for (int j = i + 1; j < NUM_UUIDS; j++) {
            if (strcmp(uuids[i], uuids[j]) == 0) {
                TEST_FAIL("uuid_uniqueness", "duplicate UUID generated");
            }
        }
    }

    TEST_PASS("uuid_uniqueness");
    return 0;
}

static int test_uuid_is_valid(void) {
    /* Valid UUIDs */
    if (!uuid_is_valid("550e8400-e29b-41d4-a716-446655440000")) {
        TEST_FAIL("uuid_is_valid", "rejected valid lowercase UUID");
    }
    if (!uuid_is_valid("550E8400-E29B-41D4-A716-446655440000")) {
        TEST_FAIL("uuid_is_valid", "rejected valid uppercase UUID");
    }
    if (!uuid_is_valid("00000000-0000-0000-0000-000000000000")) {
        TEST_FAIL("uuid_is_valid", "rejected nil UUID");
    }

    /* Invalid UUIDs */
    if (uuid_is_valid("not-a-uuid")) {
        TEST_FAIL("uuid_is_valid", "accepted non-UUID string");
    }
    if (uuid_is_valid("550e8400-e29b-41d4-a716-44665544000")) {
        TEST_FAIL("uuid_is_valid", "accepted too-short UUID");
    }
    if (uuid_is_valid("550e8400-e29b-41d4-a716-4466554400000")) {
        TEST_FAIL("uuid_is_valid", "accepted too-long UUID");
    }
    if (uuid_is_valid("550e8400-e29b-41d4-a716_446655440000")) {
        TEST_FAIL("uuid_is_valid", "accepted UUID with underscore");
    }
    if (uuid_is_valid("550e8400-e29b-41d4-a716-44665544000g")) {
        TEST_FAIL("uuid_is_valid", "accepted UUID with invalid hex");
    }
    if (uuid_is_valid("")) {
        TEST_FAIL("uuid_is_valid", "accepted empty string");
    }
    if (uuid_is_valid(NULL)) {
        TEST_FAIL("uuid_is_valid", "accepted NULL");
    }

    TEST_PASS("uuid_is_valid");
    return 0;
}

static int test_uuid_compare(void) {
    const char* uuid1 = "11111111-1111-1111-1111-111111111111";
    const char* uuid2 = "22222222-2222-2222-2222-222222222222";
    const char* uuid1_copy = "11111111-1111-1111-1111-111111111111";

    if (uuid_compare(uuid1, uuid1_copy) != 0) {
        TEST_FAIL("uuid_compare", "equal UUIDs not equal");
    }
    if (uuid_compare(uuid1, uuid2) >= 0) {
        TEST_FAIL("uuid_compare", "smaller UUID not less than larger");
    }
    if (uuid_compare(uuid2, uuid1) <= 0) {
        TEST_FAIL("uuid_compare", "larger UUID not greater than smaller");
    }

    /* Case-insensitive comparison */
    if (uuid_compare("AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA",
                     "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa") != 0) {
        TEST_FAIL("uuid_compare", "case sensitivity issue");
    }

    TEST_PASS("uuid_compare");
    return 0;
}

static int test_uuid_copy(void) {
    char src[UUID_STRING_LEN] = "12345678-1234-1234-1234-123456789012";
    char dest[UUID_STRING_LEN] = {0};

    uuid_copy(dest, src, sizeof(dest));

    if (strcmp(dest, src) != 0) {
        TEST_FAIL("uuid_copy", "copy mismatch");
    }

    /* Verify null termination */
    if (dest[36] != '\0') {
        TEST_FAIL("uuid_copy", "not null terminated");
    }

    TEST_PASS("uuid_copy");
    return 0;
}

int main(void) {
    int failed = 0;

    printf("\n=== UUID Utilities Tests ===\n\n");

    failed += test_uuid_generate();
    failed += test_uuid_format();
    failed += test_uuid_version4();
    failed += test_uuid_uniqueness();
    failed += test_uuid_is_valid();
    failed += test_uuid_compare();
    failed += test_uuid_copy();

    printf("\n");
    if (failed == 0) {
        printf("All tests passed!\n\n");
        return 0;
    } else {
        printf("%d test(s) failed.\n\n", failed);
        return 1;
    }
}
