/**
 * @file monitor_events.c
 * @brief Event Monitor Tool
 *
 * Connects to the HAL Engine IPC socket and displays events in real-time.
 * Useful for debugging and monitoring event flow.
 *
 * @author FAM-HAL-v1.0-001
 * @date February 10, 2026
 */

#include "event_types.h"
#include "json_serializer.h"
#include "ipc_common.h"

#include <arpa/inet.h>
#include <errno.h>
#include <getopt.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <time.h>
#include <unistd.h>

/* ============================================================================
 * Constants
 * ========================================================================== */

#define DEFAULT_SOCKET_PATH     "/tmp/hal_events.sock"

static const char* VERSION = "1.0.0";
static const char* PROGRAM_NAME = "monitor_events";

/* ============================================================================
 * ANSI Colors
 * ========================================================================== */

#define COLOR_RESET     "\033[0m"
#define COLOR_GREEN     "\033[32m"
#define COLOR_RED       "\033[31m"
#define COLOR_YELLOW    "\033[33m"
#define COLOR_BLUE      "\033[34m"
#define COLOR_CYAN      "\033[36m"
#define COLOR_BOLD      "\033[1m"

/* ============================================================================
 * State
 * ========================================================================== */

static volatile sig_atomic_t g_running = 1;
static int g_socket_fd = -1;
static bool g_use_color = true;
static bool g_show_json = false;
static bool g_quiet = false;

/* ============================================================================
 * Functions
 * ========================================================================== */

static void signal_handler(int sig) {
    (void)sig;
    g_running = 0;
}

static void print_usage(void) {
    printf("Usage: %s [OPTIONS]\n", PROGRAM_NAME);
    printf("\n");
    printf("Event Monitor - Displays HAL events in real-time\n");
    printf("\n");
    printf("Options:\n");
    printf("  -s, --socket PATH      Socket path (default: %s)\n", DEFAULT_SOCKET_PATH);
    printf("  -j, --json             Show raw JSON instead of formatted output\n");
    printf("  -q, --quiet            Quiet mode - minimal output\n");
    printf("  -n, --no-color         Disable colored output\n");
    printf("  -c, --count N          Exit after N events\n");
    printf("  -t, --type TYPE        Filter by event type (granted, denied, all)\n");
    printf("  -V, --version          Print version and exit\n");
    printf("  -h, --help             Print this help\n");
    printf("\n");
    printf("Examples:\n");
    printf("  %s                     # Monitor all events\n", PROGRAM_NAME);
    printf("  %s -j                  # Show raw JSON\n", PROGRAM_NAME);
    printf("  %s -t granted          # Only show access granted events\n", PROGRAM_NAME);
    printf("  %s -c 10               # Show 10 events then exit\n", PROGRAM_NAME);
    printf("\n");
}

static void print_version(void) {
    printf("%s version %s\n", PROGRAM_NAME, VERSION);
    printf("HAL Azure Panel - Event Monitor\n");
}

static const char* event_type_string(event_type_t type) {
    switch (type) {
        case EVENT_ACCESS_GRANTED:  return "ACCESS_GRANTED";
        case EVENT_ACCESS_DENIED:   return "ACCESS_DENIED";
        case EVENT_DOOR_HELD_OPEN:  return "DOOR_HELD_OPEN";
        case EVENT_DOOR_FORCED:     return "DOOR_FORCED";
        case EVENT_TAMPER:          return "TAMPER";
        case EVENT_HEARTBEAT:       return "HEARTBEAT";
        default:                    return "UNKNOWN";
    }
}

static const char* access_result_string(access_result_t result) {
    switch (result) {
        case ACCESS_GRANTED:            return "Granted";
        case ACCESS_DENIED_UNKNOWN:     return "Unknown Card";
        case ACCESS_DENIED_EXPIRED:     return "Expired";
        case ACCESS_DENIED_SUSPENDED:   return "Suspended";
        case ACCESS_DENIED_TIME:        return "Time Restriction";
        case ACCESS_DENIED_ZONE:        return "Zone Restriction";
        default:                        return "Unknown";
    }
}

