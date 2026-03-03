/**
 * @file ambient_client.c
 * @brief Ambient.ai HTTP client implementation
 *
 * @author FAM-HAL-v1.0-001
 * @date February 10, 2026
 */

#include "ambient_client.h"
#include "json_serializer.h"
#include "logger.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <curl/curl.h>
#include <pthread.h>
#include <sys/time.h>

/* ============================================================================
 * Static State
 * ========================================================================== */

static ambient_client_config_t s_config;
static bool s_initialized = false;
static pthread_mutex_t s_mutex = PTHREAD_MUTEX_INITIALIZER;

/* Statistics */
static uint64_t s_requests_sent = 0;
static uint64_t s_requests_success = 0;
static uint64_t s_requests_failed = 0;
static int64_t s_total_latency_ms = 0;

/* ============================================================================
 * Internal Functions
 * ========================================================================== */

static int64_t get_time_ms(void) {
    struct timeval tv;
    gettimeofday(&tv, NULL);
    return (int64_t)tv.tv_sec * 1000 + tv.tv_usec / 1000;
}

/* Callback for curl response body (we discard it) */
static size_t write_callback(void* contents, size_t size, size_t nmemb, void* userp) {
    (void)contents;
    (void)userp;
    return size * nmemb;
}

/* ============================================================================
 * Public Functions
 * ========================================================================== */

int ambient_client_init(const ambient_client_config_t* config) {
    pthread_mutex_lock(&s_mutex);

    if (s_initialized) {
        pthread_mutex_unlock(&s_mutex);
        return 0;
    }

    if (!config) {
        pthread_mutex_unlock(&s_mutex);
        return -1;
    }

    memcpy(&s_config, config, sizeof(ambient_client_config_t));

    /* Initialize libcurl globally */
    if (curl_global_init(CURL_GLOBAL_DEFAULT) != CURLE_OK) {
        LOG_ERROR("Failed to initialize libcurl");
        pthread_mutex_unlock(&s_mutex);
        return -1;
    }

    s_requests_sent = 0;
    s_requests_success = 0;
    s_requests_failed = 0;
    s_total_latency_ms = 0;

    s_initialized = true;
    LOG_INFO("Ambient client initialized: %s", s_config.endpoint);

    pthread_mutex_unlock(&s_mutex);
    return 0;
}

void ambient_client_shutdown(void) {
    pthread_mutex_lock(&s_mutex);

    if (!s_initialized) {
        pthread_mutex_unlock(&s_mutex);
        return;
    }

    curl_global_cleanup();
    s_initialized = false;
    LOG_INFO("Ambient client shutdown");

    pthread_mutex_unlock(&s_mutex);
}

int ambient_client_send_json(const char* json, ambient_response_t* response) {
    if (!s_initialized || !json) {
        return -1;
    }

    int64_t start_time = get_time_ms();

    /* Initialize response */
    if (response) {
        memset(response, 0, sizeof(ambient_response_t));
    }

    CURL* curl = curl_easy_init();
    if (!curl) {
        LOG_ERROR("Failed to create curl handle");
        if (response) {
            strcpy(response->error_message, "Failed to create curl handle");
        }
        return -1;
    }

    /* Set headers */
    struct curl_slist* headers = NULL;
    headers = curl_slist_append(headers, "Content-Type: application/json");

    char api_key_header[256];
    snprintf(api_key_header, sizeof(api_key_header), "x-api-key: %s", s_config.api_key);
    headers = curl_slist_append(headers, api_key_header);

    char ua_header[128];
    snprintf(ua_header, sizeof(ua_header), "User-Agent: %s", s_config.user_agent);
    headers = curl_slist_append(headers, ua_header);

    /* Configure curl */
    curl_easy_setopt(curl, CURLOPT_URL, s_config.endpoint);
    curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
    curl_easy_setopt(curl, CURLOPT_POSTFIELDS, json);
    curl_easy_setopt(curl, CURLOPT_TIMEOUT_MS, (long)s_config.timeout_ms);
    curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, write_callback);

    if (!s_config.verify_ssl) {
        curl_easy_setopt(curl, CURLOPT_SSL_VERIFYPEER, 0L);
        curl_easy_setopt(curl, CURLOPT_SSL_VERIFYHOST, 0L);
    }

    /* Perform request */
    CURLcode res = curl_easy_perform(curl);

    int64_t latency_ms = get_time_ms() - start_time;

    pthread_mutex_lock(&s_mutex);
    s_requests_sent++;
    s_total_latency_ms += latency_ms;
    pthread_mutex_unlock(&s_mutex);

    int result = -1;

    if (res == CURLE_OK) {
        long http_code = 0;
        curl_easy_getinfo(curl, CURLINFO_RESPONSE_CODE, &http_code);

        if (response) {
            response->status_code = (int)http_code;
            response->latency_ms = latency_ms;
        }

        if (http_code >= 200 && http_code < 300) {
            pthread_mutex_lock(&s_mutex);
            s_requests_success++;
            pthread_mutex_unlock(&s_mutex);

            LOG_DEBUG("Ambient.ai POST success: HTTP %ld (%ldms)", http_code, latency_ms);
            result = 0;
        } else {
            pthread_mutex_lock(&s_mutex);
            s_requests_failed++;
            pthread_mutex_unlock(&s_mutex);

            LOG_WARN("Ambient.ai POST failed: HTTP %ld (%ldms)", http_code, latency_ms);

            if (response) {
                snprintf(response->error_message, sizeof(response->error_message),
                         "HTTP %ld", http_code);
            }
        }
    } else {
        pthread_mutex_lock(&s_mutex);
        s_requests_failed++;
        pthread_mutex_unlock(&s_mutex);

        const char* err_str = curl_easy_strerror(res);
        LOG_ERROR("Ambient.ai POST error: %s (%ldms)", err_str, latency_ms);

        if (response) {
            response->status_code = 0;
            response->latency_ms = latency_ms;
            strncpy(response->error_message, err_str, sizeof(response->error_message) - 1);
        }
    }

    curl_slist_free_all(headers);
    curl_easy_cleanup(curl);

    return result;
}

