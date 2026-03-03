#include "event_exporter.h"
#include "../utils/cJSON.h"
#include "../../include/hal_public.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <curl/curl.h>

// Event batch for transmission
typedef struct {
    void** events;          // Array of event pointers
    int count;              // Current event count
    int capacity;           // Max capacity
} EventBatch_t;

// Event exporter instance
struct EventExporter_t {
    ExportConfig_t config;
    HAL_t* hal;
    EventBatch_t batch;
    ExportStats_t stats;
    bool running;
    uint32_t last_serial;
};

// HTTP response buffer
typedef struct {
    char* data;
    size_t size;
} HttpResponse_t;

// cURL write callback
static size_t WriteCallback(void* contents, size_t size, size_t nmemb, void* userp) {
    size_t realsize = size * nmemb;
    HttpResponse_t* mem = (HttpResponse_t*)userp;

    char* ptr = realloc(mem->data, mem->size + realsize + 1);
    if (!ptr) {
        printf("ERROR: Not enough memory for HTTP response\n");
        return 0;
    }

    mem->data = ptr;
    memcpy(&(mem->data[mem->size]), contents, realsize);
    mem->size += realsize;
    mem->data[mem->size] = 0;

    return realsize;
}

EventExporter_t* EventExporter_Create(const ExportConfig_t* config) {
    if (!config || !config->enabled) {
        printf("Event exporter disabled in configuration\n");
        return NULL;
    }

    EventExporter_t* exporter = (EventExporter_t*)malloc(sizeof(EventExporter_t));
    if (!exporter) return NULL;

    memset(exporter, 0, sizeof(EventExporter_t));
    memcpy(&exporter->config, config, sizeof(ExportConfig_t));

    // Initialize event batch
    exporter->batch.capacity = config->batch_size > 0 ? config->batch_size : 100;
    exporter->batch.events = (void**)calloc(exporter->batch.capacity, sizeof(void*));
    exporter->batch.count = 0;

    // Initialize cURL globally
    curl_global_init(CURL_GLOBAL_ALL);

    printf("Event Exporter created:\n");
    printf("  Server: %s%s\n", config->server_url, config->api_endpoint);
    printf("  Batch size: %d events\n", exporter->batch.capacity);
    printf("  Retry attempts: %d\n", config->retry_attempts);
    printf("  Timeout: %d seconds\n", config->timeout_seconds);

    return exporter;
}

void EventExporter_Destroy(EventExporter_t* exporter) {
    if (!exporter) return;

    EventExporter_Stop(exporter);

    if (exporter->batch.events) {
        // Free any pending events
        for (int i = 0; i < exporter->batch.count; i++) {
            free(exporter->batch.events[i]);
        }
        free(exporter->batch.events);
    }

    curl_global_cleanup();
    free(exporter);
}

ErrorCode_t EventExporter_Start(EventExporter_t* exporter, const char* hal_address, uint16_t hal_port) {
    if (!exporter) return ErrorCode_BadParams;

    // Create HAL instance
    HAL_RuntimeConfig_t hal_config = {
        .event_buffer_size = 100000,
        .max_events_before_ack = exporter->config.batch_size,
        .connection_timeout_ms = exporter->config.timeout_seconds * 1000,
        .log_level = 2
    };

    exporter->hal = HAL_Create(&hal_config);
    if (!exporter->hal) {
        printf("ERROR: Failed to create HAL instance\n");
        return ErrorCode_Failed;
    }

    // Connect to HAL controller
    ErrorCode_t result = HAL_Connect(exporter->hal, hal_address, hal_port);
    if (result != ErrorCode_OK) {
        printf("ERROR: Failed to connect to HAL at %s:%d (code: %d)\n",
               hal_address, hal_port, result);
        HAL_Destroy(exporter->hal);
        exporter->hal = NULL;
        return result;
    }

    // Subscribe to all events
    EventSubscription_t sub = {
        .max_events_before_ack = exporter->config.batch_size,
        .src_node = 1,
        .start_event_serial_number = 0
    };

    result = HAL_SubscribeToEvents(exporter->hal, &sub);
    if (result != ErrorCode_OK) {
        printf("ERROR: Failed to subscribe to events (code: %d)\n", result);
        HAL_Disconnect(exporter->hal);
        HAL_Destroy(exporter->hal);
        exporter->hal = NULL;
        return result;
    }

    exporter->running = true;
    exporter->last_serial = 0;

    printf("Event Exporter started - monitoring HAL events at %s:%d\n", hal_address, hal_port);
    return ErrorCode_OK;
}

void EventExporter_Stop(EventExporter_t* exporter) {
    if (!exporter || !exporter->running) return;

    exporter->running = false;

    if (exporter->hal) {
        HAL_UnsubscribeFromEvents(exporter->hal);
        HAL_Disconnect(exporter->hal);
        HAL_Destroy(exporter->hal);
        exporter->hal = NULL;
    }

    printf("Event Exporter stopped\n");
}

