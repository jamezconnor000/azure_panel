/**
 * @file diagnostic_logger.c
 * @brief Diagnostic Logging System Implementation
 */

#include "diagnostic_logger.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>
#include <sys/time.h>
#include <pthread.h>
#include <unistd.h>

// =============================================================================
// Configuration
// =============================================================================

static DiagnosticConfig_t g_config;
static FILE* g_log_file = NULL;
static pthread_mutex_t g_log_mutex = PTHREAD_MUTEX_INITIALIZER;
static bool g_initialized = false;

#define MAX_PERF_METRICS 1000
static PerformanceMetric_t g_perf_metrics[MAX_PERF_METRICS];
static uint32_t g_perf_count = 0;
static pthread_mutex_t g_perf_mutex = PTHREAD_MUTEX_INITIALIZER;

#define MAX_LOG_BUFFER 10000
static DiagnosticEntry_t g_log_buffer[MAX_LOG_BUFFER];
static uint32_t g_log_head = 0;
static uint32_t g_log_tail = 0;
static uint32_t g_log_count = 0;

// =============================================================================
// Helper Functions
// =============================================================================

static uint64_t get_timestamp_ms(void) {
    struct timeval tv;
    gettimeofday(&tv, NULL);
    return (uint64_t)tv.tv_sec * 1000 + tv.tv_usec / 1000;
}

static uint32_t get_thread_id(void) {
    return (uint32_t)pthread_self();
}

const char* Diagnostic_LevelToString(LogLevel_t level) {
    switch (level) {
        case LOG_LEVEL_TRACE: return "TRACE";
        case LOG_LEVEL_DEBUG: return "DEBUG";
        case LOG_LEVEL_INFO:  return "INFO ";
        case LOG_LEVEL_WARN:  return "WARN ";
        case LOG_LEVEL_ERROR: return "ERROR";
        case LOG_LEVEL_FATAL: return "FATAL";
        default: return "?????";
    }
}

const char* Diagnostic_CategoryToString(LogCategory_t category) {
    switch (category) {
        case LOG_CAT_SYSTEM:      return "SYSTEM";
        case LOG_CAT_DATABASE:    return "DATABASE";
        case LOG_CAT_READER:      return "READER";
        case LOG_CAT_OSDP:        return "OSDP";
        case LOG_CAT_ACCESS:      return "ACCESS";
        case LOG_CAT_EVENT:       return "EVENT";
        case LOG_CAT_NETWORK:     return "NETWORK";
        case LOG_CAT_RELAY:       return "RELAY";
        case LOG_CAT_CONFIG:      return "CONFIG";
        case LOG_CAT_PERFORMANCE: return "PERFORMANCE";
        default: return "UNKNOWN";
    }
}

static void rotate_log_if_needed(void) {
    if (!g_log_file || !g_config.rotate_logs) {
        return;
    }

    // Get current file size
    long pos = ftell(g_log_file);
    if (pos < 0 || pos < (g_config.max_log_size_mb * 1024 * 1024)) {
        return;
    }

    // Close current file
    fclose(g_log_file);
    g_log_file = NULL;

    // Rotate files
    char old_path[512], new_path[512];
    for (int i = g_config.max_log_files - 1; i > 0; i--) {
        snprintf(old_path, sizeof(old_path), "%s/%s.%d",
                 g_config.log_directory, g_config.log_filename, i - 1);
        snprintf(new_path, sizeof(new_path), "%s/%s.%d",
                 g_config.log_directory, g_config.log_filename, i);
        rename(old_path, new_path);
    }

    // Rename current to .0
    snprintf(old_path, sizeof(old_path), "%s/%s",
             g_config.log_directory, g_config.log_filename);
    snprintf(new_path, sizeof(new_path), "%s/%s.0",
             g_config.log_directory, g_config.log_filename);
    rename(old_path, new_path);

    // Open new file
    g_log_file = fopen(old_path, "a");
}

