/**
 * @file test_json.c
 * @brief JSON Serializer Tests
 *
 * @author FAM-HAL-v1.0-001
 * @date February 10, 2026
 */

#include "event_types.h"
#include "json_serializer.h"
#include "ipc_common.h"
#include "uuid_utils.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>

#define TEST_PASS(name) printf("  ✓ %s\n", name)
#define TEST_FAIL(name, msg) do { printf("  ✗ %s: %s\n", name, msg); return 1; } while(0)

static int test_event_to_json(void) {
    hal_event_t event;
    memset(&event, 0, sizeof(event));

    strcpy(event.event_uid, "11111111-1111-1111-1111-111111111111");
    strcpy(event.device_uid, "22222222-2222-2222-2222-222222222222");
    strcpy(event.device_name, "Test Reader");
    strcpy(event.device_type, "Door Reader");
    strcpy(event.alarm_uid, "33333333-3333-3333-3333-333333333333");
    strcpy(event.alarm_name, "Access Granted");
    event.occurred_timestamp = 1707580800000;
    event.published_timestamp = 1707580800100;
    event.event_type = EVENT_ACCESS_GRANTED;
    event.access_result = ACCESS_GRANTED;
    event.facility_code = 100;
    event.card_number = 12345;
    event.reader_port = 1;

    char* json = event_to_json(&event);
    if (!json) {
        TEST_FAIL("event_to_json", "returned NULL");
    }

    /* Verify JSON contains expected fields */
    if (!strstr(json, "\"event_uid\"")) {
        free(json);
        TEST_FAIL("event_to_json", "missing event_uid");
    }
    if (!strstr(json, "\"device_name\":\"Test Reader\"")) {
        free(json);
        TEST_FAIL("event_to_json", "incorrect device_name");
    }
    if (!strstr(json, "\"facility_code\":100")) {
        free(json);
        TEST_FAIL("event_to_json", "incorrect facility_code");
    }

    free(json);
    TEST_PASS("event_to_json");
    return 0;
}

static int test_json_to_event(void) {
    const char* json =
        "{"
        "\"event_uid\":\"aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa\","
        "\"device_uid\":\"bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb\","
        "\"device_name\":\"Test Device\","
        "\"device_type\":\"Reader\","
        "\"alarm_uid\":\"cccccccc-cccc-cccc-cccc-cccccccccccc\","
        "\"alarm_name\":\"Access Denied\","
        "\"occurred_timestamp\":1707580800000,"
        "\"published_timestamp\":1707580800100,"
        "\"event_type\":1,"
        "\"access_result\":1,"
        "\"facility_code\":200,"
        "\"card_number\":54321,"
        "\"reader_port\":2"
        "}";

    hal_event_t event;
    int result = json_to_event(json, &event);

    if (result != 0) {
        TEST_FAIL("json_to_event", "parsing failed");
    }

    if (strcmp(event.device_name, "Test Device") != 0) {
        TEST_FAIL("json_to_event", "incorrect device_name");
    }
    if (event.facility_code != 200) {
        TEST_FAIL("json_to_event", "incorrect facility_code");
    }
    if (event.card_number != 54321) {
        TEST_FAIL("json_to_event", "incorrect card_number");
    }
    if (event.reader_port != 2) {
        TEST_FAIL("json_to_event", "incorrect reader_port");
    }

    TEST_PASS("json_to_event");
    return 0;
}

static int test_event_roundtrip(void) {
    hal_event_t original;
    memset(&original, 0, sizeof(original));

    uuid_generate(original.event_uid);
    uuid_generate(original.device_uid);
    strcpy(original.device_name, "Roundtrip Test");
    strcpy(original.device_type, "Test Type");
    uuid_generate(original.alarm_uid);
    strcpy(original.alarm_name, "Test Alarm");
    original.occurred_timestamp = 1707580800000;
    original.published_timestamp = 1707580800100;
    original.event_type = EVENT_ACCESS_DENIED;
    original.access_result = ACCESS_DENIED_EXPIRED;
    original.facility_code = 999;
    original.card_number = 88888;
    original.reader_port = 3;

    /* Serialize */
    char* json = event_to_json(&original);
    if (!json) {
        TEST_FAIL("event_roundtrip", "serialization failed");
    }

    /* Deserialize */
    hal_event_t parsed;
    if (json_to_event(json, &parsed) != 0) {
        free(json);
        TEST_FAIL("event_roundtrip", "deserialization failed");
    }
    free(json);

    /* Compare */
    if (strcmp(original.event_uid, parsed.event_uid) != 0) {
        TEST_FAIL("event_roundtrip", "event_uid mismatch");
    }
    if (strcmp(original.device_name, parsed.device_name) != 0) {
        TEST_FAIL("event_roundtrip", "device_name mismatch");
    }
    if (original.facility_code != parsed.facility_code) {
        TEST_FAIL("event_roundtrip", "facility_code mismatch");
    }
    if (original.card_number != parsed.card_number) {
        TEST_FAIL("event_roundtrip", "card_number mismatch");
    }
    if (original.access_result != parsed.access_result) {
        TEST_FAIL("event_roundtrip", "access_result mismatch");
    }

    TEST_PASS("event_roundtrip");
    return 0;
}

