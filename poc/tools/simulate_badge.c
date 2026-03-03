/**
 * @file simulate_badge.c
 * @brief Badge Read Simulator
 *
 * Simulates Wiegand 26-bit badge reads by writing to the HAL Engine's
 * simulation FIFO. Used for testing without physical hardware.
 *
 * @author FAM-HAL-v1.0-001
 * @date February 10, 2026
 */

#include <errno.h>
#include <fcntl.h>
#include <getopt.h>
#include <signal.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
#include <sys/stat.h>

/* ============================================================================
 * Constants
 * ========================================================================== */

#define DEFAULT_FIFO_PATH       "/tmp/hal_wiegand.fifo"
#define DEFAULT_READER_PORT     1

static const char* VERSION = "1.0.0";
static const char* PROGRAM_NAME = "simulate_badge";

/* ============================================================================
 * Test Cards
 * ========================================================================== */

typedef struct {
    const char* name;
    uint16_t facility;
    uint32_t card_number;
    const char* description;
} test_card_t;

static const test_card_t TEST_CARDS[] = {
    {"john",    100, 12345,  "John Smith - Full Access"},
    {"jane",    100, 12346,  "Jane Doe - Office Hours Only"},
    {"bob",     100, 67890,  "Bob Wilson - Limited Access"},
    {"admin",   100, 99999,  "Admin Badge - All Access"},
    {"invalid", 200, 11111,  "Unknown Card - Should Deny"},
    {"visitor", 100, 55555,  "Visitor Badge - Main Entry"},
    {NULL, 0, 0, NULL}
};

/* ============================================================================
 * Functions
 * ========================================================================== */

static void print_usage(void) {
    printf("Usage: %s [OPTIONS] [COMMAND]\n", PROGRAM_NAME);
    printf("\n");
    printf("Badge Read Simulator - Sends simulated badge reads to HAL Engine\n");
    printf("\n");
    printf("Commands:\n");
    printf("  swipe FACILITY CARD    Swipe a badge (e.g., swipe 100 12345)\n");
    printf("  test NAME              Swipe a test badge by name\n");
    printf("  list                   List available test cards\n");
    printf("  random                 Swipe a random test card\n");
    printf("  flood COUNT            Swipe COUNT random badges rapidly\n");
    printf("  interactive            Enter interactive mode\n");
    printf("\n");
    printf("Options:\n");
    printf("  -f, --fifo PATH        FIFO path (default: %s)\n", DEFAULT_FIFO_PATH);
    printf("  -p, --port PORT        Reader port number (default: %d)\n", DEFAULT_READER_PORT);
    printf("  -d, --delay MS         Delay between swipes in flood mode (default: 100)\n");
    printf("  -v, --verbose          Verbose output\n");
    printf("  -V, --version          Print version and exit\n");
    printf("  -h, --help             Print this help\n");
    printf("\n");
    printf("Examples:\n");
    printf("  %s swipe 100 12345     # Swipe facility 100, card 12345\n", PROGRAM_NAME);
    printf("  %s test john           # Swipe John's test badge\n", PROGRAM_NAME);
    printf("  %s random              # Swipe a random test card\n", PROGRAM_NAME);
    printf("  %s flood 100           # Rapid-fire 100 random swipes\n", PROGRAM_NAME);
    printf("\n");
}

static void print_version(void) {
    printf("%s version %s\n", PROGRAM_NAME, VERSION);
    printf("HAL Azure Panel - Badge Simulator\n");
}

static void list_test_cards(void) {
    printf("\nAvailable test cards:\n");
    printf("%-12s %-10s %-12s %s\n", "NAME", "FACILITY", "CARD#", "DESCRIPTION");
    printf("%-12s %-10s %-12s %s\n", "----", "--------", "-----", "-----------");

    for (int i = 0; TEST_CARDS[i].name != NULL; i++) {
        printf("%-12s %-10u %-12u %s\n",
               TEST_CARDS[i].name,
               TEST_CARDS[i].facility,
               TEST_CARDS[i].card_number,
               TEST_CARDS[i].description);
    }
    printf("\n");
}

static const test_card_t* find_test_card(const char* name) {
    for (int i = 0; TEST_CARDS[i].name != NULL; i++) {
        if (strcasecmp(TEST_CARDS[i].name, name) == 0) {
            return &TEST_CARDS[i];
        }
    }
    return NULL;
}

static const test_card_t* get_random_card(void) {
    int count = 0;
    while (TEST_CARDS[count].name != NULL) count++;
    return &TEST_CARDS[rand() % count];
}

static int send_swipe(const char* fifo_path, int port, uint16_t facility, uint32_t card, bool verbose) {
    /* Construct the simulated Wiegand data line */
    char buffer[64];
    snprintf(buffer, sizeof(buffer), "%d:%u:%u\n", port, facility, card);

    /* Open FIFO (non-blocking first to check if HAL Engine is listening) */
    int fd = open(fifo_path, O_WRONLY | O_NONBLOCK);
    if (fd < 0) {
        if (errno == ENXIO) {
            fprintf(stderr, "Error: HAL Engine not running (no reader on FIFO)\n");
            fprintf(stderr, "Hint: Start hal_engine first with --simulation\n");
        } else if (errno == ENOENT) {
            fprintf(stderr, "Error: FIFO does not exist: %s\n", fifo_path);
            fprintf(stderr, "Hint: Start hal_engine with --simulation to create it\n");
        } else {
            perror("Failed to open FIFO");
        }
        return -1;
    }

    /* Write the badge data */
    ssize_t written = write(fd, buffer, strlen(buffer));
    close(fd);

    if (written < 0) {
        perror("Failed to write to FIFO");
        return -1;
    }

    if (verbose) {
        printf("Swipe sent: Port %d, Facility %u, Card %u\n", port, facility, card);
    }

    return 0;
}