static void write_to_file(const DiagnosticEntry_t* entry) {
    if (!g_log_file) {
        return;
    }

    char timestamp[32];
    time_t sec = entry->timestamp_ms / 1000;
    uint32_t ms = entry->timestamp_ms % 1000;
    struct tm* tm_info = localtime(&sec);
    strftime(timestamp, sizeof(timestamp), "%Y-%m-%d %H:%M:%S", tm_info);
    snprintf(&timestamp[19], sizeof(timestamp) - 19, ".%03u", ms);

    if (g_config.include_source_info) {
        fprintf(g_log_file, "[%s] [%s] [%s] [%s:%u:%s] %s",
                timestamp,
                Diagnostic_LevelToString(entry->level),
                Diagnostic_CategoryToString(entry->category),
                entry->file,
                entry->line,
                entry->function,
                entry->message);
    } else {
        fprintf(g_log_file, "[%s] [%s] [%s] %s",
                timestamp,
                Diagnostic_LevelToString(entry->level),
                Diagnostic_CategoryToString(entry->category),
                entry->message);
    }

    if (entry->error_code != ErrorCode_OK) {
        fprintf(g_log_file, " (ErrorCode=%d)", entry->error_code);
    }

    fprintf(g_log_file, "\n");

    rotate_log_if_needed();
}

static void write_to_console(const DiagnosticEntry_t* entry) {
    const char* color = "";
    const char* reset = "\033[0m";

    switch (entry->level) {
        case LOG_LEVEL_TRACE: color = "\033[90m"; break; // Gray
        case LOG_LEVEL_DEBUG: color = "\033[36m"; break; // Cyan
        case LOG_LEVEL_INFO:  color = "\033[32m"; break; // Green
        case LOG_LEVEL_WARN:  color = "\033[33m"; break; // Yellow
        case LOG_LEVEL_ERROR: color = "\033[31m"; break; // Red
        case LOG_LEVEL_FATAL: color = "\033[35m"; break; // Magenta
    }

    printf("%s[%s] [%s]%s %s",
           color,
           Diagnostic_LevelToString(entry->level),
           Diagnostic_CategoryToString(entry->category),
           reset,
           entry->message);

    if (entry->error_code != ErrorCode_OK) {
        printf(" (ErrorCode=%d)", entry->error_code);
    }

    printf("\n");
}

static void add_to_buffer(const DiagnosticEntry_t* entry) {
    pthread_mutex_lock(&g_log_mutex);

    memcpy(&g_log_buffer[g_log_head], entry, sizeof(DiagnosticEntry_t));
    g_log_head = (g_log_head + 1) % MAX_LOG_BUFFER;

    if (g_log_count < MAX_LOG_BUFFER) {
        g_log_count++;
    } else {
        // Buffer full, overwrite oldest
        g_log_tail = (g_log_tail + 1) % MAX_LOG_BUFFER;
    }

    pthread_mutex_unlock(&g_log_mutex);
}

// =============================================================================
// Public API
// =============================================================================

ErrorCode_t Diagnostic_Init(const DiagnosticConfig_t* config) {
    if (!config) {
        return ErrorCode_BadParams;
    }

    pthread_mutex_lock(&g_log_mutex);

    memcpy(&g_config, config, sizeof(DiagnosticConfig_t));

    if (g_config.log_to_file) {
        char log_path[512];
        snprintf(log_path, sizeof(log_path), "%s/%s",
                 g_config.log_directory, g_config.log_filename);

        g_log_file = fopen(log_path, "a");
        if (!g_log_file) {
            pthread_mutex_unlock(&g_log_mutex);
            return ErrorCode_Failed;
        }

        // Write startup marker
        fprintf(g_log_file, "\n");
        fprintf(g_log_file, "================================================================================\n");
        fprintf(g_log_file, "HAL DIAGNOSTIC LOGGER STARTED\n");
        fprintf(g_log_file, "================================================================================\n");
        fflush(g_log_file);
    }

    g_initialized = true;
    pthread_mutex_unlock(&g_log_mutex);

    return ErrorCode_OK;
}

void Diagnostic_Shutdown(void) {
    pthread_mutex_lock(&g_log_mutex);

    if (g_log_file) {
        fprintf(g_log_file, "================================================================================\n");
        fprintf(g_log_file, "HAL DIAGNOSTIC LOGGER STOPPED\n");
        fprintf(g_log_file, "================================================================================\n");
        fclose(g_log_file);
        g_log_file = NULL;
    }

    g_initialized = false;
    pthread_mutex_unlock(&g_log_mutex);
}

