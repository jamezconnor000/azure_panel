/**
 * @file test_ipc.c
 * @brief IPC Communication Tests
 *
 * Tests the IPC message framing and communication.
 *
 * @author FAM-HAL-v1.0-001
 * @date February 10, 2026
 */

#include "event_types.h"
#include "json_serializer.h"
#include "ipc_common.h"
#include "uuid_utils.h"

#include <arpa/inet.h>
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <unistd.h>

#define TEST_PASS(name) printf("  ✓ %s\n", name)
#define TEST_FAIL(name, msg) do { printf("  ✗ %s: %s\n", name, msg); return 1; } while(0)

#define TEST_SOCKET_PATH "/tmp/test_ipc.sock"

static int test_message_length_encoding(void) {
    /* Test length header encoding */
    const char* test_msg = "Hello, World!";
    size_t msg_len;

    char* ipc_msg = ipc_create_message(test_msg, &msg_len);
    if (!ipc_msg) {
        TEST_FAIL("message_length_encoding", "ipc_create_message failed");
    }

    /* Verify total length */
    if (msg_len != 4 + strlen(test_msg)) {
        free(ipc_msg);
        TEST_FAIL("message_length_encoding", "incorrect total length");
    }

    /* Extract and verify length header */
    uint32_t header;
    memcpy(&header, ipc_msg, 4);
    uint32_t payload_len = ntohl(header);

    if (payload_len != strlen(test_msg)) {
        free(ipc_msg);
        TEST_FAIL("message_length_encoding", "incorrect payload length");
    }

    /* Verify payload */
    if (memcmp(ipc_msg + 4, test_msg, strlen(test_msg)) != 0) {
        free(ipc_msg);
        TEST_FAIL("message_length_encoding", "payload mismatch");
    }

    free(ipc_msg);
    TEST_PASS("message_length_encoding");
    return 0;
}

static int test_message_parsing(void) {
    const char* original = "{\"test\":\"data\",\"number\":42}";
    size_t msg_len;

    /* Create message */
    char* ipc_msg = ipc_create_message(original, &msg_len);
    if (!ipc_msg) {
        TEST_FAIL("message_parsing", "ipc_create_message failed");
    }

    /* Parse message */
    char* parsed = NULL;
    if (ipc_parse_message(ipc_msg, msg_len, &parsed) != 0) {
        free(ipc_msg);
        TEST_FAIL("message_parsing", "ipc_parse_message failed");
    }

    /* Verify */
    if (strcmp(original, parsed) != 0) {
        free(ipc_msg);
        free(parsed);
        TEST_FAIL("message_parsing", "parsed content mismatch");
    }

    free(ipc_msg);
    free(parsed);
    TEST_PASS("message_parsing");
    return 0;
}

static int test_empty_message(void) {
    const char* empty = "";
    size_t msg_len;

    char* ipc_msg = ipc_create_message(empty, &msg_len);
    if (!ipc_msg) {
        TEST_FAIL("empty_message", "ipc_create_message failed");
    }

    if (msg_len != 4) {
        free(ipc_msg);
        TEST_FAIL("empty_message", "incorrect length for empty message");
    }

    char* parsed = NULL;
    if (ipc_parse_message(ipc_msg, msg_len, &parsed) != 0) {
        free(ipc_msg);
        TEST_FAIL("empty_message", "ipc_parse_message failed");
    }

    if (strlen(parsed) != 0) {
        free(ipc_msg);
        free(parsed);
        TEST_FAIL("empty_message", "parsed content not empty");
    }

    free(ipc_msg);
    free(parsed);
    TEST_PASS("empty_message");
    return 0;
}

static int test_large_message(void) {
    /* Create a large message (64KB) */
    size_t large_size = 64 * 1024;
    char* large_msg = malloc(large_size + 1);
    if (!large_msg) {
        TEST_FAIL("large_message", "malloc failed");
    }

    memset(large_msg, 'A', large_size);
    large_msg[large_size] = '\0';

    size_t msg_len;
    char* ipc_msg = ipc_create_message(large_msg, &msg_len);
    if (!ipc_msg) {
        free(large_msg);
        TEST_FAIL("large_message", "ipc_create_message failed");
    }

    char* parsed = NULL;
    if (ipc_parse_message(ipc_msg, msg_len, &parsed) != 0) {
        free(large_msg);
        free(ipc_msg);
        TEST_FAIL("large_message", "ipc_parse_message failed");
    }

    if (strlen(parsed) != large_size) {
        free(large_msg);
        free(ipc_msg);
        free(parsed);
        TEST_FAIL("large_message", "parsed length mismatch");
    }

    free(large_msg);
    free(ipc_msg);
    free(parsed);
    TEST_PASS("large_message");
    return 0;
}

