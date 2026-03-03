/**
 * @file ipc_common.h
 * @brief IPC (Inter-Process Communication) common definitions
 *
 * Defines constants and structures for Unix Domain Socket IPC
 * between the HAL Engine and Ambient.ai Forwarder.
 *
 * @author FAM-HAL-v1.0-001
 * @date February 10, 2026
 */

#ifndef POC_IPC_COMMON_H
#define POC_IPC_COMMON_H

#include <stdint.h>
#include <stdbool.h>
#include <sys/socket.h>
#include <sys/un.h>

#ifdef __cplusplus
extern "C" {
#endif

/* ============================================================================
 * Constants
 * ========================================================================== */

/* Default socket path */
#define IPC_DEFAULT_SOCKET_PATH     "/tmp/hal_events.sock"

/* Maximum message size (bytes) */
#define IPC_MAX_MESSAGE_SIZE        8192

/* Maximum number of pending connections */
#define IPC_BACKLOG                 5

/* Connection timeout (seconds) */
#define IPC_CONNECT_TIMEOUT_SEC     5

/* Read/write timeout (milliseconds) */
#define IPC_IO_TIMEOUT_MS           1000

/* Heartbeat interval (seconds) */
#define IPC_HEARTBEAT_INTERVAL_SEC  30

/* Reconnect delay (seconds) */
#define IPC_RECONNECT_DELAY_SEC     2

/* Message framing - each message is prefixed with 4-byte length */
#define IPC_MSG_HEADER_SIZE         4

/* ============================================================================
 * Message Header
 * ========================================================================== */

/**
 * @brief IPC message header for framing
 *
 * Messages are sent with a 4-byte length prefix (network byte order)
 * followed by the JSON payload.
 */
typedef struct {
    uint32_t length;    /* Payload length in bytes (network byte order) */
} ipc_msg_header_t;

/* ============================================================================
 * Connection State
 * ========================================================================== */

/**
 * @brief IPC connection state
 */
typedef enum {
    IPC_STATE_DISCONNECTED = 0,
    IPC_STATE_CONNECTING,
    IPC_STATE_CONNECTED,
    IPC_STATE_ERROR
} ipc_state_t;

/**
 * @brief IPC connection handle
 */
typedef struct {
    int socket_fd;                          /* Socket file descriptor */
    ipc_state_t state;                      /* Connection state */
    char socket_path[108];                  /* Unix socket path */
    bool is_server;                         /* True if server (publisher) */
    uint64_t messages_sent;                 /* Counter: messages sent */
    uint64_t messages_received;             /* Counter: messages received */
    uint64_t bytes_sent;                    /* Counter: bytes sent */
    uint64_t bytes_received;                /* Counter: bytes received */
    int64_t last_activity;                  /* Timestamp of last activity */
} ipc_handle_t;

/* ============================================================================
 * Inline Utility Functions
 * ========================================================================== */

/**
 * @brief Initialize an IPC handle
 */
static inline void ipc_handle_init(ipc_handle_t* handle) {
    if (handle) {
        handle->socket_fd = -1;
        handle->state = IPC_STATE_DISCONNECTED;
        handle->socket_path[0] = '\0';
        handle->is_server = false;
        handle->messages_sent = 0;
        handle->messages_received = 0;
        handle->bytes_sent = 0;
        handle->bytes_received = 0;
        handle->last_activity = 0;
    }
}

/**
 * @brief Check if IPC handle is connected
 */
static inline bool ipc_is_connected(const ipc_handle_t* handle) {
    return handle && handle->state == IPC_STATE_CONNECTED && handle->socket_fd >= 0;
}

/**
 * @brief Get state name as string
 */
static inline const char* ipc_state_to_string(ipc_state_t state) {
    switch (state) {
        case IPC_STATE_DISCONNECTED: return "DISCONNECTED";
        case IPC_STATE_CONNECTING:   return "CONNECTING";
        case IPC_STATE_CONNECTED:    return "CONNECTED";
        case IPC_STATE_ERROR:        return "ERROR";
        default:                     return "UNKNOWN";
    }
}

/* ============================================================================
 * Low-Level Message Framing Functions
 * ========================================================================== */

#include <stdlib.h>
#include <string.h>
#include <arpa/inet.h>

/**
 * @brief Create a length-prefixed IPC message
 *
 * Creates a message with a 4-byte network-order length prefix followed
 * by the payload. Caller must free the returned buffer.
 *
 * @param payload       The message payload (string)
 * @param total_len     Output: total length of the message (header + payload)
 * @return              Allocated buffer with header + payload, or NULL on error
 */
static inline char* ipc_create_message(const char* payload, size_t* total_len) {
    if (!payload || !total_len) return NULL;

    size_t payload_len = strlen(payload);
    *total_len = IPC_MSG_HEADER_SIZE + payload_len;

    char* buffer = (char*)malloc(*total_len);
    if (!buffer) return NULL;

    /* Write length header in network byte order */
    uint32_t net_len = htonl((uint32_t)payload_len);
    memcpy(buffer, &net_len, IPC_MSG_HEADER_SIZE);

    /* Copy payload */
    memcpy(buffer + IPC_MSG_HEADER_SIZE, payload, payload_len);

    return buffer;
}

/**
 * @brief Parse a length-prefixed IPC message
 *
 * Extracts the payload from a message with 4-byte length prefix.
 * Caller must free the returned string.
 *
 * @param buffer        The raw message buffer (header + payload)
 * @param buffer_len    Length of the buffer
 * @param payload       Output: allocated string containing payload (null-terminated)
 * @return              0 on success, -1 on error
 */
static inline int ipc_parse_message(const char* buffer, size_t buffer_len, char** payload) {
    if (!buffer || !payload || buffer_len < IPC_MSG_HEADER_SIZE) {
        return -1;
    }

    /* Read length header */
    uint32_t net_len;
    memcpy(&net_len, buffer, IPC_MSG_HEADER_SIZE);
    uint32_t payload_len = ntohl(net_len);

    /* Validate */
    if (buffer_len < IPC_MSG_HEADER_SIZE + payload_len) {
        return -1;
    }

    /* Allocate and copy payload */
    *payload = (char*)malloc(payload_len + 1);
    if (!*payload) return -1;

    memcpy(*payload, buffer + IPC_MSG_HEADER_SIZE, payload_len);
    (*payload)[payload_len] = '\0';

    return 0;
}

/* ============================================================================
 * Publisher/Subscriber Interface (Forward Declarations)
 * ========================================================================== */

/* These are implemented in ipc_publisher.c and ipc_subscriber.c */

/**
 * @brief Event callback type for subscribers
 */
typedef void (*ipc_event_callback_t)(const char* json_message, void* user_data);

/**
 * @brief Connection event callback type
 */
typedef void (*ipc_connect_callback_t)(ipc_handle_t* handle, bool connected, void* user_data);

#ifdef __cplusplus
}
#endif

#endif /* POC_IPC_COMMON_H */