// Convert HAL event to JSON
static cJSON* EventToJSON(EventHeader_t* event) {
    cJSON* json = cJSON_CreateObject();

    cJSON_AddNumberToObject(json, "serial_number", event->serial_number);
    cJSON_AddNumberToObject(json, "timestamp", event->event_time);
    cJSON_AddNumberToObject(json, "node_id", event->node_id);
    cJSON_AddNumberToObject(json, "event_type", event->event_type);
    cJSON_AddNumberToObject(json, "event_subtype", event->event_subtype);

    // Add source LPA
    cJSON* source = cJSON_CreateObject();
    cJSON_AddNumberToObject(source, "type", event->source.type);
    cJSON_AddNumberToObject(source, "id", event->source.id);
    cJSON_AddNumberToObject(source, "node_id", event->source.node_id);
    cJSON_AddItemToObject(json, "source", source);

    // Add destination LPA
    cJSON* dest = cJSON_CreateObject();
    cJSON_AddNumberToObject(dest, "type", event->destination.type);
    cJSON_AddNumberToObject(dest, "id", event->destination.id);
    cJSON_AddNumberToObject(dest, "node_id", event->destination.node_id);
    cJSON_AddItemToObject(json, "destination", dest);

    return json;
}

// Send batch of events to external API
static ErrorCode_t SendBatch(EventExporter_t* exporter) {
    if (exporter->batch.count == 0) return ErrorCode_OK;

    // Build JSON array of events
    cJSON* root = cJSON_CreateObject();
    cJSON* events = cJSON_CreateArray();

    for (int i = 0; i < exporter->batch.count; i++) {
        EventHeader_t* event = (EventHeader_t*)exporter->batch.events[i];
        cJSON* event_json = EventToJSON(event);
        cJSON_AddItemToArray(events, event_json);
    }

    cJSON_AddItemToObject(root, "events", events);
    cJSON_AddNumberToObject(root, "count", exporter->batch.count);
    cJSON_AddNumberToObject(root, "source", 1); // Node ID

    char* json_string = cJSON_Print(root);

    printf("Sending batch of %d events to %s%s\n",
           exporter->batch.count,
           exporter->config.server_url,
           exporter->config.api_endpoint);

    // Prepare HTTP request
    CURL* curl = curl_easy_init();
    if (!curl) {
        cJSON_Delete(root);
        free(json_string);
        return ErrorCode_Failed;
    }

    // Build full URL
    char url[512];
    snprintf(url, sizeof(url), "%s%s",
             exporter->config.server_url,
             exporter->config.api_endpoint);

    HttpResponse_t response = {0};
    struct curl_slist* headers = NULL;

    // Set headers
    headers = curl_slist_append(headers, "Content-Type: application/json");

    char auth_header[384];
    snprintf(auth_header, sizeof(auth_header), "X-API-Key: %s", exporter->config.api_key);
    headers = curl_slist_append(headers, auth_header);

    // Configure cURL
    curl_easy_setopt(curl, CURLOPT_URL, url);
    curl_easy_setopt(curl, CURLOPT_POST, 1L);
    curl_easy_setopt(curl, CURLOPT_POSTFIELDS, json_string);
    curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
    curl_easy_setopt(curl, CURLOPT_TIMEOUT, exporter->config.timeout_seconds);
    curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, WriteCallback);
    curl_easy_setopt(curl, CURLOPT_WRITEDATA, (void*)&response);

    // Retry logic
    ErrorCode_t result = ErrorCode_Failed;
    int attempts = 0;

    while (attempts <= exporter->config.retry_attempts) {
        CURLcode res = curl_easy_perform(curl);

        if (res == CURLE_OK) {
            long http_code = 0;
            curl_easy_getinfo(curl, CURLINFO_RESPONSE_CODE, &http_code);

            if (http_code >= 200 && http_code < 300) {
                printf("  ✓ Batch sent successfully (HTTP %ld)\n", http_code);
                exporter->stats.events_sent += exporter->batch.count;
                exporter->stats.batches_sent++;
                result = ErrorCode_OK;
                break;
            } else {
                printf("  ✗ HTTP error %ld\n", http_code);
                snprintf(exporter->stats.last_error_msg, sizeof(exporter->stats.last_error_msg),
                        "HTTP %ld", http_code);
            }
        } else {
            printf("  ✗ Network error: %s\n", curl_easy_strerror(res));
            snprintf(exporter->stats.last_error_msg, sizeof(exporter->stats.last_error_msg),
                    "cURL error: %s", curl_easy_strerror(res));
        }

        attempts++;
        if (attempts <= exporter->config.retry_attempts) {
            printf("  Retrying... (attempt %d/%d)\n", attempts, exporter->config.retry_attempts);
            exporter->stats.retries_attempted++;
        }
    }

    // Cleanup
    if (response.data) free(response.data);
    curl_slist_free_all(headers);
    curl_easy_cleanup(curl);
    cJSON_Delete(root);
    free(json_string);

    if (result != ErrorCode_OK) {
        exporter->stats.events_failed += exporter->batch.count;
        exporter->stats.last_error_code = result;
    }

    // Clear batch
    for (int i = 0; i < exporter->batch.count; i++) {
        free(exporter->batch.events[i]);
    }
    exporter->batch.count = 0;

    return result;
}

