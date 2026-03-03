/**
 * @file main.c
 * @brief Ambient.ai Event Forwarder - Entry point
 *
 * Receives events from the HAL Access Control Engine via Unix socket
 * and forwards them to Ambient.ai Generic Cloud Event API.
 *
 * @author FAM-HAL-v1.0-001
 * @date February 10, 2026
 */

#include "forwarder.h"
#include "config.h"
#include "logger.h"

#include <getopt.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

/* ============================================================================
 * Constants and Defaults
 * ========================================================================== */

#define DEFAULT_CONFIG_PATH     "/etc/hal/ambient_forwarder.json"
#define DEFAULT_DEVICES_PATH    "/etc/hal/devices.json"
#define DEFAULT_LOG_FILE        "/var/log/hal/forwarder.log"

static const char* VERSION = "1.0.0";
static const char* PROGRAM_NAME = "ambient_forwarder";

/* ============================================================================
 * Signal Handling
 * ========================================================================== */

static volatile sig_atomic_t g_shutdown = 0;

static void signal_handler(int sig) {
    (void)sig;
    g_shutdown = 1;
    forwarder_stop();
}

static void setup_signals(void) {
    struct sigaction sa;
    memset(&sa, 0, sizeof(sa));
    sa.sa_handler = signal_handler;
    sigemptyset(&sa.sa_mask);
    sa.sa_flags = 0;

    sigaction(SIGINT, &sa, NULL);
    sigaction(SIGTERM, &sa, NULL);
    sigaction(SIGHUP, &sa, NULL);

    /* Ignore SIGPIPE */
    signal(SIGPIPE, SIG_IGN);
}

/* ============================================================================
 * Usage and Help
 * ========================================================================== */

static void print_usage(void) {
    printf("Usage: %s [OPTIONS]\n", PROGRAM_NAME);
    printf("\n");
    printf("Ambient.ai Event Forwarder - Forwards HAL events to Ambient.ai cloud\n");
    printf("\n");
    printf("Options:\n");
    printf("  -c, --config PATH      Configuration file (default: %s)\n", DEFAULT_CONFIG_PATH);
    printf("  -d, --devices PATH     Devices config file (default: %s)\n", DEFAULT_DEVICES_PATH);
    printf("  -s, --socket PATH      IPC socket path (override config)\n");
    printf("  -e, --endpoint URL     Ambient API endpoint (override config)\n");
    printf("  -k, --api-key KEY      Ambient API key (override config)\n");
    printf("  -l, --log-file PATH    Log file path (default: %s)\n", DEFAULT_LOG_FILE);
    printf("  -v, --verbose          Increase log verbosity\n");
    printf("  -q, --quiet            Decrease log verbosity\n");
    printf("  -f, --foreground       Run in foreground (no log to file)\n");
    printf("  -t, --test             Test mode - connect and print events only\n");
    printf("      --no-retry         Disable retry queue\n");
    printf("      --stats            Print stats every 30 seconds\n");
    printf("  -V, --version          Print version and exit\n");
    printf("  -h, --help             Print this help and exit\n");
    printf("\n");
    printf("Examples:\n");
    printf("  %s                          # Use default config\n", PROGRAM_NAME);
    printf("  %s -c /path/to/config.json  # Custom config\n", PROGRAM_NAME);
    printf("  %s -f -v                    # Foreground with debug logging\n", PROGRAM_NAME);
    printf("  %s -t                       # Test mode\n", PROGRAM_NAME);
    printf("\n");
}

static void print_version(void) {
    printf("%s version %s\n", PROGRAM_NAME, VERSION);
    printf("HAL Azure Panel - Aether Access\n");
    printf("Ambient.ai Event Forwarder\n");
}

/* ============================================================================
 * Main Entry Point
 * ========================================================================== */

