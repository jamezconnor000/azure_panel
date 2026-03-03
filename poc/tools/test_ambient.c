/**
 * @file test_ambient.c
 * @brief Ambient.ai API Test Tool
 *
 * Tests connectivity and API calls to Ambient.ai Generic Cloud Event API.
 * Sends test events directly without going through the HAL Engine.
 *
 * @author FAM-HAL-v1.0-001
 * @date February 10, 2026
 */

#include "event_types.h"
#include "json_serializer.h"
#include "uuid_utils.h"

#include <curl/curl.h>
#include <getopt.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <sys/time.h>

/* ============================================================================
 * Constants
 * ========================================================================== */

#define DEFAULT_ENDPOINT    "https://pacs-ingestion.ambient.ai/api/generic-cloud/event"
#define DEFAULT_TIMEOUT_MS  10000

static const char* VERSION = "1.0.0";
static const char* PROGRAM_NAME = "test_ambient";

/* ============================================================================
 * Response Buffer
 * ========================================================================== */

typedef struct {
    char* data;
    size_t size;
} response_buffer_t;

static size_t write_callback(void* contents, size_t size, size_t nmemb, void* userp) {
    size_t total = size * nmemb;
    response_buffer_t* buf = (response_buffer_t*)userp;

    char* new_data = realloc(buf->data, buf->size + total + 1);
    if (!new_data) {
        return 0;
    }

    buf->data = new_data;
    memcpy(&buf->data[buf->size], contents, total);
    buf->size += total;
    buf->data[buf->size] = '\0';

    return total;
}

/* ============================================================================
 * Functions
 * ========================================================================== */

static void print_usage(void) {
    printf("Usage: %s [OPTIONS] COMMAND\n", PROGRAM_NAME);
    printf("\n");
    printf("Ambient.ai API Test Tool\n");
    printf("\n");
    printf("Commands:\n");
    printf("  ping                   Test API connectivity\n");
    printf("  send                   Send a test event\n");
    printf("  validate               Validate API key\n");
    printf("\n");
    printf("Options:\n");
    printf("  -e, --endpoint URL     API endpoint (default: production)\n");
    printf("  -k, --api-key KEY      API key (required)\n");
    printf("  -t, --timeout MS       Request timeout (default: %d)\n", DEFAULT_TIMEOUT_MS);
    printf("  -s, --source-uid UUID  Source system UUID\n");
    printf("  -d, --device-uid UUID  Device UUID for test event\n");
    printf("  -a, --alarm-uid UUID   Alarm UUID for test event\n");
    printf("      --no-verify        Disable SSL verification\n");
    printf("  -v, --verbose          Verbose output (show JSON)\n");
    printf("  -V, --version          Print version and exit\n");
    printf("  -h, --help             Print this help\n");
    printf("\n");
    printf("Environment:\n");
    printf("  AMBIENT_API_KEY        API key (alternative to -k)\n");
    printf("  AMBIENT_ENDPOINT       API endpoint (alternative to -e)\n");
    printf("\n");
    printf("Examples:\n");
    printf("  %s -k YOUR_API_KEY ping\n", PROGRAM_NAME);
    printf("  %s -k YOUR_API_KEY send -v\n", PROGRAM_NAME);
    printf("  %s -k YOUR_API_KEY --no-verify ping  # Skip SSL check\n", PROGRAM_NAME);
    printf("\n");
}

static void print_version(void) {
    printf("%s version %s\n", PROGRAM_NAME, VERSION);
    printf("HAL Azure Panel - Ambient.ai Test Tool\n");
}

static int64_t get_timestamp_ms(void) {
    struct timeval tv;
    gettimeofday(&tv, NULL);
    return (int64_t)tv.tv_sec * 1000 + tv.tv_usec / 1000;
}

