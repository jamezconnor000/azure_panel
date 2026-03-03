/**
 * @file hal_logs.c
 * @brief Log Viewer Tool
 *
 * Real-time log viewing and filtering for HAL system logs.
 *
 * @author FAM-HAL-v1.0-001
 * @date February 10, 2026
 */

#include <ctype.h>
#include <errno.h>
#include <getopt.h>
#include <signal.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <time.h>
#include <unistd.h>

/* ============================================================================
 * Constants
 * ========================================================================== */

#define DEFAULT_LOG_DIR         "/var/log/hal"
#define DEFAULT_HAL_LOG         "hal_engine.log"
#define DEFAULT_FORWARDER_LOG   "forwarder.log"
#define MAX_LINE_LEN            4096

static const char* VERSION = "1.0.0";
static const char* PROGRAM_NAME = "hal_logs";

/* ============================================================================
 * ANSI Colors
 * ========================================================================== */

#define COLOR_RESET     "\033[0m"
#define COLOR_RED       "\033[31m"
#define COLOR_GREEN     "\033[32m"
#define COLOR_YELLOW    "\033[33m"
#define COLOR_BLUE      "\033[34m"
#define COLOR_MAGENTA   "\033[35m"
#define COLOR_CYAN      "\033[36m"
#define COLOR_GRAY      "\033[90m"
#define COLOR_BOLD      "\033[1m"

/* ============================================================================
 * State
 * ========================================================================== */

static volatile sig_atomic_t g_running = 1;
static bool g_use_color = true;

/* ============================================================================
 * Functions
 * ========================================================================== */

static void signal_handler(int sig) {
    (void)sig;
    g_running = 0;
}

static void print_usage(void) {
    printf("Usage: %s [OPTIONS] [LOG_FILE]\n", PROGRAM_NAME);
    printf("\n");
    printf("Log Viewer - View and filter HAL system logs\n");
    printf("\n");
    printf("Options:\n");
    printf("  -f, --follow           Follow log (like tail -f)\n");
    printf("  -n, --lines N          Show last N lines (default: 20)\n");
    printf("  -l, --level LEVEL      Filter by level (debug, info, warn, error)\n");
    printf("  -g, --grep PATTERN     Filter lines containing pattern\n");
    printf("  -H, --hal              Show HAL Engine log (default)\n");
    printf("  -F, --forwarder        Show Forwarder log\n");
    printf("  -a, --all              Show all logs combined\n");
    printf("  -d, --dir PATH         Log directory (default: %s)\n", DEFAULT_LOG_DIR);
    printf("      --no-color         Disable colored output\n");
    printf("  -V, --version          Print version and exit\n");
    printf("  -h, --help             Print this help\n");
    printf("\n");
    printf("Log Levels:\n");
    printf("  debug    - Verbose debugging information\n");
    printf("  info     - General information\n");
    printf("  warn     - Warnings\n");
    printf("  error    - Errors\n");
    printf("\n");
    printf("Examples:\n");
    printf("  %s                     # Show last 20 lines of HAL log\n", PROGRAM_NAME);
    printf("  %s -f                  # Follow HAL log in real-time\n", PROGRAM_NAME);
    printf("  %s -f -l error         # Follow only error messages\n", PROGRAM_NAME);
    printf("  %s -F -n 50            # Last 50 lines of forwarder log\n", PROGRAM_NAME);
    printf("  %s -g \"ACCESS_GRANTED\" # Filter for access granted events\n", PROGRAM_NAME);
    printf("\n");
}

static void print_version(void) {
    printf("%s version %s\n", PROGRAM_NAME, VERSION);
    printf("HAL Azure Panel - Log Viewer\n");
}

typedef enum {
    LEVEL_UNKNOWN = 0,
    LEVEL_DEBUG,
    LEVEL_INFO,
    LEVEL_WARN,
    LEVEL_ERROR,
    LEVEL_FATAL
} log_level_t;

static log_level_t parse_level(const char* level_str) {
    if (!level_str) return LEVEL_UNKNOWN;

    if (strcasecmp(level_str, "debug") == 0) return LEVEL_DEBUG;
    if (strcasecmp(level_str, "info") == 0) return LEVEL_INFO;
    if (strcasecmp(level_str, "warn") == 0 || strcasecmp(level_str, "warning") == 0) return LEVEL_WARN;
    if (strcasecmp(level_str, "error") == 0) return LEVEL_ERROR;
    if (strcasecmp(level_str, "fatal") == 0) return LEVEL_FATAL;

    return LEVEL_UNKNOWN;
}