static const char* get_event_color(event_type_t type) {
    if (!g_use_color) return "";

    switch (type) {
        case EVENT_ACCESS_GRANTED:  return COLOR_GREEN;
        case EVENT_ACCESS_DENIED:   return COLOR_RED;
        case EVENT_DOOR_HELD_OPEN:  return COLOR_YELLOW;
        case EVENT_DOOR_FORCED:     return COLOR_RED COLOR_BOLD;
        case EVENT_TAMPER:          return COLOR_RED COLOR_BOLD;
        case EVENT_HEARTBEAT:       return COLOR_BLUE;
        default:                    return COLOR_CYAN;
    }
}

static void print_event(const hal_event_t* event, const char* json) {
    if (g_show_json) {
        printf("%s\n", json);
        fflush(stdout);
        return;
    }

    /* Format timestamp */
    time_t ts = (time_t)(event->occurred_timestamp / 1000);
    struct tm* tm_info = localtime(&ts);
    char time_str[32];
    strftime(time_str, sizeof(time_str), "%H:%M:%S", tm_info);

    /* Get color */
    const char* color = get_event_color(event->event_type);
    const char* reset = g_use_color ? COLOR_RESET : "";

    if (g_quiet) {
        printf("[%s] %s%s%s FC:%u Card:%u\n",
               time_str,
               color, event_type_string(event->event_type), reset,
               event->facility_code, event->card_number);
    } else {
        printf("\n");
        printf("%s╔══════════════════════════════════════════════════════════════╗%s\n", color, reset);
        printf("%s║ %-62s ║%s\n", color, event_type_string(event->event_type), reset);
        printf("%s╚══════════════════════════════════════════════════════════════╝%s\n", color, reset);
        printf("  Time:     %s.%03lld\n", time_str, (long long)(event->occurred_timestamp % 1000));
        printf("  Device:   %s (Port %u)\n", event->device_name, event->reader_port);
        printf("  Card:     FC=%u, CN=%u\n", event->facility_code, event->card_number);
        printf("  Result:   %s%s%s\n", color, access_result_string(event->access_result), reset);
        printf("  Event ID: %s\n", event->event_uid);
    }

    fflush(stdout);
}

static int connect_to_hal(const char* socket_path) {
    int fd = socket(AF_UNIX, SOCK_STREAM, 0);
    if (fd < 0) {
        perror("Failed to create socket");
        return -1;
    }

    struct sockaddr_un addr;
    memset(&addr, 0, sizeof(addr));
    addr.sun_family = AF_UNIX;
    strncpy(addr.sun_path, socket_path, sizeof(addr.sun_path) - 1);

    if (connect(fd, (struct sockaddr*)&addr, sizeof(addr)) < 0) {
        perror("Failed to connect to HAL Engine");
        close(fd);
        return -1;
    }

    return fd;
}

static int receive_event(int fd, char* buffer, size_t buffer_size) {
    /* Read 4-byte length header */
    uint32_t msg_len;
    ssize_t n = recv(fd, &msg_len, 4, MSG_WAITALL);
    if (n == 0) {
        return 0;  /* Connection closed */
    }
    if (n < 0) {
        if (errno == EINTR) return 1;  /* Interrupted */
        perror("Failed to read message length");
        return -1;
    }
    if (n != 4) {
        fprintf(stderr, "Short read on length header\n");
        return -1;
    }

    msg_len = ntohl(msg_len);
    if (msg_len == 0 || msg_len >= buffer_size) {
        fprintf(stderr, "Invalid message length: %u\n", msg_len);
        return -1;
    }

    /* Read message body */
    n = recv(fd, buffer, msg_len, MSG_WAITALL);
    if (n <= 0) {
        if (errno == EINTR) return 1;
        perror("Failed to read message body");
        return -1;
    }

    buffer[msg_len] = '\0';
    return 1;
}