static char* create_test_event_json(const char* source_uid, const char* device_uid,
                                    const char* alarm_uid, bool verbose) {
    /* Generate UUIDs if not provided */
    char source_uuid[UUID_STRING_LEN] = {0};
    char device_uuid[UUID_STRING_LEN] = {0};
    char alarm_uuid[UUID_STRING_LEN] = {0};
    char event_uuid[UUID_STRING_LEN] = {0};

    if (source_uid && strlen(source_uid) > 0) {
        strncpy(source_uuid, source_uid, UUID_STRING_LEN - 1);
    } else {
        uuid_generate(source_uuid);
        if (verbose) printf("Generated source UUID: %s\n", source_uuid);
    }

    if (device_uid && strlen(device_uid) > 0) {
        strncpy(device_uuid, device_uid, UUID_STRING_LEN - 1);
    } else {
        uuid_generate(device_uuid);
        if (verbose) printf("Generated device UUID: %s\n", device_uuid);
    }

    if (alarm_uid && strlen(alarm_uid) > 0) {
        strncpy(alarm_uuid, alarm_uid, UUID_STRING_LEN - 1);
    } else {
        uuid_generate(alarm_uuid);
        if (verbose) printf("Generated alarm UUID: %s\n", alarm_uuid);
    }

    uuid_generate(event_uuid);
    if (verbose) printf("Generated event UUID: %s\n", event_uuid);

    int64_t now = get_timestamp_ms();

    /* Build JSON manually for test event */
    char* json = malloc(4096);
    if (!json) return NULL;

    snprintf(json, 4096,
        "{"
        "\"sourceSystemUid\":\"%s\","
        "\"occurredTimestamp\":%lld,"
        "\"publishedTimestamp\":%lld,"
        "\"eventUid\":\"%s\","
        "\"deviceUid\":\"%s\","
        "\"deviceName\":\"Test Reader 1\","
        "\"deviceType\":\"Door Reader\","
        "\"alarmUid\":\"%s\","
        "\"alarmName\":\"Access Granted\","
        "\"accessItemKey\":\"FC100-CN12345\","
        "\"accessResult\":\"granted\""
        "}",
        source_uuid,
        (long long)now,
        (long long)now,
        event_uuid,
        device_uuid,
        alarm_uuid);

    return json;
}

static int send_request(const char* endpoint, const char* api_key,
                        const char* json, int timeout_ms, bool verify_ssl,
                        bool verbose, bool is_post) {

    CURL* curl = curl_easy_init();
    if (!curl) {
        fprintf(stderr, "Failed to initialize CURL\n");
        return -1;
    }

    response_buffer_t response = {NULL, 0};

    /* Headers */
    struct curl_slist* headers = NULL;
    headers = curl_slist_append(headers, "Content-Type: application/json");

    char api_key_header[256];
    snprintf(api_key_header, sizeof(api_key_header), "x-api-key: %s", api_key);
    headers = curl_slist_append(headers, api_key_header);
    headers = curl_slist_append(headers, "User-Agent: HAL-TestTool/1.0");

    /* Configure request */
    curl_easy_setopt(curl, CURLOPT_URL, endpoint);
    curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
    curl_easy_setopt(curl, CURLOPT_TIMEOUT_MS, (long)timeout_ms);
    curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, write_callback);
    curl_easy_setopt(curl, CURLOPT_WRITEDATA, &response);

    if (!verify_ssl) {
        curl_easy_setopt(curl, CURLOPT_SSL_VERIFYPEER, 0L);
        curl_easy_setopt(curl, CURLOPT_SSL_VERIFYHOST, 0L);
        if (verbose) printf("SSL verification disabled\n");
    }

    if (is_post && json) {
        curl_easy_setopt(curl, CURLOPT_POSTFIELDS, json);
        if (verbose) {
            printf("\n=== Request Body ===\n%s\n====================\n\n", json);
        }
    } else {
        /* HEAD request for ping */
        curl_easy_setopt(curl, CURLOPT_NOBODY, 1L);
    }

    /* Perform request */
    int64_t start = get_timestamp_ms();
    CURLcode res = curl_easy_perform(curl);
    int64_t latency = get_timestamp_ms() - start;

    int result = -1;

    if (res == CURLE_OK) {
        long http_code = 0;
        curl_easy_getinfo(curl, CURLINFO_RESPONSE_CODE, &http_code);

        printf("HTTP Status: %ld\n", http_code);
        printf("Latency: %lld ms\n", (long long)latency);

        if (response.data && strlen(response.data) > 0) {
            printf("\n=== Response Body ===\n%s\n=====================\n", response.data);
        }

        if (http_code >= 200 && http_code < 300) {
            printf("\n✓ SUCCESS\n");
            result = 0;
        } else if (http_code == 401 || http_code == 403) {
            printf("\n✗ AUTHENTICATION FAILED - Check your API key\n");
        } else if (http_code == 404) {
            printf("\n✗ NOT FOUND - Check endpoint URL\n");
        } else {
            printf("\n✗ FAILED - HTTP %ld\n", http_code);
        }
    } else {
        fprintf(stderr, "\n✗ REQUEST FAILED: %s\n", curl_easy_strerror(res));

        if (res == CURLE_COULDNT_RESOLVE_HOST) {
            fprintf(stderr, "   Cannot resolve hostname - check network/DNS\n");
        } else if (res == CURLE_COULDNT_CONNECT) {
            fprintf(stderr, "   Connection refused - check endpoint URL\n");
        } else if (res == CURLE_SSL_CONNECT_ERROR) {
            fprintf(stderr, "   SSL error - try --no-verify for testing\n");
        } else if (res == CURLE_OPERATION_TIMEDOUT) {
            fprintf(stderr, "   Request timed out - try increasing timeout\n");
        }
    }

    /* Cleanup */
    curl_slist_free_all(headers);
    curl_easy_cleanup(curl);
    free(response.data);

    return result;
}