static log_level_t detect_line_level(const char* line) {
    /* Look for level indicators in the line */
    if (strstr(line, "[DEBUG]") || strstr(line, "[D]") || strstr(line, "DEBUG")) {
        return LEVEL_DEBUG;
    }
    if (strstr(line, "[INFO]") || strstr(line, "[I]") || strstr(line, "INFO")) {
        return LEVEL_INFO;
    }
    if (strstr(line, "[WARN]") || strstr(line, "[W]") || strstr(line, "WARN")) {
        return LEVEL_WARN;
    }
    if (strstr(line, "[ERROR]") || strstr(line, "[E]") || strstr(line, "ERROR")) {
        return LEVEL_ERROR;
    }
    if (strstr(line, "[FATAL]") || strstr(line, "[F]") || strstr(line, "FATAL")) {
        return LEVEL_FATAL;
    }
    return LEVEL_UNKNOWN;
}

static const char* get_level_color(log_level_t level) {
    if (!g_use_color) return "";

    switch (level) {
        case LEVEL_DEBUG:   return COLOR_GRAY;
        case LEVEL_INFO:    return COLOR_GREEN;
        case LEVEL_WARN:    return COLOR_YELLOW;
        case LEVEL_ERROR:   return COLOR_RED;
        case LEVEL_FATAL:   return COLOR_RED COLOR_BOLD;
        default:            return "";
    }
}

static bool matches_filter(const char* line, log_level_t min_level, const char* grep_pattern) {
    /* Check log level filter */
    if (min_level != LEVEL_UNKNOWN) {
        log_level_t line_level = detect_line_level(line);
        if (line_level < min_level && line_level != LEVEL_UNKNOWN) {
            return false;
        }
    }

    /* Check grep pattern */
    if (grep_pattern && strlen(grep_pattern) > 0) {
        if (strcasestr(line, grep_pattern) == NULL) {
            return false;
        }
    }

    return true;
}

static void print_line(const char* line, const char* prefix) {
    log_level_t level = detect_line_level(line);
    const char* color = get_level_color(level);
    const char* reset = g_use_color ? COLOR_RESET : "";

    if (prefix && strlen(prefix) > 0) {
        printf("%s[%s]%s %s%s%s",
               COLOR_CYAN, prefix, COLOR_RESET,
               color, line, reset);
    } else {
        printf("%s%s%s", color, line, reset);
    }

    /* Ensure newline */
    size_t len = strlen(line);
    if (len == 0 || line[len - 1] != '\n') {
        printf("\n");
    }
}

static int tail_file(const char* path, int num_lines, log_level_t min_level,
                     const char* grep_pattern, const char* prefix) {
    FILE* f = fopen(path, "r");
    if (!f) {
        fprintf(stderr, "Cannot open log file: %s\n", path);
        return -1;
    }

    /* Store last N matching lines */
    char** lines = calloc(num_lines, sizeof(char*));
    int line_count = 0;
    int line_index = 0;

    char buffer[MAX_LINE_LEN];
    while (fgets(buffer, sizeof(buffer), f)) {
        if (!matches_filter(buffer, min_level, grep_pattern)) {
            continue;
        }

        /* Free old line if we're wrapping around */
        if (lines[line_index]) {
            free(lines[line_index]);
        }

        lines[line_index] = strdup(buffer);
        line_index = (line_index + 1) % num_lines;
        if (line_count < num_lines) line_count++;
    }

    fclose(f);

    /* Print collected lines in order */
    int start = (line_count == num_lines) ? line_index : 0;
    for (int i = 0; i < line_count; i++) {
        int idx = (start + i) % num_lines;
        if (lines[idx]) {
            print_line(lines[idx], prefix);
            free(lines[idx]);
        }
    }

    free(lines);
    return 0;
}

static int follow_file(const char* path, log_level_t min_level,
                       const char* grep_pattern, const char* prefix) {
    FILE* f = fopen(path, "r");
    if (!f) {
        fprintf(stderr, "Cannot open log file: %s\n", path);
        return -1;
    }

    /* Seek to end */
    fseek(f, 0, SEEK_END);

    char buffer[MAX_LINE_LEN];
    while (g_running) {
        if (fgets(buffer, sizeof(buffer), f)) {
            if (matches_filter(buffer, min_level, grep_pattern)) {
                print_line(buffer, prefix);
                fflush(stdout);
            }
        } else {
            /* Check if file was rotated/truncated */
            struct stat st;
            if (fstat(fileno(f), &st) == 0) {
                long pos = ftell(f);
                if (st.st_size < pos) {
                    /* File was truncated, reopen */
                    fclose(f);
                    f = fopen(path, "r");
                    if (!f) break;
                    continue;
                }
            }

            /* No new data, sleep briefly */
            clearerr(f);
            usleep(100000);  /* 100ms */
        }
    }

    fclose(f);
    return 0;
}

