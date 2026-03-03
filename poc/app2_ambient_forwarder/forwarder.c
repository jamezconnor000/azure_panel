/**
 * @file forwarder.c
 * @brief Event forwarder implementation
 *
 * @author FAM-HAL-v1.0-001
 * @date February 10, 2026
 */

#include "forwarder.h"
#include "ipc_subscriber.h"
#include "ambient_client.h"
#include "retry_queue.h"
#include "uuid_registry.h"
#include "logger.h"

#include <inttypes.h>
#include <pthread.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

/* ============================================================================
 * Static State
 * ========================================================================== */

static forwarder_config_t s_config;
static volatile bool s_running = false;
static volatile bool s_shutdown_requested = false;

static pthread_t s_event_thread;
static pthread_t s_retry_thread;
static pthread_mutex_t s_stats_mutex = PTHREAD_MUTEX_INITIALIZER;

/* Statistics */
static uint64_t s_events_received = 0;
static uint64_t s_events_forwarded = 0;
static uint64_t s_events_queued = 0;
static uint64_t s_events_dropped = 0;
static uint64_t s_retries_attempted = 0;
static uint64_t s_retries_success = 0;

/* ============================================================================
 * Internal Functions
 * ========================================================================== */

/**
 * @brief Process a single event - forward to Ambient.ai
 */
static int process_event(const hal_event_t* event) {
    ambient_response_t response;
    int result = ambient_client_send_event(event, &response);

    if (result == 0) {
        pthread_mutex_lock(&s_stats_mutex);
        s_events_forwarded++;
        pthread_mutex_unlock(&s_stats_mutex);

        LOG_DEBUG("Event forwarded: %s (HTTP %d, %ldms)",
                  event->event_uid, response.status_code, response.latency_ms);
        return 0;
    }

    /* Failed - queue for retry if enabled */
    if (s_config.retry_enabled && retry_queue_is_open()) {
        if (retry_queue_push(event) == 0) {
            pthread_mutex_lock(&s_stats_mutex);
            s_events_queued++;
            pthread_mutex_unlock(&s_stats_mutex);

            LOG_WARN("Event queued for retry: %s (%s)",
                     event->event_uid, response.error_message);
            return 0;
        }
    }

    pthread_mutex_lock(&s_stats_mutex);
    s_events_dropped++;
    pthread_mutex_unlock(&s_stats_mutex);

    LOG_ERROR("Event dropped: %s (%s)", event->event_uid, response.error_message);
    return -1;
}

/**
 * @brief Event callback from IPC subscriber
 */
static void event_callback(const hal_event_t* event) {
    if (!event) return;

    pthread_mutex_lock(&s_stats_mutex);
    s_events_received++;
    pthread_mutex_unlock(&s_stats_mutex);

    LOG_INFO("Event received: type=%d device=%s", event->event_type, event->device_name);

    process_event(event);
}

/**
 * @brief Event processing thread
 */
static void* event_thread_func(void* arg) {
    (void)arg;

    LOG_INFO("Event processing thread started");

    while (!s_shutdown_requested) {
        if (!ipc_subscriber_is_connected()) {
            LOG_INFO("Connecting to HAL Engine...");

            if (ipc_subscriber_connect(s_config.ipc_socket_path) == 0) {
                LOG_INFO("Connected to HAL Engine");
            } else {
                LOG_WARN("Connection failed, retrying in %d ms",
                         s_config.ipc_reconnect_delay_ms);
                usleep(s_config.ipc_reconnect_delay_ms * 1000);
                continue;
            }
        }

        /* Process events with timeout */
        ipc_subscriber_poll(100);
    }

    LOG_INFO("Event processing thread stopped");
    return NULL;
}

/**
 * @brief Retry processing thread
 */
static void* retry_thread_func(void* arg) {
    (void)arg;

    LOG_INFO("Retry processing thread started");

    while (!s_shutdown_requested) {
        /* Wait for retry interval */
        for (int i = 0; i < s_config.retry_interval_sec && !s_shutdown_requested; i++) {
            sleep(1);
        }

        if (s_shutdown_requested) break;

        /* Process retry queue */
        int processed = 0;
        int max_batch = 10;

        while (processed < max_batch && !s_shutdown_requested) {
            hal_event_t event;
            int64_t id;

            int result = retry_queue_peek(&event, &id);
            if (result == 1) {
                /* Queue empty */
                break;
            } else if (result != 0) {
                LOG_ERROR("Failed to peek retry queue");
                break;
            }

            pthread_mutex_lock(&s_stats_mutex);
            s_retries_attempted++;
            pthread_mutex_unlock(&s_stats_mutex);

            ambient_response_t response;
            if (ambient_client_send_event(&event, &response) == 0) {
                /* Success - remove from queue */
                retry_queue_remove(id);

                pthread_mutex_lock(&s_stats_mutex);
                s_retries_success++;
                s_events_forwarded++;
                pthread_mutex_unlock(&s_stats_mutex);

                LOG_INFO("Retry successful: %s", event.event_uid);
                processed++;
            } else {
                /* Still failing - leave in queue */
                LOG_WARN("Retry still failing: %s (%s)", event.event_uid, response.error_message);
                break;
            }
        }

        if (processed > 0) {
            LOG_INFO("Retry batch: %d events processed", processed);
        }
    }

    LOG_INFO("Retry processing thread stopped");
    return NULL;
}