/* ============================================================================
 * Main
 * ========================================================================== */

int main(int argc, char* argv[]) {
    static struct option long_options[] = {
        {"socket",   required_argument, 0, 's'},
        {"json",     no_argument,       0, 'j'},
        {"quiet",    no_argument,       0, 'q'},
        {"no-color", no_argument,       0, 'n'},
        {"count",    required_argument, 0, 'c'},
        {"type",     required_argument, 0, 't'},
        {"version",  no_argument,       0, 'V'},
        {"help",     no_argument,       0, 'h'},
        {0, 0, 0, 0}
    };

    const char* socket_path = DEFAULT_SOCKET_PATH;
    int max_count = 0;
    event_type_t filter_type = EVENT_UNKNOWN;
    bool filter_enabled = false;

    int opt;
    while ((opt = getopt_long(argc, argv, "s:jqnc:t:Vh", long_options, NULL)) != -1) {
        switch (opt) {
            case 's':
                socket_path = optarg;
                break;
            case 'j':
                g_show_json = true;
                break;
            case 'q':
                g_quiet = true;
                break;
            case 'n':
                g_use_color = false;
                break;
            case 'c':
                max_count = atoi(optarg);
                break;
            case 't':
                filter_enabled = true;
                if (strcasecmp(optarg, "granted") == 0) {
                    filter_type = EVENT_ACCESS_GRANTED;
                } else if (strcasecmp(optarg, "denied") == 0) {
                    filter_type = EVENT_ACCESS_DENIED;
                } else if (strcasecmp(optarg, "all") == 0) {
                    filter_enabled = false;
                } else {
                    fprintf(stderr, "Unknown event type: %s\n", optarg);
                    return 1;
                }
                break;
            case 'V':
                print_version();
                return 0;
            case 'h':
                print_usage();
                return 0;
            default:
                print_usage();
                return 1;
        }
    }

    /* Check if output is a terminal */
    if (!isatty(STDOUT_FILENO)) {
        g_use_color = false;
    }

    /* Set up signal handlers */
    signal(SIGINT, signal_handler);
    signal(SIGTERM, signal_handler);

    /* Connect to HAL Engine */
    printf("Connecting to HAL Engine at %s...\n", socket_path);

    g_socket_fd = connect_to_hal(socket_path);
    if (g_socket_fd < 0) {
        fprintf(stderr, "Hint: Make sure hal_engine is running\n");
        return 1;
    }

    printf("Connected! Waiting for events... (Ctrl+C to exit)\n");
    if (filter_enabled) {
        printf("Filter: %s only\n", event_type_string(filter_type));
    }
    if (max_count > 0) {
        printf("Will exit after %d events\n", max_count);
    }
    printf("\n");

    /* Event receiving loop */
    char buffer[IPC_MAX_MESSAGE_SIZE];
    int event_count = 0;

    while (g_running) {
        int result = receive_event(g_socket_fd, buffer, sizeof(buffer));

        if (result <= 0) {
            if (result == 0) {
                printf("\nConnection closed by HAL Engine\n");
            }
            break;
        }

        /* Parse event */
        hal_event_t event;
        if (json_to_event(buffer, &event) != 0) {
            fprintf(stderr, "Failed to parse event JSON\n");
            continue;
        }

        /* Apply filter */
        if (filter_enabled && event.event_type != filter_type) {
            continue;
        }

        /* Display event */
        print_event(&event, buffer);
        event_count++;

        /* Check count limit */
        if (max_count > 0 && event_count >= max_count) {
            printf("\nReached event limit (%d)\n", max_count);
            break;
        }
    }

    /* Cleanup */
    if (g_socket_fd >= 0) {
        close(g_socket_fd);
    }

    printf("\nReceived %d events\n", event_count);
    return 0;
}
