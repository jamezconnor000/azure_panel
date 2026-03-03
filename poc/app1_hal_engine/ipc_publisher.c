/**
 * @file ipc_publisher.c
 * @brief IPC publisher implementation
 *
 * @author FAM-HAL-v1.0-001
 * @date February 10, 2026
 */

#include "ipc_publisher.h"
#include "json_serializer.h"
#include "logger.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <errno.h>
#include <fcntl.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <arpa/inet.h>
#include <pthread.h>

/* ============================================================================
 * Constants
 * ========================================================================== */

#define MAX_SUBSCRIBERS 16

/* ============================================================================
 * Static State
 * ========================================================================== */

static int s_server_fd = -1;
static char s_socket_path[108];
static bool s_initialized = false;
static pthread_mutex_t s_mutex = PTHREAD_MUTEX_INITIALIZER;

/* Subscriber list */
static int s_subscribers[MAX_SUBSCRIBERS];
static int s_subscriber_count = 0;

/* Statistics */
static uint64_t s_messages_sent = 0;
static uint64_t s_bytes_sent = 0;

/* ============================================================================
 * Internal Functions
 * ========================================================================== */

static int set_nonblocking(int fd) {
    int flags = fcntl(fd, F_GETFL, 0);
    if (flags == -1) {
        return -1;
    }
    return fcntl(fd, F_SETFL, flags | O_NONBLOCK);
}

static void remove_subscriber(int index) {
    if (index < 0 || index >= s_subscriber_count) {
        return;
    }

    close(s_subscribers[index]);

    /* Shift remaining subscribers down */
    for (int i = index; i < s_subscriber_count - 1; i++) {
        s_subscribers[i] = s_subscribers[i + 1];
    }

    s_subscriber_count--;
    LOG_DEBUG("Subscriber disconnected, count now %d", s_subscriber_count);
}

static int send_message(int fd, const char* json) {
    if (fd < 0 || !json) {
        return -1;
    }

    uint32_t len = strlen(json);
    uint32_t net_len = htonl(len);

    /* Send length prefix */
    ssize_t sent = send(fd, &net_len, sizeof(net_len), MSG_NOSIGNAL);
    if (sent != sizeof(net_len)) {
        return -1;
    }

    /* Send message body */
    size_t total_sent = 0;
    while (total_sent < len) {
        sent = send(fd, json + total_sent, len - total_sent, MSG_NOSIGNAL);
        if (sent <= 0) {
            return -1;
        }
        total_sent += sent;
    }

    return (int)total_sent;
}

/* ============================================================================
 * Public Functions
 * ========================================================================== */

int ipc_publisher_init(const char* socket_path) {
    pthread_mutex_lock(&s_mutex);

    if (s_initialized) {
        pthread_mutex_unlock(&s_mutex);
        return 0;
    }

    if (!socket_path || strlen(socket_path) >= sizeof(s_socket_path)) {
        LOG_ERROR("Invalid socket path");
        pthread_mutex_unlock(&s_mutex);
        return -1;
    }

    strncpy(s_socket_path, socket_path, sizeof(s_socket_path) - 1);

    /* Remove any existing socket file */
    unlink(s_socket_path);

    /* Create socket */
    s_server_fd = socket(AF_UNIX, SOCK_STREAM, 0);
    if (s_server_fd < 0) {
        LOG_ERROR("Failed to create socket: %s", strerror(errno));
        pthread_mutex_unlock(&s_mutex);
        return -1;
    }

    /* Bind to socket path */
    struct sockaddr_un addr;
    memset(&addr, 0, sizeof(addr));
    addr.sun_family = AF_UNIX;
    strncpy(addr.sun_path, s_socket_path, sizeof(addr.sun_path) - 1);

    if (bind(s_server_fd, (struct sockaddr*)&addr, sizeof(addr)) < 0) {
        LOG_ERROR("Failed to bind socket: %s", strerror(errno));
        close(s_server_fd);
        s_server_fd = -1;
        pthread_mutex_unlock(&s_mutex);
        return -1;
    }

    /* Start listening */
    if (listen(s_server_fd, IPC_BACKLOG) < 0) {
        LOG_ERROR("Failed to listen: %s", strerror(errno));
        close(s_server_fd);
        unlink(s_socket_path);
        s_server_fd = -1;
        pthread_mutex_unlock(&s_mutex);
        return -1;
    }

    /* Set non-blocking for accept */
    set_nonblocking(s_server_fd);

    /* Initialize subscriber array */
    for (int i = 0; i < MAX_SUBSCRIBERS; i++) {
        s_subscribers[i] = -1;
    }
    s_subscriber_count = 0;

    s_initialized = true;
    s_messages_sent = 0;
    s_bytes_sent = 0;

    LOG_INFO("IPC publisher initialized: %s", s_socket_path);
    pthread_mutex_unlock(&s_mutex);
    return 0;
}

