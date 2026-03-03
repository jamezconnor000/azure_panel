/**
 * @file ipc_subscriber.c
 * @brief IPC subscriber implementation
 *
 * @author FAM-HAL-v1.0-001
 * @date February 10, 2026
 */

#include "ipc_subscriber.h"
#include "json_serializer.h"
#include "logger.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <errno.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <sys/select.h>
#include <arpa/inet.h>
#include <pthread.h>

/* ============================================================================
 * Static State
 * ========================================================================== */

static int s_socket_fd = -1;
static char s_socket_path[256] = {0};
static bool s_initialized = false;
static pthread_mutex_t s_mutex = PTHREAD_MUTEX_INITIALIZER;

/* Callback */
static event_callback_fn s_callback = NULL;

/* Statistics */
static uint64_t s_messages_received = 0;
static uint64_t s_bytes_received = 0;
static int s_reconnects = 0;

/* ============================================================================
 * Public Functions
 * ========================================================================== */

int ipc_subscriber_init(event_callback_fn callback) {
    pthread_mutex_lock(&s_mutex);

    if (s_initialized) {
        pthread_mutex_unlock(&s_mutex);
        return 0;
    }

    s_callback = callback;
    s_socket_fd = -1;
    s_messages_received = 0;
    s_bytes_received = 0;
    s_reconnects = 0;

    s_initialized = true;
    LOG_INFO("IPC subscriber initialized");

    pthread_mutex_unlock(&s_mutex);
    return 0;
}

void ipc_subscriber_shutdown(void) {
    pthread_mutex_lock(&s_mutex);

    if (!s_initialized) {
        pthread_mutex_unlock(&s_mutex);
        return;
    }

    if (s_socket_fd >= 0) {
        close(s_socket_fd);
        s_socket_fd = -1;
    }

    s_initialized = false;
    LOG_INFO("IPC subscriber shutdown");

    pthread_mutex_unlock(&s_mutex);
}

int ipc_subscriber_connect(const char* socket_path) {
    pthread_mutex_lock(&s_mutex);

    if (!s_initialized) {
        pthread_mutex_unlock(&s_mutex);
        return -1;
    }

    if (s_socket_fd >= 0) {
        /* Already connected */
        pthread_mutex_unlock(&s_mutex);
        return 0;
    }

    if (socket_path) {
        strncpy(s_socket_path, socket_path, sizeof(s_socket_path) - 1);
    }

    /* Create socket */
    s_socket_fd = socket(AF_UNIX, SOCK_STREAM, 0);
    if (s_socket_fd < 0) {
        LOG_ERROR("Failed to create socket: %s", strerror(errno));
        pthread_mutex_unlock(&s_mutex);
        return -1;
    }

    /* Connect to server */
    struct sockaddr_un addr;
    memset(&addr, 0, sizeof(addr));
    addr.sun_family = AF_UNIX;
    strncpy(addr.sun_path, s_socket_path, sizeof(addr.sun_path) - 1);

    if (connect(s_socket_fd, (struct sockaddr*)&addr, sizeof(addr)) < 0) {
        LOG_DEBUG("Failed to connect to %s: %s", s_socket_path, strerror(errno));
        close(s_socket_fd);
        s_socket_fd = -1;
        pthread_mutex_unlock(&s_mutex);
        return -1;
    }

    s_reconnects++;
    LOG_INFO("Connected to IPC publisher: %s", s_socket_path);

    pthread_mutex_unlock(&s_mutex);
    return 0;
}

void ipc_subscriber_disconnect(void) {
    pthread_mutex_lock(&s_mutex);

    if (s_socket_fd >= 0) {
        close(s_socket_fd);
        s_socket_fd = -1;
        LOG_INFO("Disconnected from IPC publisher");
    }

    pthread_mutex_unlock(&s_mutex);
}