int main(int argc, char* argv[]) {
    /* Command line options */
    static struct option long_options[] = {
        {"config",      required_argument, 0, 'c'},
        {"devices",     required_argument, 0, 'd'},
        {"socket",      required_argument, 0, 's'},
        {"endpoint",    required_argument, 0, 'e'},
        {"api-key",     required_argument, 0, 'k'},
        {"log-file",    required_argument, 0, 'l'},
        {"verbose",     no_argument,       0, 'v'},
        {"quiet",       no_argument,       0, 'q'},
        {"foreground",  no_argument,       0, 'f'},
        {"test",        no_argument,       0, 't'},
        {"no-retry",    no_argument,       0,  1 },
        {"stats",       no_argument,       0,  2 },
        {"version",     no_argument,       0, 'V'},
        {"help",        no_argument,       0, 'h'},
        {0, 0, 0, 0}
    };

    const char* config_path = DEFAULT_CONFIG_PATH;
    const char* devices_path = NULL;
    const char* socket_path = NULL;
    const char* endpoint_url = NULL;
    const char* api_key = NULL;
    const char* log_file = NULL;
    int log_level = LOG_LEVEL_INFO;
    bool foreground = false;
    bool test_mode = false;
    bool no_retry = false;
    bool show_stats = false;

    int opt;
    int option_index = 0;

    while ((opt = getopt_long(argc, argv, "c:d:s:e:k:l:vqftVh",
                              long_options, &option_index)) != -1) {
        switch (opt) {
            case 'c':
                config_path = optarg;
                break;
            case 'd':
                devices_path = optarg;
                break;
            case 's':
                socket_path = optarg;
                break;
            case 'e':
                endpoint_url = optarg;
                break;
            case 'k':
                api_key = optarg;
                break;
            case 'l':
                log_file = optarg;
                break;
            case 'v':
                if (log_level > LOG_LEVEL_DEBUG) log_level--;
                break;
            case 'q':
                if (log_level < LOG_LEVEL_ERROR) log_level++;
                break;
            case 'f':
                foreground = true;
                break;
            case 't':
                test_mode = true;
                foreground = true;
                break;
            case 1:  /* --no-retry */
                no_retry = true;
                break;
            case 2:  /* --stats */
                show_stats = true;
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

    /* Initialize logging */
    logger_config_t log_config = {
        .level = log_level,
        .console_enabled = foreground,
        .file_enabled = !foreground,
        .max_rotated_files = 5,
        .max_file_size_mb = 10,
        .include_timestamp = true,
        .include_level = true,
        .include_source = false
    };
    strcpy(log_config.app_name, "forwarder");

    if (log_file) {
        strncpy(log_config.log_file, log_file, sizeof(log_config.log_file) - 1);
    } else {
        strncpy(log_config.log_file, DEFAULT_LOG_FILE, sizeof(log_config.log_file) - 1);
    }

    if (logger_init(&log_config) != 0) {
        fprintf(stderr, "Failed to initialize logging\n");
        return 1;
    }

    LOG_INFO("==============================================");
    LOG_INFO("Ambient.ai Event Forwarder v%s starting", VERSION);
    LOG_INFO("==============================================");

    /* Set up signal handlers */
    setup_signals();

    /* Load configuration */
    forwarder_config_t fwd_config;
    forwarder_config_defaults(&fwd_config);

    if (forwarder_config_load(config_path, &fwd_config) != 0) {
        LOG_WARN("Could not load config from %s, using defaults", config_path);
    }

    /* Apply command-line overrides */
    if (devices_path) {
        strncpy(fwd_config.devices_config_path, devices_path,
                sizeof(fwd_config.devices_config_path) - 1);
    }
    if (socket_path) {
        strncpy(fwd_config.ipc_socket_path, socket_path,
                sizeof(fwd_config.ipc_socket_path) - 1);
    }
    if (endpoint_url) {
        strncpy(fwd_config.ambient_endpoint, endpoint_url,
                sizeof(fwd_config.ambient_endpoint) - 1);
    }
    if (api_key) {
        strncpy(fwd_config.ambient_api_key, api_key,
                sizeof(fwd_config.ambient_api_key) - 1);
    }
    if (no_retry) {
        fwd_config.retry_enabled = false;
    }

    /* Validate configuration */
    if (forwarder_config_validate(&fwd_config) != 0) {
        LOG_ERROR("Configuration validation failed");
        logger_shutdown();
        return 1;
    }

    if (foreground) {
        forwarder_config_print(&fwd_config);
    }

    /* Test mode - just verify connectivity */
    if (test_mode) {
        LOG_INFO("Test mode - will only print received events");
    }

    /* Convert to forwarder config */
    forwarder_config_t config;
    memset(&config, 0, sizeof(config));

    strncpy(config.ipc_socket_path, fwd_config.ipc_socket_path, sizeof(config.ipc_socket_path) - 1);
    config.ipc_reconnect_delay_ms = fwd_config.ipc_reconnect_delay_ms;
    strncpy(config.ambient_endpoint, fwd_config.ambient_endpoint, sizeof(config.ambient_endpoint) - 1);
    strncpy(config.ambient_api_key, fwd_config.ambient_api_key, sizeof(config.ambient_api_key) - 1);
    config.ambient_timeout_ms = fwd_config.ambient_timeout_ms;
    config.ambient_verify_ssl = fwd_config.ambient_verify_ssl;
    strncpy(config.user_agent, fwd_config.user_agent, sizeof(config.user_agent) - 1);
    config.retry_enabled = fwd_config.retry_enabled;
    strncpy(config.retry_db_path, fwd_config.retry_db_path, sizeof(config.retry_db_path) - 1);
    config.retry_max_queue_size = fwd_config.retry_max_queue_size;
    config.retry_interval_sec = fwd_config.retry_interval_sec;
    config.retry_max_attempts = fwd_config.retry_max_attempts;
    strncpy(config.devices_config_path, fwd_config.devices_config_path, sizeof(config.devices_config_path) - 1);

    /* Initialize forwarder */
    if (forwarder_init(&config) != 0) {
        LOG_ERROR("Failed to initialize forwarder");
        logger_shutdown();
        return 1;
    }

    /* Start forwarder */
    if (forwarder_start() != 0) {
        LOG_ERROR("Failed to start forwarder");
        forwarder_shutdown();
        logger_shutdown();
        return 1;
    }

    LOG_INFO("Forwarder started, waiting for events...");

    /* Main loop */
    int stats_counter = 0;
    while (!g_shutdown && forwarder_is_running()) {
        sleep(1);

        if (show_stats) {
            stats_counter++;
            if (stats_counter >= 30) {
                forwarder_print_stats();
                stats_counter = 0;
            }
        }
    }

    LOG_INFO("Shutting down...");

    /* Cleanup */
    forwarder_shutdown();

    LOG_INFO("Forwarder stopped");
    logger_shutdown();

    return 0;
}
