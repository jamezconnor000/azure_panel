/**
 * @file hal_status.c
 * @brief System Status Tool
 *
 * Displays the status of the HAL system components including
 * HAL Engine, Forwarder, and connectivity status.
 *
 * @author FAM-HAL-v1.0-001
 * @date February 10, 2026
 */

#include <dirent.h>
#include <errno.h>
#include <fcntl.h>
#include <getopt.h>
#include <signal.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <sys/un.h>
#include <time.h>
#include <unistd.h>

/* ============================================================================
 * Constants
 * ========================================================================== */

#define DEFAULT_IPC_SOCKET      "/tmp/hal_events.sock"
#define DEFAULT_WIEGAND_FIFO    "/tmp/hal_wiegand.fifo"
#define DEFAULT_HAL_PID         "/var/run/hal_engine.pid"
#define DEFAULT_FWD_PID         "/var/run/ambient_forwarder.pid"
#define DEFAULT_DATA_DIR        "./data"
#define DEFAULT_LOG_DIR         "./logs"

static const char* VERSION = "1.0.0";
static const char* PROGRAM_NAME = "hal_status";

/* ============================================================================
 * ANSI Colors
 * ========================================================================== */

#define COLOR_RESET     "\033[0m"
#define COLOR_RED       "\033[31m"
#define COLOR_GREEN     "\033[32m"
#define COLOR_YELLOW    "\033[33m"
#define COLOR_BLUE      "\033[34m"
#define COLOR_CYAN      "\033[36m"
#define COLOR_BOLD      "\033[1m"

static bool g_use_color = true;

#define OK()      (g_use_color ? COLOR_GREEN "✓" COLOR_RESET : "[OK]")
#define FAIL()    (g_use_color ? COLOR_RED "✗" COLOR_RESET : "[FAIL]")
#define WARN()    (g_use_color ? COLOR_YELLOW "!" COLOR_RESET : "[WARN]")
#define INFO()    (g_use_color ? COLOR_BLUE "•" COLOR_RESET : "[INFO]")

/* ============================================================================
 * Functions
 * ========================================================================== */

static void print_usage(void) {
    printf("Usage: %s [OPTIONS]\n", PROGRAM_NAME);
    printf("\n");
    printf("System Status - Display HAL system component status\n");
    printf("\n");
    printf("Options:\n");
    printf("  -w, --watch            Watch mode - refresh every 2 seconds\n");
    printf("  -j, --json             Output status as JSON\n");
    printf("  -q, --quiet            Quiet mode - exit code only\n");
    printf("      --ipc PATH         IPC socket path\n");
    printf("      --fifo PATH        Wiegand FIFO path\n");
    printf("      --no-color         Disable colored output\n");
    printf("  -V, --version          Print version and exit\n");
    printf("  -h, --help             Print this help\n");
    printf("\n");
    printf("Exit Codes:\n");
    printf("  0  - All components running\n");
    printf("  1  - Some components not running\n");
    printf("  2  - All components stopped\n");
    printf("\n");
}

static void print_version(void) {
    printf("%s version %s\n", PROGRAM_NAME, VERSION);
    printf("HAL Azure Panel - System Status\n");
}

static bool check_process_running(const char* name) {
    /* Simple check using pgrep */
    char cmd[256];
    snprintf(cmd, sizeof(cmd), "pgrep -x %s >/dev/null 2>&1", name);
    return system(cmd) == 0;
}

static pid_t get_pid_from_file(const char* pid_file) {
    FILE* f = fopen(pid_file, "r");
    if (!f) return 0;

    pid_t pid = 0;
    fscanf(f, "%d", &pid);
    fclose(f);

    /* Verify process is still running */
    if (pid > 0 && kill(pid, 0) != 0) {
        return 0;  /* Process not running */
    }

    return pid;
}

static bool check_socket_listening(const char* path) {
    struct stat st;
    if (stat(path, &st) != 0) {
        return false;
    }

    if (!S_ISSOCK(st.st_mode)) {
        return false;
    }

    /* Try to connect */
    int fd = socket(AF_UNIX, SOCK_STREAM, 0);
    if (fd < 0) return false;

    struct sockaddr_un addr;
    memset(&addr, 0, sizeof(addr));
    addr.sun_family = AF_UNIX;
    strncpy(addr.sun_path, path, sizeof(addr.sun_path) - 1);

    bool connected = (connect(fd, (struct sockaddr*)&addr, sizeof(addr)) == 0);
    close(fd);

    return connected;
}

static bool check_fifo_exists(const char* path) {
    struct stat st;
    if (stat(path, &st) != 0) {
        return false;
    }
    return S_ISFIFO(st.st_mode);
}