/* ============================================================================
 * Main
 * ========================================================================== */

int main(int argc, char* argv[]) {
    static struct option long_options[] = {
        {"follow",     no_argument,       0, 'f'},
        {"lines",      required_argument, 0, 'n'},
        {"level",      required_argument, 0, 'l'},
        {"grep",       required_argument, 0, 'g'},
        {"hal",        no_argument,       0, 'H'},
        {"forwarder",  no_argument,       0, 'F'},
        {"all",        no_argument,       0, 'a'},
        {"dir",        required_argument, 0, 'd'},
        {"no-color",   no_argument,       0,  1 },
        {"version",    no_argument,       0, 'V'},
        {"help",       no_argument,       0, 'h'},
        {0, 0, 0, 0}
    };

    bool follow = false;
    int num_lines = 20;
    log_level_t min_level = LEVEL_UNKNOWN;
    const char* grep_pattern = NULL;
    const char* log_dir = DEFAULT_LOG_DIR;
    bool show_hal = true;
    bool show_forwarder = false;
    bool show_all = false;

    int opt;
    while ((opt = getopt_long(argc, argv, "fn:l:g:HFad:Vh", long_options, NULL)) != -1) {
        switch (opt) {
            case 'f':
                follow = true;
                break;
            case 'n':
                num_lines = atoi(optarg);
                break;
            case 'l':
                min_level = parse_level(optarg);
                if (min_level == LEVEL_UNKNOWN) {
                    fprintf(stderr, "Unknown level: %s\n", optarg);
                    return 1;
                }
                break;
            case 'g':
                grep_pattern = optarg;
                break;
            case 'H':
                show_hal = true;
                show_forwarder = false;
                break;
            case 'F':
                show_hal = false;
                show_forwarder = true;
                break;
            case 'a':
                show_all = true;
                show_hal = true;
                show_forwarder = true;
                break;
            case 'd':
                log_dir = optarg;
                break;
            case 1:  /* --no-color */
                g_use_color = false;
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

    /* Check for explicit log file argument */
    const char* explicit_file = NULL;
    if (optind < argc) {
        explicit_file = argv[optind];
    }

    /* Check if output is terminal */
    if (!isatty(STDOUT_FILENO)) {
        g_use_color = false;
    }

    /* Set up signal handlers */
    signal(SIGINT, signal_handler);
    signal(SIGTERM, signal_handler);

    /* Handle explicit file */
    if (explicit_file) {
        if (follow) {
            return follow_file(explicit_file, min_level, grep_pattern, NULL);
        } else {
            return tail_file(explicit_file, num_lines, min_level, grep_pattern, NULL);
        }
    }

    /* Build log paths */
    char hal_log[512];
    char forwarder_log[512];
    snprintf(hal_log, sizeof(hal_log), "%s/%s", log_dir, DEFAULT_HAL_LOG);
    snprintf(forwarder_log, sizeof(forwarder_log), "%s/%s", log_dir, DEFAULT_FORWARDER_LOG);

    /* Display logs */
    if (show_all || (show_hal && show_forwarder)) {
        /* Show both - can't follow both easily, show last N of each */
        printf("=== HAL Engine Log ===\n\n");
        tail_file(hal_log, num_lines, min_level, grep_pattern, "HAL");
        printf("\n=== Forwarder Log ===\n\n");
        tail_file(forwarder_log, num_lines, min_level, grep_pattern, "FWD");

        if (follow) {
            printf("\nNote: Can't follow multiple files. Following HAL log only...\n\n");
            follow_file(hal_log, min_level, grep_pattern, "HAL");
        }
    } else if (show_forwarder) {
        if (follow) {
            printf("Following %s (Ctrl+C to exit)...\n\n", forwarder_log);
            follow_file(forwarder_log, min_level, grep_pattern, NULL);
        } else {
            tail_file(forwarder_log, num_lines, min_level, grep_pattern, NULL);
        }
    } else {
        /* Default: HAL log */
        if (follow) {
            printf("Following %s (Ctrl+C to exit)...\n\n", hal_log);
            follow_file(hal_log, min_level, grep_pattern, NULL);
        } else {
            tail_file(hal_log, num_lines, min_level, grep_pattern, NULL);
        }
    }

    return 0;
}