void Diagnostic_Log(LogLevel_t level, LogCategory_t category,
                    const char* file, uint32_t line, const char* function,
                    const char* format, ...) {
    if (!g_initialized || level < g_config.min_level) {
        return;
    }

    DiagnosticEntry_t entry = {0};
    entry.timestamp_ms = get_timestamp_ms();
    entry.level = level;
    entry.category = category;
    entry.line = line;
    entry.error_code = ErrorCode_OK;
    entry.thread_id = get_thread_id();

    strncpy(entry.file, file, sizeof(entry.file) - 1);
    strncpy(entry.function, function, sizeof(entry.function) - 1);

    va_list args;
    va_start(args, format);
    vsnprintf(entry.message, sizeof(entry.message), format, args);
    va_end(args);

    add_to_buffer(&entry);

    pthread_mutex_lock(&g_log_mutex);
    if (g_config.log_to_file) {
        write_to_file(&entry);
    }
    if (g_config.log_to_console) {
        write_to_console(&entry);
    }
    pthread_mutex_unlock(&g_log_mutex);
}

void Diagnostic_LogError(LogLevel_t level, LogCategory_t category,
                         const char* file, uint32_t line, const char* function,
                         ErrorCode_t error_code, const char* format, ...) {
    if (!g_initialized || level < g_config.min_level) {
        return;
    }

    DiagnosticEntry_t entry = {0};
    entry.timestamp_ms = get_timestamp_ms();
    entry.level = level;
    entry.category = category;
    entry.line = line;
    entry.error_code = error_code;
    entry.thread_id = get_thread_id();

    strncpy(entry.file, file, sizeof(entry.file) - 1);
    strncpy(entry.function, function, sizeof(entry.function) - 1);

    va_list args;
    va_start(args, format);
    vsnprintf(entry.message, sizeof(entry.message), format, args);
    va_end(args);

    add_to_buffer(&entry);

    pthread_mutex_lock(&g_log_mutex);
    if (g_config.log_to_file) {
        write_to_file(&entry);
    }
    if (g_config.log_to_console) {
        write_to_console(&entry);
    }
    pthread_mutex_unlock(&g_log_mutex);
}

uint32_t Diagnostic_PerfStart(const char* operation) {
    pthread_mutex_lock(&g_perf_mutex);

    if (g_perf_count >= MAX_PERF_METRICS) {
        pthread_mutex_unlock(&g_perf_mutex);
        return 0;
    }

    uint32_t id = g_perf_count++;
    PerformanceMetric_t* metric = &g_perf_metrics[id];

    metric->start_time_ms = get_timestamp_ms();
    metric->end_time_ms = 0;
    metric->duration_ms = 0;
    metric->success = false;
    strncpy(metric->operation, operation, sizeof(metric->operation) - 1);

    pthread_mutex_unlock(&g_perf_mutex);
    return id;
}

void Diagnostic_PerfEnd(uint32_t metric_id, bool success) {
    pthread_mutex_lock(&g_perf_mutex);

    if (metric_id >= g_perf_count) {
        pthread_mutex_unlock(&g_perf_mutex);
        return;
    }

    PerformanceMetric_t* metric = &g_perf_metrics[metric_id];
    metric->end_time_ms = get_timestamp_ms();
    metric->duration_ms = metric->end_time_ms - metric->start_time_ms;
    metric->success = success;

    pthread_mutex_unlock(&g_perf_mutex);

    DIAG_DEBUG(LOG_CAT_PERFORMANCE, "Operation '%s' took %llu ms (success=%d)",
               metric->operation, metric->duration_ms, success);
}

void Diagnostic_Flush(void) {
    pthread_mutex_lock(&g_log_mutex);
    if (g_log_file) {
        fflush(g_log_file);
    }
    pthread_mutex_unlock(&g_log_mutex);
}

