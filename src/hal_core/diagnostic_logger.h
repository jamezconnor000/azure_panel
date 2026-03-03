/**
 * @file diagnostic_logger.h
 * @brief Diagnostic Logging System for Azure Panel Deployment
 *
 * Provides comprehensive logging, telemetry, and error reporting for
 * debugging HAL deployment issues on Azure Panel hardware.
 */

#ifndef DIAGNOSTIC_LOGGER_H
#define DIAGNOSTIC_LOGGER_H

#include "../../include/hal_types.h"
#include <stdint.h>
#include <stdbool.h>
#include <time.h>

// =============================================================================
// Log Levels
// =============================================================================

typedef enum {
    LOG_LEVEL_TRACE = 0,    // Extremely verbose (function entry/exit)
    LOG_LEVEL_DEBUG = 1,    // Debug information
    LOG_LEVEL_INFO = 2,     // Informational messages
    LOG_LEVEL_WARN = 3,     // Warnings
    LOG_LEVEL_ERROR = 4,    // Errors
    LOG_LEVEL_FATAL = 5     // Fatal errors (system crash)
} LogLevel_t;

// =============================================================================
// Log Categories
// =============================================================================

typedef enum {
    LOG_CAT_SYSTEM = 0,         // System initialization/shutdown
    LOG_CAT_DATABASE = 1,       // Database operations
    LOG_CAT_READER = 2,         // Reader communication
    LOG_CAT_OSDP = 3,           // OSDP protocol
    LOG_CAT_ACCESS = 4,         // Access control logic
    LOG_CAT_EVENT = 5,          // Event processing
    LOG_CAT_NETWORK = 6,        // Network/API
    LOG_CAT_RELAY = 7,          // Relay/output control
    LOG_CAT_CONFIG = 8,         // Configuration loading
    LOG_CAT_PERFORMANCE = 9     // Performance metrics
} LogCategory_t;

// =============================================================================
// Diagnostic Entry Structure
// =============================================================================

typedef struct {
    uint64_t timestamp_ms;      // Millisecond timestamp
    LogLevel_t level;           // Log level
    LogCategory_t category;     // Log category
    uint32_t line;              // Source line number
    char file[64];              // Source file name
    char function[64];          // Function name
    char message[256];          // Log message
    ErrorCode_t error_code;     // Associated error code (if any)
    uint32_t thread_id;         // Thread ID
    uint32_t context_id;        // Context ID (reader ID, etc.)
} DiagnosticEntry_t;

// =============================================================================
// Performance Metrics
// =============================================================================

typedef struct {
    uint64_t start_time_ms;
    uint64_t end_time_ms;
    uint64_t duration_ms;
    char operation[64];
    bool success;
} PerformanceMetric_t;

// =============================================================================
// System Health Status
// =============================================================================

typedef struct {
    bool database_connected;
    bool api_server_running;
    bool event_export_running;
    uint32_t reader_count;
    uint32_t readers_online;
    uint32_t readers_offline;
    uint32_t events_pending;
    uint32_t errors_last_hour;
    uint64_t uptime_seconds;
    float cpu_usage_percent;
    float memory_usage_mb;
} SystemHealth_t;

// =============================================================================
// Diagnostic Logger Configuration
// =============================================================================

typedef struct {
    LogLevel_t min_level;           // Minimum level to log
    bool log_to_file;               // Write to log file
    bool log_to_console;            // Write to console
    bool log_to_syslog;             // Write to syslog
    bool include_source_info;       // Include file/line/function
    bool include_timestamps;        // Include timestamps
    bool rotate_logs;               // Enable log rotation
    uint32_t max_log_size_mb;       // Max log file size
    uint32_t max_log_files;         // Max number of rotated logs
    char log_directory[256];        // Log directory path
    char log_filename[64];          // Log filename
} DiagnosticConfig_t;

// =============================================================================
// Diagnostic Logger API
// =============================================================================

/**
 * Initialize diagnostic logging system
 *
 * @param config Diagnostic configuration
 * @return ErrorCode_OK on success
 */
ErrorCode_t Diagnostic_Init(const DiagnosticConfig_t* config);

