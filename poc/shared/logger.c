/**
 * @file logger.c
 * @brief Logging framework implementation
 *
 * @author FAM-HAL-v1.0-001
 * @date February 10, 2026
 */

#include "logger.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <sys/time.h>
#include <pthread.h>
#include <unistd.h>
#include <sys/stat.h>

/* ============================================================================
 * Static State
 * ========================================================================== */

static logger_config_t s_config;
static FILE* s_log_file = NULL;
static pthread_mutex_t s_mutex = PTHREAD_MUTEX_INITIALIZER;
static bool s_initialized = false;
static uint64_t s_messages_logged = 0;
static uint64_t s_bytes_written = 0;
static int s_rotations = 0;

/* Log level names */
static const char* s_level_names[] = {
    "DEBUG",
    "INFO",
    "WARN",
    "ERROR",
    "FATAL",
    "OFF"
};

/* ANSI color codes for console output */
static const char* s_level_colors[] = {
    "\033[36m",     /* DEBUG - Cyan */
    "\033[32m",     /* INFO  - Green */
    "\033[33m",     /* WARN  - Yellow */
    "\033[31m",     /* ERROR - Red */
    "\033[35m",     /* FATAL - Magenta */
    ""              /* OFF   - No color */
};
static const char* s_color_reset = "\033[0m";

/* ============================================================================
 * Internal Functions
 * ========================================================================== */

static void get_timestamp(char* buf, size_t len) {
    struct timeval tv;
    gettimeofday(&tv, NULL);

    struct tm tm_info;
    localtime_r(&tv.tv_sec, &tm_info);

    int ms = tv.tv_usec / 1000;

    snprintf(buf, len, "%04d-%02d-%02d %02d:%02d:%02d.%03d",
             tm_info.tm_year + 1900,
             tm_info.tm_mon + 1,
             tm_info.tm_mday,
             tm_info.tm_hour,
             tm_info.tm_min,
             tm_info.tm_sec,
             ms);
}

static long get_file_size(const char* path) {
    struct stat st;
    if (stat(path, &st) == 0) {
        return st.st_size;
    }
    return 0;
}

static int do_rotate(void) {
    if (!s_config.file_enabled || s_config.log_file[0] == '\0') {
        return 0;
    }

    /* Close current file */
    if (s_log_file) {
        fclose(s_log_file);
        s_log_file = NULL;
    }

    /* Rotate existing files */
    char old_path[512];
    char new_path[512];

    /* Delete oldest file if exists */
    snprintf(old_path, sizeof(old_path), "%s.%d", s_config.log_file, s_config.max_rotated_files);
    unlink(old_path);

    /* Rename existing rotated files */
    for (int i = s_config.max_rotated_files - 1; i >= 1; i--) {
        snprintf(old_path, sizeof(old_path), "%s.%d", s_config.log_file, i);
        snprintf(new_path, sizeof(new_path), "%s.%d", s_config.log_file, i + 1);
        rename(old_path, new_path);
    }

    /* Rename current log to .1 */
    snprintf(new_path, sizeof(new_path), "%s.1", s_config.log_file);
    rename(s_config.log_file, new_path);

    /* Open new log file */
    s_log_file = fopen(s_config.log_file, "a");
    if (!s_log_file) {
        return -1;
    }

    s_rotations++;
    return 0;
}

static void check_rotation(void) {
    if (!s_config.file_enabled || s_config.max_file_size_mb == 0) {
        return;
    }

    long size = get_file_size(s_config.log_file);
    long max_bytes = (long)s_config.max_file_size_mb * 1024 * 1024;

    if (size >= max_bytes) {
        do_rotate();
    }
}

static const char* basename_only(const char* path) {
    const char* last_slash = strrchr(path, '/');
    return last_slash ? last_slash + 1 : path;
}

/* ============================================================================
 * Initialization
 * ========================================================================== */

void logger_get_default_config(logger_config_t* config) {
    if (!config) return;

    memset(config, 0, sizeof(logger_config_t));
    config->level = LOG_LEVEL_DEBUG;
    config->console_enabled = true;
    config->file_enabled = false;
    config->log_file[0] = '\0';
    config->max_file_size_mb = 10;
    config->max_rotated_files = 5;
    config->include_timestamp = true;
    config->include_level = true;
    config->include_source = true;
    strcpy(config->app_name, "app");
}

int logger_init(const logger_config_t* config) {
    pthread_mutex_lock(&s_mutex);

    if (s_initialized) {
        pthread_mutex_unlock(&s_mutex);
        return 0; /* Already initialized */
    }

    if (config) {
        memcpy(&s_config, config, sizeof(logger_config_t));
    } else {
        logger_get_default_config(&s_config);
    }

    /* Open log file if enabled */
    if (s_config.file_enabled && s_config.log_file[0] != '\0') {
        s_log_file = fopen(s_config.log_file, "a");
        if (!s_log_file) {
            fprintf(stderr, "Failed to open log file: %s\n", s_config.log_file);
            /* Continue without file logging */
            s_config.file_enabled = false;
        }
    }

    s_messages_logged = 0;
    s_bytes_written = 0;
    s_rotations = 0;
    s_initialized = true;

    pthread_mutex_unlock(&s_mutex);
    return 0;
}

