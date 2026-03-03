#include "src/hal_core/event_exporter.h"
#include <stdio.h>

int main() {
    printf("\n");
    printf("╔══════════════════════════════════════════════════════════════╗\n");
    printf("║                                                              ║\n");
    printf("║     Event Export Configuration Test                         ║\n");
    printf("║                                                              ║\n");
    printf("╚══════════════════════════════════════════════════════════════╝\n");
    printf("\n");

    // Load configuration
    ExportConfig_t config;
    ErrorCode_t result = EventExporter_LoadConfig("config/hal_config.json", &config);

    if (result != ErrorCode_OK) {
        printf("✗ Failed to load configuration (error code: %d)\n", result);
        return 1;
    }

    printf("✓ Configuration loaded successfully\n\n");

    // Display configuration
    printf("Export Configuration:\n");
    printf("═══════════════════════════════════════════════════════════════\n");
    printf("  Enabled:          %s\n", config.enabled ? "YES" : "NO");
    printf("  Server URL:       %s\n", config.server_url);
    printf("  API Endpoint:     %s\n", config.api_endpoint);
    printf("  API Key:          %s\n", config.api_key[0] ? "***configured***" : "(not set)");
    printf("  Timeout:          %d seconds\n", config.timeout_seconds);
    printf("  Retry Attempts:   %d\n", config.retry_attempts);
    printf("  Batch Size:       %d events\n", config.batch_size);
    printf("═══════════════════════════════════════════════════════════════\n");
    printf("\n");

    if (!config.enabled) {
        printf("⚠ Export is currently DISABLED in configuration\n");
        printf("  To enable, set ambient_ai.enabled = true in config file\n");
        printf("\n");
    }

    // Test creating exporter instance
    if (config.enabled) {
        EventExporter_t* exporter = EventExporter_Create(&config);
        if (exporter) {
            printf("✓ Event exporter instance created successfully\n");
            EventExporter_Destroy(exporter);
        } else {
            printf("✗ Failed to create event exporter instance\n");
            return 1;
        }
    }

    printf("\n");
    printf("═══════════════════════════════════════════════════════════════\n");
    printf("  Configuration Test PASSED                                    \n");
    printf("═══════════════════════════════════════════════════════════════\n");
    printf("\n");

    return 0;
}