int ambient_client_send_event(const hal_event_t* event, ambient_response_t* response) {
    if (!s_initialized || !event) {
        return -1;
    }

    /* Serialize event to Ambient.ai JSON format */
    char* json = event_to_ambient_json(event, s_config.source_system_uid);
    if (!json) {
        LOG_ERROR("Failed to serialize event");
        return -1;
    }

    LOG_DEBUG("Sending to Ambient.ai: %s", json);

    int result = ambient_client_send_json(json, response);
    free(json);

    return result;
}

int ambient_client_test_connection(int64_t* latency_ms) {
    if (!s_initialized) {
        return -1;
    }

    int64_t start_time = get_time_ms();

    CURL* curl = curl_easy_init();
    if (!curl) {
        return -1;
    }

    /* Try a HEAD request to the endpoint */
    curl_easy_setopt(curl, CURLOPT_URL, s_config.endpoint);
    curl_easy_setopt(curl, CURLOPT_NOBODY, 1L);
    curl_easy_setopt(curl, CURLOPT_TIMEOUT_MS, 5000L);

    char api_key_header[256];
    snprintf(api_key_header, sizeof(api_key_header), "x-api-key: %s", s_config.api_key);
    struct curl_slist* headers = curl_slist_append(NULL, api_key_header);
    curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);

    if (!s_config.verify_ssl) {
        curl_easy_setopt(curl, CURLOPT_SSL_VERIFYPEER, 0L);
        curl_easy_setopt(curl, CURLOPT_SSL_VERIFYHOST, 0L);
    }

    CURLcode res = curl_easy_perform(curl);

    int64_t latency = get_time_ms() - start_time;
    if (latency_ms) {
        *latency_ms = latency;
    }

    curl_slist_free_all(headers);
    curl_easy_cleanup(curl);

    if (res == CURLE_OK) {
        LOG_DEBUG("Ambient.ai connectivity test: OK (%ldms)", latency);
        return 0;
    } else {
        LOG_WARN("Ambient.ai connectivity test: FAILED - %s", curl_easy_strerror(res));
        return -1;
    }
}

void ambient_client_get_stats(uint64_t* requests_sent, uint64_t* requests_success,
                              uint64_t* requests_failed, int64_t* avg_latency_ms) {
    pthread_mutex_lock(&s_mutex);

    if (requests_sent) *requests_sent = s_requests_sent;
    if (requests_success) *requests_success = s_requests_success;
    if (requests_failed) *requests_failed = s_requests_failed;

    if (avg_latency_ms) {
        if (s_requests_sent > 0) {
            *avg_latency_ms = s_total_latency_ms / (int64_t)s_requests_sent;
        } else {
            *avg_latency_ms = 0;
        }
    }

    pthread_mutex_unlock(&s_mutex);
}