/**
 * Shutdown diagnostic logging system
 */
void Diagnostic_Shutdown(void);

/**
 * Log a diagnostic entry
 *
 * @param level Log level
 * @param category Log category
 * @param file Source file name
 * @param line Source line number
 * @param function Function name
 * @param format Printf-style format string
 * @param ... Variable arguments
 */
void Diagnostic_Log(LogLevel_t level, LogCategory_t category,
                    const char* file, uint32_t line, const char* function,
                    const char* format, ...);

/**
 * Log with associated error code
 */
void Diagnostic_LogError(LogLevel_t level, LogCategory_t category,
                         const char* file, uint32_t line, const char* function,
                         ErrorCode_t error_code, const char* format, ...);

/**
 * Start performance measurement
 *
 * @param operation Operation name
 * @return Metric ID for ending measurement
 */
uint32_t Diagnostic_PerfStart(const char* operation);

/**
 * End performance measurement
 *
 * @param metric_id Metric ID from PerfStart
 * @param success Whether operation succeeded
 */
void Diagnostic_PerfEnd(uint32_t metric_id, bool success);

/**
 * Record system health snapshot
 *
 * @param health Current system health
 */
void Diagnostic_RecordHealth(const SystemHealth_t* health);

/**
 * Get current system health
 *
 * @param health Output buffer for health status
 * @return ErrorCode_OK on success
 */
ErrorCode_t Diagnostic_GetHealth(SystemHealth_t* health);

/**
 * Flush all pending log entries to disk
 */
void Diagnostic_Flush(void);

/**
 * Generate diagnostic report
 *
 * @param output_path Path to write report
 * @return ErrorCode_OK on success
 */
ErrorCode_t Diagnostic_GenerateReport(const char* output_path);

/**
 * Export logs in JSON format for external analysis
 *
 * @param output_path Path to write JSON file
 * @param since_timestamp_ms Only export logs after this timestamp (0 = all)
 * @return ErrorCode_OK on success
 */
ErrorCode_t Diagnostic_ExportJSON(const char* output_path, uint64_t since_timestamp_ms);

// =============================================================================
// Convenience Macros
// =============================================================================

#define DIAG_TRACE(cat, fmt, ...) \
    Diagnostic_Log(LOG_LEVEL_TRACE, cat, __FILE__, __LINE__, __func__, fmt, ##__VA_ARGS__)

#define DIAG_DEBUG(cat, fmt, ...) \
    Diagnostic_Log(LOG_LEVEL_DEBUG, cat, __FILE__, __LINE__, __func__, fmt, ##__VA_ARGS__)

#define DIAG_INFO(cat, fmt, ...) \
    Diagnostic_Log(LOG_LEVEL_INFO, cat, __FILE__, __LINE__, __func__, fmt, ##__VA_ARGS__)

#define DIAG_WARN(cat, fmt, ...) \
    Diagnostic_Log(LOG_LEVEL_WARN, cat, __FILE__, __LINE__, __func__, fmt, ##__VA_ARGS__)

#define DIAG_ERROR(cat, fmt, ...) \
    Diagnostic_Log(LOG_LEVEL_ERROR, cat, __FILE__, __LINE__, __func__, fmt, ##__VA_ARGS__)

#define DIAG_FATAL(cat, fmt, ...) \
    Diagnostic_Log(LOG_LEVEL_FATAL, cat, __FILE__, __LINE__, __func__, fmt, ##__VA_ARGS__)

#define DIAG_ERROR_CODE(cat, err, fmt, ...) \
    Diagnostic_LogError(LOG_LEVEL_ERROR, cat, __FILE__, __LINE__, __func__, err, fmt, ##__VA_ARGS__)

#define DIAG_PERF_START(op) Diagnostic_PerfStart(op)
#define DIAG_PERF_END(id, success) Diagnostic_PerfEnd(id, success)

// =============================================================================
// Log Level Names
// =============================================================================

const char* Diagnostic_LevelToString(LogLevel_t level);
const char* Diagnostic_CategoryToString(LogCategory_t category);

#endif // DIAGNOSTIC_LOGGER_H