/* ============================================================================
 * Main
 * ========================================================================== */

int main(int argc, char* argv[]) {
    static struct option long_options[] = {
        {"endpoint",   required_argument, 0, 'e'},
        {"api-key",    required_argument, 0, 'k'},
        {"timeout",    required_argument, 0, 't'},
        {"source-uid", required_argument, 0, 's'},
        {"device-uid", required_argument, 0, 'd'},
        {"alarm-uid",  required_argument, 0, 'a'},
        {"no-verify",  no_argument,       0,  1 },
        {"verbose",    no_argument,       0, 'v'},
        {"version",    no_argument,       0, 'V'},
        {"help",       no_argument,       0, 'h'},
        {0, 0, 0, 0}
    };

    const char* endpoint = NULL;
    const char* api_key = NULL;
    const char* source_uid = NULL;
    const char* device_uid = NULL;
    const char* alarm_uid = NULL;
    int timeout_ms = DEFAULT_TIMEOUT_MS;
    bool verify_ssl = true;
    bool verbose = false;

    /* Check environment variables first */
    if (getenv("AMBIENT_ENDPOINT")) {
        endpoint = getenv("AMBIENT_ENDPOINT");
    }
    if (getenv("AMBIENT_API_KEY")) {
        api_key = getenv("AMBIENT_API_KEY");
    }

    int opt;
    while ((opt = getopt_long(argc, argv, "e:k:t:s:d:a:vVh", long_options, NULL)) != -1) {
        switch (opt) {
            case 'e':
                endpoint = optarg;
                break;
            case 'k':
                api_key = optarg;
                break;
            case 't':
                timeout_ms = atoi(optarg);
                break;
            case 's':
                source_uid = optarg;
                break;
            case 'd':
                device_uid = optarg;
                break;
            case 'a':
                alarm_uid = optarg;
                break;
            case 1:  /* --no-verify */
                verify_ssl = false;
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

    /* Use default endpoint if not specified */
    if (!endpoint) {
        endpoint = DEFAULT_ENDPOINT;
    }

    /* Check for API key */
    if (!api_key || strlen(api_key) == 0) {
        fprintf(stderr, "Error: API key is required\n");
        fprintf(stderr, "Use -k KEY or set AMBIENT_API_KEY environment variable\n\n");
        print_usage();
        return 1;
    }

    /* Get command */
    if (optind >= argc) {
        fprintf(stderr, "Error: Command required (ping, send, validate)\n\n");
        print_usage();
        return 1;
    }

    const char* command = argv[optind];

    /* Initialize CURL */
    curl_global_init(CURL_GLOBAL_DEFAULT);

    printf("\n=== Ambient.ai API Test ===\n");
    printf("Endpoint: %s\n", endpoint);
    printf("Timeout: %d ms\n", timeout_ms);
    printf("SSL Verify: %s\n", verify_ssl ? "yes" : "no");
    printf("===========================\n\n");

    int result = -1;

    if (strcmp(command, "ping") == 0) {
        printf("Testing connectivity...\n\n");
        result = send_request(endpoint, api_key, NULL, timeout_ms, verify_ssl, verbose, false);

    } else if (strcmp(command, "send") == 0) {
        printf("Sending test event...\n");

        char* json = create_test_event_json(source_uid, device_uid, alarm_uid, verbose);
        if (!json) {
            fprintf(stderr, "Failed to create test event\n");
            curl_global_cleanup();
            return 1;
        }

        result = send_request(endpoint, api_key, json, timeout_ms, verify_ssl, verbose, true);
        free(json);

    } else if (strcmp(command, "validate") == 0) {
        printf("Validating API key...\n\n");
        /* Same as ping - just checking auth */
        result = send_request(endpoint, api_key, NULL, timeout_ms, verify_ssl, verbose, false);

    } else {
        fprintf(stderr, "Unknown command: %s\n", command);
        print_usage();
        result = 1;
    }

    curl_global_cleanup();

    return result == 0 ? 0 : 1;
}