static void interactive_mode(const char* fifo_path, int port, bool verbose) {
    printf("\n");
    printf("=== Interactive Badge Simulator ===\n");
    printf("Commands:\n");
    printf("  FACILITY CARD   - Swipe a badge\n");
    printf("  test NAME       - Swipe a test badge\n");
    printf("  list            - List test cards\n");
    printf("  random          - Random test card\n");
    printf("  port N          - Change reader port\n");
    printf("  quit            - Exit\n");
    printf("===================================\n\n");

    char line[256];
    while (1) {
        printf("badge> ");
        fflush(stdout);

        if (!fgets(line, sizeof(line), stdin)) {
            break;
        }

        /* Trim newline */
        line[strcspn(line, "\n")] = '\0';

        /* Skip empty lines */
        if (strlen(line) == 0) continue;

        /* Parse command */
        char cmd[32];
        char arg[32];
        unsigned int num1, num2;

        if (strcmp(line, "quit") == 0 || strcmp(line, "exit") == 0) {
            break;
        } else if (strcmp(line, "list") == 0) {
            list_test_cards();
        } else if (strcmp(line, "random") == 0) {
            const test_card_t* card = get_random_card();
            printf("Random card: %s\n", card->name);
            send_swipe(fifo_path, port, card->facility, card->card_number, verbose);
        } else if (sscanf(line, "port %d", &num1) == 1) {
            port = (int)num1;
            printf("Port changed to %d\n", port);
        } else if (sscanf(line, "test %31s", arg) == 1) {
            const test_card_t* card = find_test_card(arg);
            if (card) {
                send_swipe(fifo_path, port, card->facility, card->card_number, verbose);
            } else {
                printf("Unknown test card: %s\n", arg);
            }
        } else if (sscanf(line, "%u %u", &num1, &num2) == 2) {
            send_swipe(fifo_path, port, (uint16_t)num1, num2, verbose);
        } else {
            printf("Unknown command: %s\n", line);
            printf("Try: FACILITY CARD, test NAME, list, random, quit\n");
        }
    }

    printf("Goodbye!\n");
}

/* ============================================================================
 * Main
 * ========================================================================== */

int main(int argc, char* argv[]) {
    static struct option long_options[] = {
        {"fifo",    required_argument, 0, 'f'},
        {"port",    required_argument, 0, 'p'},
        {"delay",   required_argument, 0, 'd'},
        {"verbose", no_argument,       0, 'v'},
        {"version", no_argument,       0, 'V'},
        {"help",    no_argument,       0, 'h'},
        {0, 0, 0, 0}
    };

    const char* fifo_path = DEFAULT_FIFO_PATH;
    int port = DEFAULT_READER_PORT;
    int delay_ms = 100;
    bool verbose = false;

    int opt;
    while ((opt = getopt_long(argc, argv, "f:p:d:vVh", long_options, NULL)) != -1) {
        switch (opt) {
            case 'f':
                fifo_path = optarg;
                break;
            case 'p':
                port = atoi(optarg);
                break;
            case 'd':
                delay_ms = atoi(optarg);
                break;
            case 'v':
                verbose = true;
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

    /* Seed random */
    srand((unsigned int)time(NULL));

    /* Get command */
    if (optind >= argc) {
        /* Default to interactive mode */
        interactive_mode(fifo_path, port, verbose);
        return 0;
    }

    const char* command = argv[optind];

    if (strcmp(command, "swipe") == 0) {
        if (optind + 2 >= argc) {
            fprintf(stderr, "Usage: swipe FACILITY CARD\n");
            return 1;
        }
        uint16_t facility = (uint16_t)atoi(argv[optind + 1]);
        uint32_t card = (uint32_t)atoi(argv[optind + 2]);
        return send_swipe(fifo_path, port, facility, card, true) == 0 ? 0 : 1;

    } else if (strcmp(command, "test") == 0) {
        if (optind + 1 >= argc) {
            fprintf(stderr, "Usage: test NAME\n");
            list_test_cards();
            return 1;
        }
        const test_card_t* card = find_test_card(argv[optind + 1]);
        if (!card) {
            fprintf(stderr, "Unknown test card: %s\n", argv[optind + 1]);
            list_test_cards();
            return 1;
        }
        printf("Swiping: %s (%s)\n", card->name, card->description);
        return send_swipe(fifo_path, port, card->facility, card->card_number, true) == 0 ? 0 : 1;

    } else if (strcmp(command, "list") == 0) {
        list_test_cards();
        return 0;

    } else if (strcmp(command, "random") == 0) {
        const test_card_t* card = get_random_card();
        printf("Random card: %s (%s)\n", card->name, card->description);
        return send_swipe(fifo_path, port, card->facility, card->card_number, true) == 0 ? 0 : 1;

    } else if (strcmp(command, "flood") == 0) {
        int count = 10;
        if (optind + 1 < argc) {
            count = atoi(argv[optind + 1]);
        }
        printf("Flooding %d random swipes (delay: %dms)...\n", count, delay_ms);

        int success = 0;
        for (int i = 0; i < count; i++) {
            const test_card_t* card = get_random_card();
            if (send_swipe(fifo_path, port, card->facility, card->card_number, verbose) == 0) {
                success++;
            }
            if (delay_ms > 0 && i < count - 1) {
                usleep(delay_ms * 1000);
            }
        }
        printf("Flood complete: %d/%d successful\n", success, count);
        return success == count ? 0 : 1;

    } else if (strcmp(command, "interactive") == 0) {
        interactive_mode(fifo_path, port, verbose);
        return 0;

    } else {
        fprintf(stderr, "Unknown command: %s\n", command);
        print_usage();
        return 1;
    }
}
