/**
 * @file logger.h
 * @brief Logging framework for Aether Access PoC
 *
 * Provides a simple but powerful logging system with:
 * - Multiple log levels (DEBUG, INFO, WARN, ERROR, FATAL)
 * - File and console output
 * - Timestamped messages
 * - Log rotation
 * - Thread-safe operation
 *
 * @author FAM-HAL-v1.0-001
 * @date February 10, 2026
 */

#ifndef POC_LOGGER_H
#define POC_LOGGER_H

#include <stdbool.h>
#include <stdarg.h>
#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/* ============================================================================
 * Log Levels
 * ========================================================================== */

typedef enum {
    LOG_LEVEL_DEBUG = 0,
    LOG_LEVEL_INFO  = 1,
    LOG_LEVEL_WARN  = 2,
    LOG_LEVEL_ERROR = 3,
    LOG_LEVEL_FATAL = 4,
    LOG_LEVEL_OFF   = 5
} log_level_t;

/* ============================================================================
 * Configuration
 * ========================================================================== */

/**
 * @brief Logger configuration structure
 */
typedef struct {
    log_level_t level;              /* Minimum log level */
    bool console_enabled;            /* Output to stdout/stderr */
    bool file_enabled;               /* Output to file */
    char log_file[256];              /* Log file path */
    size_t max_file_size_mb;         /* Max file size before rotation */
    int max_rotated_files;           /* Number of rotated files to keep */
    bool include_timestamp;          /* Include timestamp in messages */
    bool include_level;              /* Include level name in messages */
    bool include_source;             /* Include source file/line in messages */
    char app_name[64];               /* Application name prefix */
} logger_config_t;

/* ============================================================================
 * Initialization
 * ========================================================================== */

/**
 * @brief Initialize the logger with configuration
 *
 * @param config    Logger configuration
 * @return          0 on success, -1 on error
 */
int logger_init(const logger_config_t* config);

/**
 * @brief Initialize logger with default settings
 *
 * Defaults: DEBUG level, console only, no file
 *
 * @param app_name  Application name for log prefix
 * @return          0 on success, -1 on error
 */
int logger_init_default(const char* app_name);

/**
 * @brief Shutdown the logger
 *
 * Flushes pending messages and closes log file.
 */
void logger_shutdown(void);

/**
 * @brief Get default logger configuration
 *
 * @param config    Configuration structure to fill
 */
void logger_get_default_config(logger_config_t* config);

/* ============================================================================
 * Level Control
 * ========================================================================== */

/**
 * @brief Set the current log level
 *
 * @param level     New minimum log level
 */
void logger_set_level(log_level_t level);

/**
 * @brief Get the current log level
 *
 * @return          Current log level
 */
log_level_t logger_get_level(void);

/**
 * @brief Parse log level from string
 *
 * @param str       Level name ("DEBUG", "INFO", "WARN", "ERROR", "FATAL")
 * @return          Log level, or LOG_LEVEL_INFO if unknown
 */
log_level_t logger_parse_level(const char* str);

/**
 * @brief Get log level name
 *
 * @param level     Log level
 * @return          Level name string
 */
const char* logger_level_name(log_level_t level);

/* ============================================================================
 * Logging Functions
 * ========================================================================== */

/**
 * @brief Log a message with source information
 *
 * @param level     Log level
 * @param file      Source file name (__FILE__)
 * @param line      Source line number (__LINE__)
 * @param func      Function name (__func__)
 * @param fmt       Format string (printf-style)
 * @param ...       Format arguments
 */
void logger_log(log_level_t level, const char* file, int line,
                const char* func, const char* fmt, ...);

/**
 * @brief Log a message with source information (va_list version)
 */
void logger_logv(log_level_t level, const char* file, int line,
                 const char* func, const char* fmt, va_list args);

/* ============================================================================
 * Convenience Macros
 * ========================================================================== */

#define LOG_DEBUG(fmt, ...) \
    logger_log(LOG_LEVEL_DEBUG, __FILE__, __LINE__, __func__, fmt, ##__VA_ARGS__)

#define LOG_INFO(fmt, ...) \
    logger_log(LOG_LEVEL_INFO, __FILE__, __LINE__, __func__, fmt, ##__VA_ARGS__)

#define LOG_WARN(fmt, ...) \
    logger_log(LOG_LEVEL_WARN, __FILE__, __LINE__, __func__, fmt, ##__VA_ARGS__)

#define LOG_ERROR(fmt, ...) \
    logger_log(LOG_LEVEL_ERROR, __FILE__, __LINE__, __func__, fmt, ##__VA_ARGS__)

#define LOG_FATAL(fmt, ...) \
    logger_log(LOG_LEVEL_FATAL, __FILE__, __LINE__, __func__, fmt, ##__VA_ARGS__)

/* Conditional logging (only if condition is true) */
#define LOG_DEBUG_IF(cond, fmt, ...) \
    do { if (cond) LOG_DEBUG(fmt, ##__VA_ARGS__); } while(0)

#define LOG_INFO_IF(cond, fmt, ...) \
    do { if (cond) LOG_INFO(fmt, ##__VA_ARGS__); } while(0)

/* ============================================================================
 * Utility Functions
 * ========================================================================== */

/**
 * @brief Flush any buffered log messages
 */
void logger_flush(void);

/**
 * @brief Rotate log files manually
 *
 * @return          0 on success, -1 on error
 */
int logger_rotate(void);

/**
 * @brief Get statistics about logging
 *
 * @param messages_logged   Output: total messages logged
 * @param bytes_written     Output: total bytes written
 * @param rotations         Output: number of file rotations
 */
void logger_get_stats(uint64_t* messages_logged, uint64_t* bytes_written,
                      int* rotations);

/**
 * @brief Check if a log level is enabled
 *
 * Useful for avoiding expensive string formatting when logging is disabled.
 *
 * @param level     Level to check
 * @return          true if logging at this level is enabled
 */
bool logger_is_enabled(log_level_t level);

#ifdef __cplusplus
}
#endif

#endif /* POC_LOGGER_H */