/* ============================================================================
 * Public Functions
 * ========================================================================== */

int forwarder_init(const forwarder_config_t* config) {
    if (s_running) {
        LOG_WARN("Forwarder already running");
        return 0;
    }

    if (!config) {
        LOG_ERROR("Configuration is NULL");
        return -1;
    }

    memcpy(&s_config, config, sizeof(forwarder_config_t));

    /* Initialize UUID registry */
    if (uuid_registry_init(s_config.devices_config_path) != 0) {
        LOG_ERROR("Failed to initialize UUID registry");
        return -1;
    }

    /* Initialize Ambient client */
    ambient_client_config_t ambient_config;
    strncpy(ambient_config.endpoint, s_config.ambient_endpoint, sizeof(ambient_config.endpoint) - 1);
    strncpy(ambient_config.api_key, s_config.ambient_api_key, sizeof(ambient_config.api_key) - 1);
    ambient_config.timeout_ms = s_config.ambient_timeout_ms;
    strncpy(ambient_config.user_agent, s_config.user_agent, sizeof(ambient_config.user_agent) - 1);
    ambient_config.verify_ssl = s_config.ambient_verify_ssl;
    strncpy(ambient_config.source_system_uid, uuid_registry_get_source_system(),
            sizeof(ambient_config.source_system_uid) - 1);

    if (ambient_client_init(&ambient_config) != 0) {
        LOG_ERROR("Failed to initialize Ambient client");
        uuid_registry_shutdown();
        return -1;
    }

    /* Initialize retry queue if enabled */
    if (s_config.retry_enabled) {
        if (retry_queue_init(s_config.retry_db_path, s_config.retry_max_queue_size) != 0) {
            LOG_WARN("Failed to initialize retry queue, continuing without");
            s_config.retry_enabled = false;
        }
    }

    /* Initialize IPC subscriber */
    ipc_subscriber_init(event_callback);

    /* Reset statistics */
    pthread_mutex_lock(&s_stats_mutex);
    s_events_received = 0;
    s_events_forwarded = 0;
    s_events_queued = 0;
    s_events_dropped = 0;
    s_retries_attempted = 0;
    s_retries_success = 0;
    pthread_mutex_unlock(&s_stats_mutex);

    s_shutdown_requested = false;
    s_running = true;

    LOG_INFO("Forwarder initialized");
    return 0;
}

int forwarder_start(void) {
    if (!s_running) {
        LOG_ERROR("Forwarder not initialized");
        return -1;
    }

    /* Start event processing thread */
    if (pthread_create(&s_event_thread, NULL, event_thread_func, NULL) != 0) {
        LOG_ERROR("Failed to create event thread");
        return -1;
    }

    /* Start retry thread if enabled */
    if (s_config.retry_enabled) {
        if (pthread_create(&s_retry_thread, NULL, retry_thread_func, NULL) != 0) {
            LOG_ERROR("Failed to create retry thread");
            s_shutdown_requested = true;
            pthread_join(s_event_thread, NULL);
            return -1;
        }
    }

    LOG_INFO("Forwarder started");
    return 0;
}

void forwarder_stop(void) {
    if (!s_running) return;

    LOG_INFO("Stopping forwarder...");

    s_shutdown_requested = true;

    /* Wait for threads */
    pthread_join(s_event_thread, NULL);

    if (s_config.retry_enabled) {
        pthread_join(s_retry_thread, NULL);
    }

    LOG_INFO("Forwarder stopped");
}

void forwarder_shutdown(void) {
    forwarder_stop();

    if (!s_running) return;

    /* Cleanup */
    ipc_subscriber_disconnect();
    ipc_subscriber_shutdown();

    if (s_config.retry_enabled) {
        retry_queue_close();
    }

    ambient_client_shutdown();
    uuid_registry_shutdown();

    s_running = false;
    LOG_INFO("Forwarder shutdown complete");
}

bool forwarder_is_running(void) {
    return s_running && !s_shutdown_requested;
}

void forwarder_get_stats(forwarder_stats_t* stats) {
    if (!stats) return;

    pthread_mutex_lock(&s_stats_mutex);
    stats->events_received = s_events_received;
    stats->events_forwarded = s_events_forwarded;
    stats->events_queued = s_events_queued;
    stats->events_dropped = s_events_dropped;
    stats->retries_attempted = s_retries_attempted;
    stats->retries_success = s_retries_success;
    pthread_mutex_unlock(&s_stats_mutex);

    stats->queue_size = retry_queue_size();
    stats->connected = ipc_subscriber_is_connected();
}

void forwarder_print_stats(void) {
    forwarder_stats_t stats;
    forwarder_get_stats(&stats);

    printf("\n=== Forwarder Statistics ===\n");
    printf("Connected: %s\n", stats.connected ? "YES" : "NO");
    printf("Events:\n");
    printf("  Received:  %" PRIu64 "\n", stats.events_received);
    printf("  Forwarded: %" PRIu64 "\n", stats.events_forwarded);
    printf("  Queued:    %" PRIu64 "\n", stats.events_queued);
    printf("  Dropped:   %" PRIu64 "\n", stats.events_dropped);
    printf("Retries:\n");
    printf("  Attempted: %" PRIu64 "\n", stats.retries_attempted);
    printf("  Success:   %" PRIu64 "\n", stats.retries_success);
    printf("  Queue:     %d\n", stats.queue_size);
    printf("============================\n\n");
}