static int test_event_ipc_roundtrip(void) {
    /* Create a full event */
    hal_event_t original;
    memset(&original, 0, sizeof(original));

    uuid_generate(original.event_uid);
    uuid_generate(original.device_uid);
    strcpy(original.device_name, "IPC Test Reader");
    strcpy(original.device_type, "Door Reader");
    uuid_generate(original.alarm_uid);
    strcpy(original.alarm_name, "Access Granted");
    original.occurred_timestamp = 1707580800000;
    original.published_timestamp = 1707580800100;
    original.event_type = EVENT_ACCESS_GRANTED;
    original.access_result = ACCESS_GRANTED;
    original.facility_code = 100;
    original.card_number = 12345;
    original.reader_port = 1;

    /* Serialize to JSON */
    char* json = event_to_json(&original);
    if (!json) {
        TEST_FAIL("event_ipc_roundtrip", "event_to_json failed");
    }

    /* Create IPC message */
    size_t msg_len;
    char* ipc_msg = ipc_create_message(json, &msg_len);
    free(json);

    if (!ipc_msg) {
        TEST_FAIL("event_ipc_roundtrip", "ipc_create_message failed");
    }

    /* Parse IPC message */
    char* parsed_json = NULL;
    if (ipc_parse_message(ipc_msg, msg_len, &parsed_json) != 0) {
        free(ipc_msg);
        TEST_FAIL("event_ipc_roundtrip", "ipc_parse_message failed");
    }
    free(ipc_msg);

    /* Parse event from JSON */
    hal_event_t parsed;
    if (json_to_event(parsed_json, &parsed) != 0) {
        free(parsed_json);
        TEST_FAIL("event_ipc_roundtrip", "json_to_event failed");
    }
    free(parsed_json);

    /* Compare */
    if (strcmp(original.event_uid, parsed.event_uid) != 0) {
        TEST_FAIL("event_ipc_roundtrip", "event_uid mismatch");
    }
    if (strcmp(original.device_name, parsed.device_name) != 0) {
        TEST_FAIL("event_ipc_roundtrip", "device_name mismatch");
    }
    if (original.facility_code != parsed.facility_code) {
        TEST_FAIL("event_ipc_roundtrip", "facility_code mismatch");
    }
    if (original.card_number != parsed.card_number) {
        TEST_FAIL("event_ipc_roundtrip", "card_number mismatch");
    }

    TEST_PASS("event_ipc_roundtrip");
    return 0;
}

/* Server thread for socket test */
static void* server_thread(void* arg) {
    (void)arg;

    /* Create socket */
    int server_fd = socket(AF_UNIX, SOCK_STREAM, 0);
    if (server_fd < 0) {
        return (void*)-1;
    }

    /* Bind */
    struct sockaddr_un addr;
    memset(&addr, 0, sizeof(addr));
    addr.sun_family = AF_UNIX;
    strncpy(addr.sun_path, TEST_SOCKET_PATH, sizeof(addr.sun_path) - 1);

    unlink(TEST_SOCKET_PATH);
    if (bind(server_fd, (struct sockaddr*)&addr, sizeof(addr)) < 0) {
        close(server_fd);
        return (void*)-1;
    }

    if (listen(server_fd, 1) < 0) {
        close(server_fd);
        return (void*)-1;
    }

    /* Accept connection */
    int client_fd = accept(server_fd, NULL, NULL);
    if (client_fd < 0) {
        close(server_fd);
        return (void*)-1;
    }

    /* Receive message */
    uint32_t len_header;
    if (recv(client_fd, &len_header, 4, MSG_WAITALL) != 4) {
        close(client_fd);
        close(server_fd);
        return (void*)-1;
    }

    uint32_t payload_len = ntohl(len_header);
    char* buffer = malloc(payload_len + 1);
    if (recv(client_fd, buffer, payload_len, MSG_WAITALL) != (ssize_t)payload_len) {
        free(buffer);
        close(client_fd);
        close(server_fd);
        return (void*)-1;
    }
    buffer[payload_len] = '\0';

    /* Echo back with "ACK:" prefix */
    char* response = malloc(payload_len + 5);
    snprintf(response, payload_len + 5, "ACK:%s", buffer);
    free(buffer);

    size_t resp_len;
    char* resp_msg = ipc_create_message(response, &resp_len);
    free(response);

    send(client_fd, resp_msg, resp_len, 0);
    free(resp_msg);

    close(client_fd);
    close(server_fd);
    unlink(TEST_SOCKET_PATH);

    return (void*)0;
}