ErrorCode_t Diagnostic_ExportJSON(const char* output_path, uint64_t since_timestamp_ms) {
    if (!output_path) {
        return ErrorCode_BadParams;
    }

    FILE* fp = fopen(output_path, "w");
    if (!fp) {
        return ErrorCode_Failed;
    }

    pthread_mutex_lock(&g_log_mutex);

    fprintf(fp, "{\n");
    fprintf(fp, "  \"export_timestamp\": %llu,\n", get_timestamp_ms());
    fprintf(fp, "  \"log_entries\": [\n");

    uint32_t idx = g_log_tail;
    bool first = true;
    for (uint32_t i = 0; i < g_log_count; i++) {
        DiagnosticEntry_t* entry = &g_log_buffer[idx];

        if (entry->timestamp_ms >= since_timestamp_ms) {
            if (!first) {
                fprintf(fp, ",\n");
            }
            first = false;

            fprintf(fp, "    {\n");
            fprintf(fp, "      \"timestamp_ms\": %llu,\n", entry->timestamp_ms);
            fprintf(fp, "      \"level\": \"%s\",\n", Diagnostic_LevelToString(entry->level));
            fprintf(fp, "      \"category\": \"%s\",\n", Diagnostic_CategoryToString(entry->category));
            fprintf(fp, "      \"file\": \"%s\",\n", entry->file);
            fprintf(fp, "      \"line\": %u,\n", entry->line);
            fprintf(fp, "      \"function\": \"%s\",\n", entry->function);
            fprintf(fp, "      \"message\": \"%s\",\n", entry->message);
            fprintf(fp, "      \"error_code\": %d,\n", entry->error_code);
            fprintf(fp, "      \"thread_id\": %u\n", entry->thread_id);
            fprintf(fp, "    }");
        }

        idx = (idx + 1) % MAX_LOG_BUFFER;
    }

    fprintf(fp, "\n  ],\n");
    fprintf(fp, "  \"total_entries\": %u\n", g_log_count);
    fprintf(fp, "}\n");

    pthread_mutex_unlock(&g_log_mutex);

    fclose(fp);
    return ErrorCode_OK;
}

ErrorCode_t Diagnostic_GenerateReport(const char* output_path) {
    if (!output_path) {
        return ErrorCode_BadParams;
    }

    FILE* fp = fopen(output_path, "w");
    if (!fp) {
        return ErrorCode_Failed;
    }

    fprintf(fp, "╔══════════════════════════════════════════════════════════════════════════════╗\n");
    fprintf(fp, "║                                                                              ║\n");
    fprintf(fp, "║                   HAL DIAGNOSTIC REPORT                                      ║\n");
    fprintf(fp, "║                                                                              ║\n");
    fprintf(fp, "╚══════════════════════════════════════════════════════════════════════════════╝\n");
    fprintf(fp, "\n");

    time_t now = time(NULL);
    fprintf(fp, "Generated: %s\n", ctime(&now));
    fprintf(fp, "\n");

    // Summary
    fprintf(fp, "LOG SUMMARY\n");
    fprintf(fp, "────────────────────────────────────────────────────────────────────────────────\n");
    fprintf(fp, "Total Log Entries: %u\n", g_log_count);
    fprintf(fp, "\n");

    // Performance Summary
    pthread_mutex_lock(&g_perf_mutex);
    fprintf(fp, "PERFORMANCE METRICS\n");
    fprintf(fp, "────────────────────────────────────────────────────────────────────────────────\n");
    for (uint32_t i = 0; i < g_perf_count && i < 100; i++) {
        PerformanceMetric_t* m = &g_perf_metrics[i];
        fprintf(fp, "%s: %llu ms (success=%d)\n",
                m->operation, m->duration_ms, m->success);
    }
    pthread_mutex_unlock(&g_perf_mutex);

    fclose(fp);
    return ErrorCode_OK;
}

void Diagnostic_RecordHealth(const SystemHealth_t* health) {
    if (!health) {
        return;
    }

    DIAG_INFO(LOG_CAT_SYSTEM, "System Health: DB=%d API=%d Export=%d Readers=%u/%u Errors=%u",
              health->database_connected,
              health->api_server_running,
              health->event_export_running,
              health->readers_online,
              health->reader_count,
              health->errors_last_hour);
}

ErrorCode_t Diagnostic_GetHealth(SystemHealth_t* health) {
    if (!health) {
        return ErrorCode_BadParams;
    }

    // TODO: Implement actual health checking
    memset(health, 0, sizeof(SystemHealth_t));
    return ErrorCode_OK;
}