int logger_init_default(const char* app_name) {
    logger_config_t config;
    logger_get_default_config(&config);

    if (app_name) {
        strncpy(config.app_name, app_name, sizeof(config.app_name) - 1);
        config.app_name[sizeof(config.app_name) - 1] = '\0';
    }

    return logger_init(&config);
}

void logger_shutdown(void) {
    pthread_mutex_lock(&s_mutex);

    if (s_log_file) {
        fflush(s_log_file);
        fclose(s_log_file);
        s_log_file = NULL;
    }

    s_initialized = false;
    pthread_mutex_unlock(&s_mutex);
}

/* ============================================================================
 * Level Control
 * ========================================================================== */

void logger_set_level(log_level_t level) {
    pthread_mutex_lock(&s_mutex);
    s_config.level = level;
    pthread_mutex_unlock(&s_mutex);
}

log_level_t logger_get_level(void) {
    return s_config.level;
}

log_level_t logger_parse_level(const char* str) {
    if (!str) return LOG_LEVEL_INFO;

    if (strcasecmp(str, "DEBUG") == 0) return LOG_LEVEL_DEBUG;
    if (strcasecmp(str, "INFO") == 0)  return LOG_LEVEL_INFO;
    if (strcasecmp(str, "WARN") == 0)  return LOG_LEVEL_WARN;
    if (strcasecmp(str, "WARNING") == 0) return LOG_LEVEL_WARN;
    if (strcasecmp(str, "ERROR") == 0) return LOG_LEVEL_ERROR;
    if (strcasecmp(str, "FATAL") == 0) return LOG_LEVEL_FATAL;
    if (strcasecmp(str, "OFF") == 0)   return LOG_LEVEL_OFF;

    return LOG_LEVEL_INFO;
}

const char* logger_level_name(log_level_t level) {
    if (level >= 0 && level < sizeof(s_level_names) / sizeof(s_level_names[0])) {
        return s_level_names[level];
    }
    return "UNKNOWN";
}

bool logger_is_enabled(log_level_t level) {
    return level >= s_config.level && s_initialized;
}

/* ============================================================================
 * Logging Functions
 * ========================================================================== */

void logger_logv(log_level_t level, const char* file, int line,
                 const char* func, const char* fmt, va_list args) {
    /* Check if logging is enabled for this level */
    if (!s_initialized || level < s_config.level) {
        return;
    }

    pthread_mutex_lock(&s_mutex);

    /* Build the log message */
    char timestamp[32] = {0};
    if (s_config.include_timestamp) {
        get_timestamp(timestamp, sizeof(timestamp));
    }

    /* Format the message */
    char message[1024];
    vsnprintf(message, sizeof(message), fmt, args);

    /* Build source info */
    char source[128] = {0};
    if (s_config.include_source && file) {
        snprintf(source, sizeof(source), " (%s:%d)", basename_only(file), line);
    }

    /* Calculate prefix */
    char prefix[256];
    if (s_config.include_timestamp && s_config.include_level) {
        snprintf(prefix, sizeof(prefix), "[%s] [%s] [%s]",
                 timestamp, s_config.app_name, s_level_names[level]);
    } else if (s_config.include_timestamp) {
        snprintf(prefix, sizeof(prefix), "[%s] [%s]",
                 timestamp, s_config.app_name);
    } else if (s_config.include_level) {
        snprintf(prefix, sizeof(prefix), "[%s] [%s]",
                 s_config.app_name, s_level_names[level]);
    } else {
        snprintf(prefix, sizeof(prefix), "[%s]", s_config.app_name);
    }

    /* Output to console */
    if (s_config.console_enabled) {
        FILE* out = (level >= LOG_LEVEL_ERROR) ? stderr : stdout;
        bool use_color = isatty(fileno(out));

        if (use_color) {
            fprintf(out, "%s%s%s %s%s\n",
                    s_level_colors[level], prefix, s_color_reset,
                    message, source);
        } else {
            fprintf(out, "%s %s%s\n", prefix, message, source);
        }
        fflush(out);
    }

    /* Output to file */
    if (s_config.file_enabled && s_log_file) {
        int bytes = fprintf(s_log_file, "%s %s%s\n", prefix, message, source);
        if (bytes > 0) {
            s_bytes_written += bytes;
        }
        fflush(s_log_file);
        check_rotation();
    }

    s_messages_logged++;
    pthread_mutex_unlock(&s_mutex);
}

void logger_log(log_level_t level, const char* file, int line,
                const char* func, const char* fmt, ...) {
    va_list args;
    va_start(args, fmt);
    logger_logv(level, file, line, func, fmt, args);
    va_end(args);
}

/* ============================================================================
 * Utility Functions
 * ========================================================================== */

void logger_flush(void) {
    pthread_mutex_lock(&s_mutex);

    if (s_log_file) {
        fflush(s_log_file);
    }
    fflush(stdout);
    fflush(stderr);

    pthread_mutex_unlock(&s_mutex);
}

int logger_rotate(void) {
    pthread_mutex_lock(&s_mutex);
    int result = do_rotate();
    pthread_mutex_unlock(&s_mutex);
    return result;
}

void logger_get_stats(uint64_t* messages_logged, uint64_t* bytes_written,
                      int* rotations) {
    pthread_mutex_lock(&s_mutex);

    if (messages_logged) *messages_logged = s_messages_logged;
    if (bytes_written) *bytes_written = s_bytes_written;
    if (rotations) *rotations = s_rotations;

    pthread_mutex_unlock(&s_mutex);
}