int EventExporter_ProcessEvents(EventExporter_t* exporter) {
    if (!exporter || !exporter->running) return -1;

    // Check connection status
    if (!HAL_IsConnected(exporter->hal)) {
        printf("WARNING: Lost connection to HAL\n");
        return -1;
    }

    // Retrieve events from HAL
    HAL_Event_t event;
    int events_processed = 0;

    while (HAL_GetNextEvent(exporter->hal, &event) == ErrorCode_OK) {
        // Allocate and copy event for batch
        HAL_Event_t* event_copy = (HAL_Event_t*)malloc(sizeof(HAL_Event_t));
        if (!event_copy) {
            printf("ERROR: Failed to allocate event copy\n");
            break;
        }
        memcpy(event_copy, &event, sizeof(HAL_Event_t));

        // Add to batch
        if (exporter->batch.count < exporter->batch.capacity) {
            exporter->batch.events[exporter->batch.count++] = event_copy;
            events_processed++;
        } else {
            // Batch full - send it first
            ErrorCode_t result = SendBatch(exporter);
            if (result != ErrorCode_OK) {
                printf("ERROR: Failed to send batch\n");
                free(event_copy);
                return -1;
            }

            // Add event to new batch
            exporter->batch.events[exporter->batch.count++] = event_copy;
            events_processed++;
        }

        // Track last serial number
        exporter->last_serial = event.serial_number;
    }

    // If batch is full or has events and we've been idle, send it
    if (exporter->batch.count >= exporter->batch.capacity) {
        ErrorCode_t result = SendBatch(exporter);
        if (result != ErrorCode_OK) {
            printf("ERROR: Failed to send batch\n");
            return -1;
        }
    }

    return events_processed;
}

ErrorCode_t EventExporter_GetStats(EventExporter_t* exporter, ExportStats_t* stats) {
    if (!exporter || !stats) return ErrorCode_BadParams;
    memcpy(stats, &exporter->stats, sizeof(ExportStats_t));
    return ErrorCode_OK;
}

ErrorCode_t EventExporter_LoadConfig(const char* config_file, ExportConfig_t* out_config) {
    if (!config_file || !out_config) return ErrorCode_BadParams;

    FILE* f = fopen(config_file, "r");
    if (!f) {
        printf("ERROR: Cannot open config file: %s\n", config_file);
        return ErrorCode_ObjectNotFound;
    }

    fseek(f, 0, SEEK_END);
    long fsize = ftell(f);
    fseek(f, 0, SEEK_SET);

    char* json_str = (char*)malloc(fsize + 1);
    fread(json_str, 1, fsize, f);
    fclose(f);
    json_str[fsize] = 0;

    cJSON* root = cJSON_Parse(json_str);
    free(json_str);

    if (!root) {
        printf("ERROR: Invalid JSON in config file\n");
        return ErrorCode_Failed;
    }

    cJSON* ambient = cJSON_GetObjectItem(root, "ambient_ai");
    if (!ambient) {
        printf("ERROR: No 'ambient_ai' section in config\n");
        cJSON_Delete(root);
        return ErrorCode_ObjectNotFound;
    }

    memset(out_config, 0, sizeof(ExportConfig_t));

    cJSON* item;
    item = cJSON_GetObjectItem(ambient, "enabled");
    out_config->enabled = item ? cJSON_IsTrue(item) : false;

    item = cJSON_GetObjectItem(ambient, "server_url");
    if (item) strncpy(out_config->server_url, item->valuestring, sizeof(out_config->server_url) - 1);

    item = cJSON_GetObjectItem(ambient, "api_endpoint");
    if (item) strncpy(out_config->api_endpoint, item->valuestring, sizeof(out_config->api_endpoint) - 1);

    item = cJSON_GetObjectItem(ambient, "api_key");
    if (item) strncpy(out_config->api_key, item->valuestring, sizeof(out_config->api_key) - 1);

    item = cJSON_GetObjectItem(ambient, "timeout_seconds");
    out_config->timeout_seconds = item ? item->valueint : 5;

    item = cJSON_GetObjectItem(ambient, "retry_attempts");
    out_config->retry_attempts = item ? item->valueint : 3;

    item = cJSON_GetObjectItem(ambient, "batch_size");
    out_config->batch_size = item ? item->valueint : 100;

    cJSON_Delete(root);

    printf("Configuration loaded from %s\n", config_file);
    printf("  Export enabled: %s\n", out_config->enabled ? "YES" : "NO");

    return ErrorCode_OK;
}