void ipc_publisher_shutdown(void) {
    pthread_mutex_lock(&s_mutex);

    if (!s_initialized) {
        pthread_mutex_unlock(&s_mutex);
        return;
    }

    /* Close all subscriber connections */
    for (int i = 0; i < s_subscriber_count; i++) {
        if (s_subscribers[i] >= 0) {
            close(s_subscribers[i]);
            s_subscribers[i] = -1;
        }
    }
    s_subscriber_count = 0;

    /* Close server socket */
    if (s_server_fd >= 0) {
        close(s_server_fd);
        s_server_fd = -1;
    }

    /* Remove socket file */
    unlink(s_socket_path);

    s_initialized = false;
    LOG_INFO("IPC publisher shutdown");

    pthread_mutex_unlock(&s_mutex);
}

int ipc_publisher_accept(void) {
    pthread_mutex_lock(&s_mutex);

    if (!s_initialized || s_server_fd < 0) {
        pthread_mutex_unlock(&s_mutex);
        return 0;
    }

    int accepted = 0;

    while (s_subscriber_count < MAX_SUBSCRIBERS) {
        int client_fd = accept(s_server_fd, NULL, NULL);
        if (client_fd < 0) {
            if (errno == EAGAIN || errno == EWOULDBLOCK) {
                /* No more pending connections */
                break;
            }
            LOG_WARN("Accept failed: %s", strerror(errno));
            break;
        }

        /* Set non-blocking */
        set_nonblocking(client_fd);

        s_subscribers[s_subscriber_count++] = client_fd;
        accepted++;

        LOG_INFO("New subscriber connected (fd=%d), count now %d",
                 client_fd, s_subscriber_count);
    }

    pthread_mutex_unlock(&s_mutex);
    return accepted;
}

int ipc_publisher_publish(const hal_event_t* event) {
    if (!event) {
        return 0;
    }

    /* Create IPC message */
    char* json = create_ipc_message(event, IPC_MSG_TYPE_EVENT);
    if (!json) {
        LOG_ERROR("Failed to serialize event");
        return 0;
    }

    int sent = ipc_publisher_publish_raw(json);
    free(json);

    return sent;
}

int ipc_publisher_publish_raw(const char* json) {
    pthread_mutex_lock(&s_mutex);

    if (!s_initialized || !json) {
        pthread_mutex_unlock(&s_mutex);
        return 0;
    }

    int sent_count = 0;
    size_t json_len = strlen(json);

    /* Send to all subscribers, removing failed ones */
    for (int i = s_subscriber_count - 1; i >= 0; i--) {
        int fd = s_subscribers[i];
        if (fd < 0) {
            continue;
        }

        int result = send_message(fd, json);
        if (result > 0) {
            sent_count++;
            s_bytes_sent += result;
        } else {
            LOG_DEBUG("Failed to send to subscriber fd=%d, removing", fd);
            remove_subscriber(i);
        }
    }

    if (sent_count > 0) {
        s_messages_sent++;
        LOG_DEBUG("Published event to %d subscribers (%zu bytes)",
                  sent_count, json_len);
    }

    pthread_mutex_unlock(&s_mutex);
    return sent_count;
}

int ipc_publisher_subscriber_count(void) {
    pthread_mutex_lock(&s_mutex);
    int count = s_subscriber_count;
    pthread_mutex_unlock(&s_mutex);
    return count;
}

bool ipc_publisher_is_ready(void) {
    return s_initialized && s_server_fd >= 0;
}

void ipc_publisher_get_stats(uint64_t* messages_sent, uint64_t* bytes_sent,
                             int* subscribers) {
    pthread_mutex_lock(&s_mutex);

    if (messages_sent) *messages_sent = s_messages_sent;
    if (bytes_sent) *bytes_sent = s_bytes_sent;
    if (subscribers) *subscribers = s_subscriber_count;

    pthread_mutex_unlock(&s_mutex);
}