bool ipc_subscriber_is_connected(void) {
    pthread_mutex_lock(&s_mutex);
    bool connected = s_socket_fd >= 0;
    pthread_mutex_unlock(&s_mutex);
    return connected;
}

int ipc_subscriber_poll(int timeout_ms) {
    pthread_mutex_lock(&s_mutex);

    if (!s_initialized || s_socket_fd < 0) {
        pthread_mutex_unlock(&s_mutex);
        return -1;
    }

    int fd = s_socket_fd;
    pthread_mutex_unlock(&s_mutex);

    /* Use select for timeout */
    fd_set read_fds;
    FD_ZERO(&read_fds);
    FD_SET(fd, &read_fds);

    struct timeval tv;
    tv.tv_sec = timeout_ms / 1000;
    tv.tv_usec = (timeout_ms % 1000) * 1000;

    int result = select(fd + 1, &read_fds, NULL, NULL, &tv);
    if (result == 0) {
        return 0;  /* Timeout */
    } else if (result < 0) {
        if (errno != EINTR) {
            LOG_ERROR("Select failed: %s", strerror(errno));
        }
        return -1;
    }

    /* Data available - read message */
    char buffer[IPC_MAX_MESSAGE_SIZE];

    /* Read message length (4 bytes) */
    uint32_t net_len;
    ssize_t n = recv(fd, &net_len, sizeof(net_len), MSG_WAITALL);
    if (n <= 0) {
        if (n == 0) {
            LOG_WARN("Connection closed by publisher");
        } else {
            LOG_ERROR("Failed to read message length: %s", strerror(errno));
        }

        pthread_mutex_lock(&s_mutex);
        close(s_socket_fd);
        s_socket_fd = -1;
        pthread_mutex_unlock(&s_mutex);

        return -1;
    }

    uint32_t msg_len = ntohl(net_len);

    if (msg_len >= sizeof(buffer)) {
        LOG_ERROR("Message too large: %u bytes", msg_len);
        return -1;
    }

    /* Read message body */
    n = recv(fd, buffer, msg_len, MSG_WAITALL);
    if (n != (ssize_t)msg_len) {
        LOG_ERROR("Failed to read message body: %s", strerror(errno));
        return -1;
    }

    buffer[msg_len] = '\0';

    pthread_mutex_lock(&s_mutex);
    s_messages_received++;
    s_bytes_received += msg_len;
    pthread_mutex_unlock(&s_mutex);

    /* Parse event and invoke callback */
    if (s_callback) {
        hal_event_t event;
        if (json_to_event(buffer, &event) == 0) {
            s_callback(&event);
        } else {
            LOG_ERROR("Failed to parse event JSON");
        }
    }

    return 0;
}

int ipc_subscriber_receive(hal_event_t* event, int timeout_ms) {
    if (!event) {
        return -1;
    }

    pthread_mutex_lock(&s_mutex);

    if (!s_initialized || s_socket_fd < 0) {
        pthread_mutex_unlock(&s_mutex);
        return -1;
    }

    int fd = s_socket_fd;
    pthread_mutex_unlock(&s_mutex);

    /* Use select for timeout */
    if (timeout_ms > 0) {
        fd_set read_fds;
        FD_ZERO(&read_fds);
        FD_SET(fd, &read_fds);

        struct timeval tv;
        tv.tv_sec = timeout_ms / 1000;
        tv.tv_usec = (timeout_ms % 1000) * 1000;

        int result = select(fd + 1, &read_fds, NULL, NULL, &tv);
        if (result == 0) {
            return 1;  /* Timeout */
        } else if (result < 0) {
            if (errno != EINTR) {
                LOG_ERROR("Select failed: %s", strerror(errno));
            }
            return -1;
        }
    }

    char buffer[IPC_MAX_MESSAGE_SIZE];

    /* Read message length (4 bytes) */
    uint32_t net_len;
    ssize_t n = recv(fd, &net_len, sizeof(net_len), MSG_WAITALL);
    if (n <= 0) {
        if (n == 0) {
            LOG_WARN("Connection closed by publisher");
        } else {
            LOG_ERROR("Failed to read message length: %s", strerror(errno));
        }

        pthread_mutex_lock(&s_mutex);
        close(s_socket_fd);
        s_socket_fd = -1;
        pthread_mutex_unlock(&s_mutex);

        return -1;
    }

    uint32_t msg_len = ntohl(net_len);

    if (msg_len >= sizeof(buffer)) {
        LOG_ERROR("Message too large: %u bytes", msg_len);
        return -1;
    }

    /* Read message body */
    n = recv(fd, buffer, msg_len, MSG_WAITALL);
    if (n != (ssize_t)msg_len) {
        LOG_ERROR("Failed to read message body: %s", strerror(errno));
        return -1;
    }

    buffer[msg_len] = '\0';

    pthread_mutex_lock(&s_mutex);
    s_messages_received++;
    s_bytes_received += msg_len;
    pthread_mutex_unlock(&s_mutex);

    /* Parse event */
    if (json_to_event(buffer, event) != 0) {
        LOG_ERROR("Failed to parse event JSON");
        return -1;
    }

    return 0;
}