static int test_socket_communication(void) {
    /* Start server thread */
    pthread_t server;
    if (pthread_create(&server, NULL, server_thread, NULL) != 0) {
        TEST_FAIL("socket_communication", "failed to create server thread");
    }

    /* Give server time to start */
    usleep(100000);  /* 100ms */

    /* Connect as client */
    int client_fd = socket(AF_UNIX, SOCK_STREAM, 0);
    if (client_fd < 0) {
        pthread_join(server, NULL);
        TEST_FAIL("socket_communication", "failed to create client socket");
    }

    struct sockaddr_un addr;
    memset(&addr, 0, sizeof(addr));
    addr.sun_family = AF_UNIX;
    strncpy(addr.sun_path, TEST_SOCKET_PATH, sizeof(addr.sun_path) - 1);

    if (connect(client_fd, (struct sockaddr*)&addr, sizeof(addr)) < 0) {
        close(client_fd);
        pthread_join(server, NULL);
        TEST_FAIL("socket_communication", "failed to connect");
    }

    /* Send message */
    const char* test_msg = "Hello Server";
    size_t msg_len;
    char* ipc_msg = ipc_create_message(test_msg, &msg_len);

    if (send(client_fd, ipc_msg, msg_len, 0) != (ssize_t)msg_len) {
        free(ipc_msg);
        close(client_fd);
        pthread_join(server, NULL);
        TEST_FAIL("socket_communication", "failed to send");
    }
    free(ipc_msg);

    /* Receive response */
    uint32_t len_header;
    if (recv(client_fd, &len_header, 4, MSG_WAITALL) != 4) {
        close(client_fd);
        pthread_join(server, NULL);
        TEST_FAIL("socket_communication", "failed to receive length");
    }

    uint32_t payload_len = ntohl(len_header);
    char* buffer = malloc(payload_len + 1);
    if (recv(client_fd, buffer, payload_len, MSG_WAITALL) != (ssize_t)payload_len) {
        free(buffer);
        close(client_fd);
        pthread_join(server, NULL);
        TEST_FAIL("socket_communication", "failed to receive payload");
    }
    buffer[payload_len] = '\0';

    /* Verify response */
    if (strncmp(buffer, "ACK:", 4) != 0) {
        free(buffer);
        close(client_fd);
        pthread_join(server, NULL);
        TEST_FAIL("socket_communication", "response not ACK");
    }

    if (strcmp(buffer + 4, test_msg) != 0) {
        free(buffer);
        close(client_fd);
        pthread_join(server, NULL);
        TEST_FAIL("socket_communication", "response content mismatch");
    }

    free(buffer);
    close(client_fd);

    void* result;
    pthread_join(server, &result);
    if (result != 0) {
        TEST_FAIL("socket_communication", "server thread failed");
    }

    TEST_PASS("socket_communication");
    return 0;
}

int main(void) {
    int failed = 0;

    printf("\n=== IPC Communication Tests ===\n\n");

    failed += test_message_length_encoding();
    failed += test_message_parsing();
    failed += test_empty_message();
    failed += test_large_message();
    failed += test_event_ipc_roundtrip();
    failed += test_socket_communication();

    printf("\n");
    if (failed == 0) {
        printf("All tests passed!\n\n");
        return 0;
    } else {
        printf("%d test(s) failed.\n\n", failed);
        return 1;
    }
}
