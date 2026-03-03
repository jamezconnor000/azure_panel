#include "src/hal_core/event_exporter.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <signal.h>
#include <unistd.h>

static volatile bool g_running = true;

void signal_handler(int signum) {
    printf("\nReceived signal %d, shutting down...\n", signum);
    g_running = false;
}

void print_banner() {
    printf("\n");
    printf("╔══════════════════════════════════════════════════════════════╗\n");
    printf("║                                                              ║\n");
    printf("║         HAL EVENT EXPORT DAEMON                              ║\n");
    printf("║         Ambient.ai Integration                               ║\n");
    printf("║                                                              ║\n");
    printf("╚══════════════════════════════════════════════════════════════╝\n");
    printf("\n");
}

void print_usage(const char* program) {
    printf("Usage: %s [options]\n\n", program);
    printf("Options:\n");
    printf("  -c <config>   Path to config file (default: config/hal_config.json)\n");
    printf("  -h <host>     HAL controller host (default: localhost)\n");
    printf("  -p <port>     HAL controller port (default: 8080)\n");
    printf("  -i <seconds>  Poll interval in seconds (default: 1)\n");
    printf("  -d            Daemon mode (run in background)\n");
    printf("  --help        Show this help message\n");
    printf("\n");
    printf("Examples:\n");
    printf("  %s\n", program);
    printf("  %s -c /etc/hal/config.json -h 192.168.1.100 -p 8080\n", program);
    printf("  %s -i 5 -d\n", program);
    printf("\n");
}

void print_stats(const ExportStats_t* stats) {
    printf("\n");
    printf("═══════════════════════════════════════════════════════════════\n");
    printf("  EXPORT STATISTICS\n");
    printf("═══════════════════════════════════════════════════════════════\n");
    printf("  Events Received:     %llu\n", stats->events_received);
    printf("  Events Sent:         %llu\n", stats->events_sent);
    printf("  Events Failed:       %llu\n", stats->events_failed);
    printf("  Batches Sent:        %llu\n", stats->batches_sent);
    printf("  Retries Attempted:   %llu\n", stats->retries_attempted);
    if (stats->events_failed > 0) {
        printf("  Last Error Code:     %u\n", stats->last_error_code);
        printf("  Last Error Message:  %s\n", stats->last_error_msg);
    }
    printf("═══════════════════════════════════════════════════════════════\n");
    printf("\n");
}

int main(int argc, char* argv[]) {
    const char* config_file = "config/hal_config.json";
    const char* hal_host = "localhost";
    uint16_t hal_port = 8080;
    int poll_interval = 1;
    bool daemon_mode = false;

    // Parse command line arguments
    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "--help") == 0) {
            print_usage(argv[0]);
            return 0;
        } else if (strcmp(argv[i], "-c") == 0 && i + 1 < argc) {
            config_file = argv[++i];
        } else if (strcmp(argv[i], "-h") == 0 && i + 1 < argc) {
            hal_host = argv[++i];
        } else if (strcmp(argv[i], "-p") == 0 && i + 1 < argc) {
            hal_port = atoi(argv[++i]);
        } else if (strcmp(argv[i], "-i") == 0 && i + 1 < argc) {
            poll_interval = atoi(argv[++i]);
        } else if (strcmp(argv[i], "-d") == 0) {
            daemon_mode = true;
        } else {
            printf("Unknown option: %s\n", argv[i]);
            print_usage(argv[0]);
            return 1;
        }
    }

    print_banner();

    // Register signal handlers
    signal(SIGINT, signal_handler);
    signal(SIGTERM, signal_handler);

    // Load configuration
    ExportConfig_t config;
    ErrorCode_t result = EventExporter_LoadConfig(config_file, &config);
    if (result != ErrorCode_OK) {
        printf("ERROR: Failed to load configuration from %s\n", config_file);
        return 1;
    }

    if (!config.enabled) {
        printf("Event export is disabled in configuration. Exiting.\n");
        return 0;
    }

    // Create event exporter
    EventExporter_t* exporter = EventExporter_Create(&config);
    if (!exporter) {
        printf("ERROR: Failed to create event exporter\n");
        return 1;
    }

    // Start exporter (connect to HAL)
    printf("\nConnecting to HAL at %s:%d...\n", hal_host, hal_port);
    result = EventExporter_Start(exporter, hal_host, hal_port);
    if (result != ErrorCode_OK) {
        printf("ERROR: Failed to start event exporter (code: %d)\n", result);
        EventExporter_Destroy(exporter);
        return 1;
    }

    printf("\n");
    printf("═══════════════════════════════════════════════════════════════\n");
    printf("  Event Export Daemon Running                                  \n");
    printf("  Poll Interval: %d second%s                                   \n",
           poll_interval, poll_interval == 1 ? "" : "s");
    printf("  Press Ctrl+C to stop                                         \n");
    printf("═══════════════════════════════════════════════════════════════\n");
    printf("\n");

    // Main event loop
    int iterations = 0;
    int stats_interval = 60 / poll_interval; // Print stats every ~60 seconds

    while (g_running) {
        // Process events
        int events_processed = EventExporter_ProcessEvents(exporter);

        if (events_processed < 0) {
            printf("ERROR: Event processing failed, attempting to reconnect...\n");
            EventExporter_Stop(exporter);
            sleep(5);
            result = EventExporter_Start(exporter, hal_host, hal_port);
            if (result != ErrorCode_OK) {
                printf("ERROR: Reconnection failed\n");
                break;
            }
        }

        // Print stats periodically
        iterations++;
        if (iterations % stats_interval == 0) {
            ExportStats_t stats;
            EventExporter_GetStats(exporter, &stats);
            print_stats(&stats);
        }

        // Sleep for poll interval
        sleep(poll_interval);
    }

    // Shutdown
    printf("\nShutting down event exporter...\n");

    // Print final stats
    ExportStats_t final_stats;
    EventExporter_GetStats(exporter, &final_stats);
    print_stats(&final_stats);

    EventExporter_Destroy(exporter);

    printf("Event Export Daemon stopped.\n\n");

    return 0;
}