int ipc_subscriber_receive_raw(char* buffer, size_t buf_size, int timeout_ms) {
    pthread_mutex_lock(&s_mutex);

    if (!s_initialized || s_socket_fd < 0 || !buffer || buf_size == 0) {
        pthread_mutex_unlock(&s_mutex);
        return -1;
    }

    int fd = s_socket_fd;
    pthread_mutex_unlock(&s_mutex);

    /* Use select for timeout */
    if (timeout_ms > 0) {
        fd_set read_fds;
        FD_ZERO(&read_fds);
        FD_SET(fd, &read_fds);

        struct timeval tv;
        tv.tv_sec = timeout_ms / 1000;
        tv.tv_usec = (timeout_ms % 1000) * 1000;

        int result = select(fd + 1, &read_fds, NULL, NULL, &tv);
        if (result == 0) {
            return 0;  /* Timeout */
        } else if (result < 0) {
            if (errno != EINTR) {
                LOG_ERROR("Select failed: %s", strerror(errno));
            }
            return -1;
        }
    }

    /* Read message length (4 bytes) */
    uint32_t net_len;
    ssize_t n = recv(fd, &net_len, sizeof(net_len), MSG_WAITALL);
    if (n <= 0) {
        if (n == 0) {
            LOG_WARN("Connection closed by publisher");
        } else {
            LOG_ERROR("Failed to read message length: %s", strerror(errno));
        }

        pthread_mutex_lock(&s_mutex);
        close(s_socket_fd);
        s_socket_fd = -1;
        pthread_mutex_unlock(&s_mutex);

        return -1;
    }

    uint32_t msg_len = ntohl(net_len);

    if (msg_len >= buf_size) {
        LOG_ERROR("Message too large: %u bytes", msg_len);
        return -1;
    }

    /* Read message body */
    n = recv(fd, buffer, msg_len, MSG_WAITALL);
    if (n != (ssize_t)msg_len) {
        LOG_ERROR("Failed to read message body: %s", strerror(errno));
        return -1;
    }

    buffer[msg_len] = '\0';

    pthread_mutex_lock(&s_mutex);
    s_messages_received++;
    s_bytes_received += msg_len;
    pthread_mutex_unlock(&s_mutex);

    return (int)msg_len;
}

void ipc_subscriber_get_stats(uint64_t* messages_received, uint64_t* bytes_received,
                              int* reconnects) {
    pthread_mutex_lock(&s_mutex);

    if (messages_received) *messages_received = s_messages_received;
    if (bytes_received) *bytes_received = s_bytes_received;
    if (reconnects) *reconnects = s_reconnects;

    pthread_mutex_unlock(&s_mutex);
}