static int test_ambient_json_format(void) {
    hal_event_t event;
    memset(&event, 0, sizeof(event));

    strcpy(event.event_uid, "11111111-1111-1111-1111-111111111111");
    strcpy(event.device_uid, "22222222-2222-2222-2222-222222222222");
    strcpy(event.device_name, "Front Door");
    strcpy(event.device_type, "Door Reader");
    strcpy(event.alarm_uid, "33333333-3333-3333-3333-333333333333");
    strcpy(event.alarm_name, "Access Granted");
    event.occurred_timestamp = 1707580800000;
    event.published_timestamp = 1707580800100;
    event.event_type = EVENT_ACCESS_GRANTED;
    event.access_result = ACCESS_GRANTED;
    event.facility_code = 100;
    event.card_number = 12345;

    const char* source_uid = "99999999-9999-9999-9999-999999999999";
    char* json = event_to_ambient_json(&event, source_uid);

    if (!json) {
        TEST_FAIL("ambient_json_format", "returned NULL");
    }

    /* Verify Ambient.ai required fields */
    if (!strstr(json, "\"sourceSystemUid\"")) {
        free(json);
        TEST_FAIL("ambient_json_format", "missing sourceSystemUid");
    }
    if (!strstr(json, "\"occurredTimestamp\"")) {
        free(json);
        TEST_FAIL("ambient_json_format", "missing occurredTimestamp");
    }
    if (!strstr(json, "\"publishedTimestamp\"")) {
        free(json);
        TEST_FAIL("ambient_json_format", "missing publishedTimestamp");
    }
    if (!strstr(json, "\"eventUid\"")) {
        free(json);
        TEST_FAIL("ambient_json_format", "missing eventUid");
    }
    if (!strstr(json, "\"deviceUid\"")) {
        free(json);
        TEST_FAIL("ambient_json_format", "missing deviceUid");
    }
    if (!strstr(json, "\"alarmUid\"")) {
        free(json);
        TEST_FAIL("ambient_json_format", "missing alarmUid");
    }

    free(json);
    TEST_PASS("ambient_json_format");
    return 0;
}

static int test_ipc_message_framing(void) {
    hal_event_t event;
    memset(&event, 0, sizeof(event));

    strcpy(event.event_uid, "11111111-1111-1111-1111-111111111111");
    strcpy(event.device_name, "IPC Test");
    event.facility_code = 123;
    event.card_number = 456;

    /* Create IPC message */
    char* json = event_to_json(&event);
    if (!json) {
        TEST_FAIL("ipc_message_framing", "json serialization failed");
    }

    size_t msg_len;
    char* ipc_msg = ipc_create_message(json, &msg_len);
    free(json);

    if (!ipc_msg) {
        TEST_FAIL("ipc_message_framing", "ipc_create_message failed");
    }

    /* Verify length prefix */
    if (msg_len < 4) {
        free(ipc_msg);
        TEST_FAIL("ipc_message_framing", "message too short");
    }

    /* Parse IPC message */
    char* parsed_json = NULL;
    if (ipc_parse_message(ipc_msg, msg_len, &parsed_json) != 0) {
        free(ipc_msg);
        TEST_FAIL("ipc_message_framing", "ipc_parse_message failed");
    }

    /* Verify roundtrip */
    hal_event_t parsed_event;
    if (json_to_event(parsed_json, &parsed_event) != 0) {
        free(ipc_msg);
        free(parsed_json);
        TEST_FAIL("ipc_message_framing", "final json parse failed");
    }

    if (parsed_event.facility_code != 123) {
        free(ipc_msg);
        free(parsed_json);
        TEST_FAIL("ipc_message_framing", "facility_code mismatch");
    }

    free(ipc_msg);
    free(parsed_json);
    TEST_PASS("ipc_message_framing");
    return 0;
}

int main(void) {
    int failed = 0;

    printf("\n=== JSON Serializer Tests ===\n\n");

    failed += test_event_to_json();
    failed += test_json_to_event();
    failed += test_event_roundtrip();
    failed += test_ambient_json_format();
    failed += test_ipc_message_framing();

    printf("\n");
    if (failed == 0) {
        printf("All tests passed!\n\n");
        return 0;
    } else {
        printf("%d test(s) failed.\n\n", failed);
        return 1;
    }
}