static long get_file_size(const char* path) {
    struct stat st;
    if (stat(path, &st) != 0) {
        return -1;
    }
    return st.st_size;
}

static int count_files_in_dir(const char* path, const char* extension) {
    DIR* dir = opendir(path);
    if (!dir) return -1;

    int count = 0;
    struct dirent* entry;
    while ((entry = readdir(dir)) != NULL) {
        if (extension) {
            size_t len = strlen(entry->d_name);
            size_t ext_len = strlen(extension);
            if (len > ext_len &&
                strcmp(entry->d_name + len - ext_len, extension) == 0) {
                count++;
            }
        } else {
            if (entry->d_name[0] != '.') {
                count++;
            }
        }
    }
    closedir(dir);
    return count;
}

static void print_header(void) {
    time_t now = time(NULL);
    char time_str[32];
    strftime(time_str, sizeof(time_str), "%Y-%m-%d %H:%M:%S", localtime(&now));

    printf("\n");
    if (g_use_color) {
        printf("%s╔══════════════════════════════════════════════════════════════╗%s\n", COLOR_CYAN, COLOR_RESET);
        printf("%s║%s            %sHAL Azure Panel - System Status%s            %s║%s\n",
               COLOR_CYAN, COLOR_RESET, COLOR_BOLD, COLOR_RESET, COLOR_CYAN, COLOR_RESET);
        printf("%s║%s                   %s                        %s║%s\n",
               COLOR_CYAN, COLOR_RESET, time_str, COLOR_CYAN, COLOR_RESET);
        printf("%s╚══════════════════════════════════════════════════════════════╝%s\n", COLOR_CYAN, COLOR_RESET);
    } else {
        printf("================================================================\n");
        printf("            HAL Azure Panel - System Status\n");
        printf("                   %s\n", time_str);
        printf("================================================================\n");
    }
    printf("\n");
}

typedef struct {
    bool hal_running;
    bool fwd_running;
    bool ipc_listening;
    bool fifo_exists;
    int db_count;
    int log_count;
    long card_db_size;
    long retry_db_size;
} status_t;

static void check_status(status_t* status, const char* ipc_path, const char* fifo_path) {
    memset(status, 0, sizeof(status_t));

    status->hal_running = check_process_running("hal_engine");
    status->fwd_running = check_process_running("ambient_forwarder");
    status->ipc_listening = check_socket_listening(ipc_path);
    status->fifo_exists = check_fifo_exists(fifo_path);

    status->db_count = count_files_in_dir(DEFAULT_DATA_DIR, ".db");
    status->log_count = count_files_in_dir(DEFAULT_LOG_DIR, ".log");

    char path[256];
    snprintf(path, sizeof(path), "%s/cards.db", DEFAULT_DATA_DIR);
    status->card_db_size = get_file_size(path);

    snprintf(path, sizeof(path), "%s/retry_queue.db", DEFAULT_DATA_DIR);
    status->retry_db_size = get_file_size(path);
}

static void print_status(const status_t* status, const char* ipc_path, const char* fifo_path) {
    print_header();

    printf("  %s Processes\n", INFO());
    printf("    %s HAL Engine:       %s\n",
           status->hal_running ? OK() : FAIL(),
           status->hal_running ? "Running" : "Stopped");
    printf("    %s Ambient Forwarder: %s\n",
           status->fwd_running ? OK() : FAIL(),
           status->fwd_running ? "Running" : "Stopped");
    printf("\n");

    printf("  %s IPC / Communication\n", INFO());
    printf("    %s Event Socket:     %s\n",
           status->ipc_listening ? OK() : FAIL(),
           status->ipc_listening ? "Listening" : "Not available");
    printf("      Path: %s\n", ipc_path);
    printf("    %s Wiegand FIFO:     %s\n",
           status->fifo_exists ? OK() : WARN(),
           status->fifo_exists ? "Available" : "Not created (simulation mode disabled)");
    printf("      Path: %s\n", fifo_path);
    printf("\n");

    printf("  %s Data Files\n", INFO());
    if (status->card_db_size >= 0) {
        printf("    %s Card Database:    %.1f KB\n", OK(), status->card_db_size / 1024.0);
    } else {
        printf("    %s Card Database:    Not found\n", WARN());
    }
    if (status->retry_db_size >= 0) {
        printf("    %s Retry Queue:      %.1f KB\n", OK(), status->retry_db_size / 1024.0);
    } else {
        printf("    %s Retry Queue:      Not found\n", INFO());
    }
    if (status->db_count >= 0) {
        printf("      Total DB files: %d\n", status->db_count);
    }
    printf("\n");

    printf("  %s Logs\n", INFO());
    if (status->log_count >= 0) {
        printf("    Log files: %d\n", status->log_count);
    } else {
        printf("    Log directory not found\n");
    }
    printf("\n");

    /* Overall status */
    if (g_use_color) {
        printf("  ═══════════════════════════════════════════════════════════\n");
    } else {
        printf("  -----------------------------------------------------------\n");
    }

    if (status->hal_running && status->fwd_running) {
        printf("  %s%s Overall: OPERATIONAL%s\n", COLOR_BOLD, COLOR_GREEN, COLOR_RESET);
    } else if (status->hal_running || status->fwd_running) {
        printf("  %s%s Overall: DEGRADED%s\n", COLOR_BOLD, COLOR_YELLOW, COLOR_RESET);
    } else {
        printf("  %s%s Overall: STOPPED%s\n", COLOR_BOLD, COLOR_RED, COLOR_RESET);
    }
    printf("\n");
}

