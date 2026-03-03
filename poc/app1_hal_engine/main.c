/**
 * @file main.c
 * @brief HAL Access Engine main entry point
 *
 * @author FAM-HAL-v1.0-001
 * @date February 10, 2026
 */

#include "hal_engine.h"
#include "config.h"
#include "logger.h"

#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <signal.h>
#include <getopt.h>
#include <unistd.h>

/* ============================================================================
 * Globals
 * ========================================================================== */

static const char* VERSION = "1.0.0";

/* ============================================================================
 * Signal Handling
 * ========================================================================== */

static void signal_handler(int sig) {
    (void)sig;
    LOG_INFO("Received shutdown signal");
    hal_engine_stop();
}

static void setup_signal_handlers(void) {
    struct sigaction sa;
    sa.sa_handler = signal_handler;
    sigemptyset(&sa.sa_mask);
    sa.sa_flags = 0;

    sigaction(SIGINT, &sa, NULL);
    sigaction(SIGTERM, &sa, NULL);
}

/* ============================================================================
 * Usage
 * ========================================================================== */

static void print_usage(const char* prog_name) {
    printf("\n");
    printf("Aether Access - HAL Engine v%s\n", VERSION);
    printf("================================\n\n");
    printf("Usage: %s [OPTIONS]\n\n", prog_name);
    printf("Options:\n");
    printf("  -c, --config FILE    Configuration file (default: config/hal_engine.json)\n");
    printf("  -d, --daemon         Run as daemon\n");
    printf("  -v, --verbose        Verbose output (DEBUG level)\n");
    printf("  -q, --quiet          Quiet output (ERROR level only)\n");
    printf("  -h, --help           Show this help message\n");
    printf("  -V, --version        Show version\n");
    printf("\n");
    printf("Simulation:\n");
    printf("  Send card data to the FIFO: echo 'FC:CN' > /tmp/hal_sim_wiegand\n");
    printf("  Example: echo '100:12345' > /tmp/hal_sim_wiegand\n");
    printf("\n");
}

static void print_version(void) {
    printf("HAL Engine v%s\n", VERSION);
    printf("Aether Access - Physical Access Control\n");
    printf("Copyright 2026 CST Physical Access Control Systems\n");
}

/* ============================================================================
 * Main
 * ========================================================================== */

int main(int argc, char* argv[]) {
    const char* config_path = "config/hal_engine.json";
    bool run_daemon = false;
    int log_level = -1;  /* -1 means use config file value */

    /* Parse command line options */
    static struct option long_options[] = {
        {"config",  required_argument, 0, 'c'},
        {"daemon",  no_argument,       0, 'd'},
        {"verbose", no_argument,       0, 'v'},
        {"quiet",   no_argument,       0, 'q'},
        {"help",    no_argument,       0, 'h'},
        {"version", no_argument,       0, 'V'},
        {0, 0, 0, 0}
    };

    int opt;
    while ((opt = getopt_long(argc, argv, "c:dvqhV", long_options, NULL)) != -1) {
        switch (opt) {
            case 'c':
                config_path = optarg;
                break;
            case 'd':
                run_daemon = true;
                break;
            case 'v':
                log_level = LOG_LEVEL_DEBUG;
                break;
            case 'q':
                log_level = LOG_LEVEL_ERROR;
                break;
            case 'h':
                print_usage(argv[0]);
                return 0;
            case 'V':
                print_version();
                return 0;
            default:
                print_usage(argv[0]);
                return 1;
        }
    }

    /* Load configuration */
    hal_engine_config_t config;
    if (config_load(config_path, &config) != 0) {
        fprintf(stderr, "Failed to load configuration\n");
        return 1;
    }

    /* Override log level if specified on command line */
    if (log_level >= 0) {
        config.log_level = log_level;
    }

    /* Initialize logger */
    logger_config_t log_config;
    logger_get_default_config(&log_config);
    log_config.level = config.log_level;
    log_config.console_enabled = config.log_console;
    log_config.file_enabled = config.log_file[0] != '\0';
    strncpy(log_config.log_file, config.log_file, sizeof(log_config.log_file) - 1);
    strncpy(log_config.app_name, "hal_engine", sizeof(log_config.app_name) - 1);

    if (logger_init(&log_config) != 0) {
        fprintf(stderr, "Failed to initialize logger\n");
        return 1;
    }

    LOG_INFO("=========================================");
    LOG_INFO(" Aether Access - HAL Engine v%s", VERSION);
    LOG_INFO("=========================================");

    /* Print configuration */
    config_print(&config);

    /* Daemonize if requested */
    if (run_daemon) {
        LOG_INFO("Daemonizing...");
        if (daemon(1, 0) != 0) {
            LOG_ERROR("Failed to daemonize: %s", strerror(errno));
            logger_shutdown();
            return 1;
        }
    }

    /* Setup signal handlers */
    setup_signal_handlers();

    /* Initialize HAL engine */
    if (hal_engine_init(&config) != 0) {
        LOG_ERROR("Failed to initialize HAL engine");
        logger_shutdown();
        return 1;
    }

    LOG_INFO("HAL engine ready, waiting for card reads...");
    LOG_INFO("Simulation: echo 'FC:CN' > %s", config.sim_fifo_path);

    /* Run the engine */
    int result = hal_engine_run();

    /* Cleanup */
    hal_engine_shutdown();

    /* Print final statistics */
    hal_engine_stats_t stats;
    hal_engine_get_stats(&stats);
    LOG_INFO("Final statistics:");
    LOG_INFO("  Cards processed: %lu", stats.cards_processed);
    LOG_INFO("  Access granted:  %lu", stats.access_granted);
    LOG_INFO("  Access denied:   %lu", stats.access_denied);
    LOG_INFO("  Events published: %lu", stats.events_published);
    LOG_INFO("  Events failed:    %lu", stats.events_failed);

    logger_shutdown();
    return result;
}