static void print_status_json(const status_t* status) {
    printf("{\n");
    printf("  \"hal_engine\": {\n");
    printf("    \"running\": %s\n", status->hal_running ? "true" : "false");
    printf("  },\n");
    printf("  \"forwarder\": {\n");
    printf("    \"running\": %s\n", status->fwd_running ? "true" : "false");
    printf("  },\n");
    printf("  \"ipc\": {\n");
    printf("    \"listening\": %s\n", status->ipc_listening ? "true" : "false");
    printf("  },\n");
    printf("  \"simulation\": {\n");
    printf("    \"enabled\": %s\n", status->fifo_exists ? "true" : "false");
    printf("  },\n");
    printf("  \"databases\": {\n");
    printf("    \"card_db_bytes\": %ld,\n", status->card_db_size >= 0 ? status->card_db_size : 0);
    printf("    \"retry_db_bytes\": %ld\n", status->retry_db_size >= 0 ? status->retry_db_size : 0);
    printf("  },\n");
    printf("  \"overall\": \"%s\"\n",
           (status->hal_running && status->fwd_running) ? "operational" :
           (status->hal_running || status->fwd_running) ? "degraded" : "stopped");
    printf("}\n");
}

/* ============================================================================
 * Main
 * ========================================================================== */

int main(int argc, char* argv[]) {
    static struct option long_options[] = {
        {"watch",     no_argument,       0, 'w'},
        {"json",      no_argument,       0, 'j'},
        {"quiet",     no_argument,       0, 'q'},
        {"ipc",       required_argument, 0,  1 },
        {"fifo",      required_argument, 0,  2 },
        {"no-color",  no_argument,       0,  3 },
        {"version",   no_argument,       0, 'V'},
        {"help",      no_argument,       0, 'h'},
        {0, 0, 0, 0}
    };

    bool watch = false;
    bool json_output = false;
    bool quiet = false;
    const char* ipc_path = DEFAULT_IPC_SOCKET;
    const char* fifo_path = DEFAULT_WIEGAND_FIFO;

    int opt;
    while ((opt = getopt_long(argc, argv, "wjqVh", long_options, NULL)) != -1) {
        switch (opt) {
            case 'w':
                watch = true;
                break;
            case 'j':
                json_output = true;
                break;
            case 'q':
                quiet = true;
                break;
            case 1:  /* --ipc */
                ipc_path = optarg;
                break;
            case 2:  /* --fifo */
                fifo_path = optarg;
                break;
            case 3:  /* --no-color */
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

    /* Check if output is terminal */
    if (!isatty(STDOUT_FILENO)) {
        g_use_color = false;
    }

    if (json_output) {
        g_use_color = false;
    }

    status_t status;

    if (watch) {
        /* Watch mode */
        while (1) {
            /* Clear screen */
            printf("\033[2J\033[H");

            check_status(&status, ipc_path, fifo_path);

            if (json_output) {
                print_status_json(&status);
            } else {
                print_status(&status, ipc_path, fifo_path);
            }

            sleep(2);
        }
    } else {
        check_status(&status, ipc_path, fifo_path);

        if (quiet) {
            /* Exit code only */
        } else if (json_output) {
            print_status_json(&status);
        } else {
            print_status(&status, ipc_path, fifo_path);
        }
    }

    /* Return exit code */
    if (status.hal_running && status.fwd_running) {
        return 0;  /* All running */
    } else if (status.hal_running || status.fwd_running) {
        return 1;  /* Partial */
    } else {
        return 2;  /* All stopped */
    }
}
