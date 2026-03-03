/**
 * @file hal_engine.c
 * @brief HAL Access Engine main implementation
 *
 * @author FAM-HAL-v1.0-001
 * @date February 10, 2026
 */

#include "hal_engine.h"
#include "wiegand_handler.h"
#include "card_database.h"
#include "access_logic.h"
#include "event_producer.h"
#include "ipc_publisher.h"
#include "config.h"
#include "logger.h"
#include "uuid_utils.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <signal.h>
#include <time.h>
#include <sys/time.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <errno.h>
#include <pthread.h>

/* ============================================================================
 * Static State
 * ========================================================================== */

static hal_engine_config_t s_config;
static bool s_initialized = false;
static volatile bool s_running = false;
static int64_t s_start_time = 0;
static pthread_mutex_t s_mutex = PTHREAD_MUTEX_INITIALIZER;

/* Statistics */
static hal_engine_stats_t s_stats;

/* Simulation FIFO */
static int s_sim_fifo_fd = -1;

/* ============================================================================
 * Internal Functions
 * ========================================================================== */

static int64_t get_current_time(void) {
    struct timeval tv;
    gettimeofday(&tv, NULL);
    return tv.tv_sec;
}

static int create_simulation_fifo(void) {
    if (!s_config.simulation_enabled) {
        return 0;
    }

    /* Remove existing FIFO */
    unlink(s_config.sim_fifo_path);

    /* Create FIFO */
    if (mkfifo(s_config.sim_fifo_path, 0666) < 0) {
        LOG_ERROR("Failed to create simulation FIFO: %s", strerror(errno));
        return -1;
    }

    /* Open non-blocking for reading */
    s_sim_fifo_fd = open(s_config.sim_fifo_path, O_RDONLY | O_NONBLOCK);
    if (s_sim_fifo_fd < 0) {
        LOG_ERROR("Failed to open simulation FIFO: %s", strerror(errno));
        return -1;
    }

    LOG_INFO("Simulation FIFO created: %s", s_config.sim_fifo_path);
    return 0;
}

static void cleanup_simulation_fifo(void) {
    if (s_sim_fifo_fd >= 0) {
        close(s_sim_fifo_fd);
        s_sim_fifo_fd = -1;
    }
    unlink(s_config.sim_fifo_path);
}

static int check_simulation_input(uint32_t* facility_code, uint32_t* card_number) {
    if (!s_config.simulation_enabled || s_sim_fifo_fd < 0) {
        return 0;
    }

    char buf[64];
    ssize_t n = read(s_sim_fifo_fd, buf, sizeof(buf) - 1);
    if (n <= 0) {
        return 0;  /* No data available */
    }

    buf[n] = '\0';

    /* Parse "FC:CN" format */
    if (sscanf(buf, "%u:%u", facility_code, card_number) == 2) {
        LOG_DEBUG("Simulation input: FC=%u CN=%u", *facility_code, *card_number);
        return 1;
    }

    /* Parse just card number */
    if (sscanf(buf, "%u", card_number) == 1) {
        *facility_code = s_config.default_facility_code;
        LOG_DEBUG("Simulation input: CN=%u (default FC=%u)", *card_number, *facility_code);
        return 1;
    }

    return 0;
}

/* ============================================================================
 * Public Functions
 * ========================================================================== */

int hal_engine_init(const hal_engine_config_t* config) {
    pthread_mutex_lock(&s_mutex);

    if (s_initialized) {
        pthread_mutex_unlock(&s_mutex);
        return 0;
    }

    if (!config) {
        pthread_mutex_unlock(&s_mutex);
        return -1;
    }

    memcpy(&s_config, config, sizeof(hal_engine_config_t));

    /* Initialize UUID generator */
    uuid_init();

    /* Initialize card database */
    if (card_db_init(s_config.db_path) != 0) {
        LOG_ERROR("Failed to initialize card database");
        pthread_mutex_unlock(&s_mutex);
        return -1;
    }

    /* Seed test data if empty */
    if (card_db_count() == 0) {
        LOG_INFO("Empty database, seeding test data");
        card_db_seed_test_data();
    }

    LOG_INFO("Card database: %d cards loaded", card_db_count());

    /* Initialize event producer */
    event_producer_config_t ep_config;
    strncpy(ep_config.device_uid, s_config.device_uid, UUID_STRING_LEN - 1);
    strncpy(ep_config.device_name, s_config.device_name, DEVICE_NAME_MAX_LEN - 1);
    ep_config.reader_port = s_config.reader_port;
    strncpy(ep_config.alarm_uid_granted, s_config.alarm_uid_granted, UUID_STRING_LEN - 1);
    strncpy(ep_config.alarm_uid_denied, s_config.alarm_uid_denied, UUID_STRING_LEN - 1);

    if (event_producer_init(&ep_config) != 0) {
        LOG_ERROR("Failed to initialize event producer");
        card_db_close();
        pthread_mutex_unlock(&s_mutex);
        return -1;
    }

    /* Initialize IPC publisher */
    if (ipc_publisher_init(s_config.socket_path) != 0) {
        LOG_ERROR("Failed to initialize IPC publisher");
        event_producer_shutdown();
        card_db_close();
        pthread_mutex_unlock(&s_mutex);
        return -1;
    }

    /* Create simulation FIFO */
    if (create_simulation_fifo() != 0) {
        LOG_WARN("Simulation FIFO not available");
    }

    /* Initialize statistics */
    memset(&s_stats, 0, sizeof(s_stats));
    s_start_time = get_current_time();

    s_initialized = true;
    LOG_INFO("HAL engine initialized");

    pthread_mutex_unlock(&s_mutex);
    return 0;
}

int hal_engine_run(void) {
    if (!s_initialized) {
        LOG_ERROR("HAL engine not initialized");
        return -1;
    }

    s_running = true;
    LOG_INFO("HAL engine started");

    while (s_running) {
        /* Accept pending IPC connections */
        ipc_publisher_accept();

        /* Check for simulated card reads */
        uint32_t fc, cn;
        if (check_simulation_input(&fc, &cn)) {
            hal_engine_process_card(fc, cn);
        }

        /* Small sleep to avoid busy loop */
        usleep(10000);  /* 10ms */
    }

    LOG_INFO("HAL engine stopped");
    return 0;
}

void hal_engine_stop(void) {
    s_running = false;
}

void hal_engine_shutdown(void) {
    pthread_mutex_lock(&s_mutex);

    if (!s_initialized) {
        pthread_mutex_unlock(&s_mutex);
        return;
    }

    s_running = false;

    cleanup_simulation_fifo();
    ipc_publisher_shutdown();
    event_producer_shutdown();
    card_db_close();

    s_initialized = false;
    LOG_INFO("HAL engine shutdown complete");

    pthread_mutex_unlock(&s_mutex);
}

bool hal_engine_is_running(void) {
    return s_running;
}

int hal_engine_process_card(uint32_t facility_code, uint32_t card_number) {
    if (!s_initialized) {
        return -1;
    }

    LOG_INFO("Processing card: FC=%u CN=%u", facility_code, card_number);

    pthread_mutex_lock(&s_mutex);
    s_stats.cards_processed++;
    pthread_mutex_unlock(&s_mutex);

    /* Look up card in database */
    card_info_t card_info;
    access_decision_t decision;
    access_result_t result;

    int lookup_result = card_db_lookup(card_number, &card_info);

    if (lookup_result == 0) {
        /* Card found - check access */
        result = access_check(&card_info, time(NULL), &decision);
    } else if (lookup_result == 1) {
        /* Card not found */
        result = access_check_unknown(card_number, &decision);
    } else {
        /* Database error */
        LOG_ERROR("Database lookup failed");
        return -1;
    }

    /* Update statistics */
    pthread_mutex_lock(&s_mutex);
    if (result == ACCESS_RESULT_GRANTED) {
        s_stats.access_granted++;
    } else {
        s_stats.access_denied++;
    }
    s_stats.last_event_time = get_current_time();
    pthread_mutex_unlock(&s_mutex);

    /* Create and publish event */
    hal_event_t event;
    if (event_producer_create_access_event(
            lookup_result == 0 ? &card_info : NULL,
            &decision,
            facility_code,
            card_number,
            &event) == 0) {

        int subscribers = ipc_publisher_publish(&event);

        pthread_mutex_lock(&s_mutex);
        if (subscribers > 0) {
            s_stats.events_published++;
        } else {
            s_stats.events_failed++;
        }
        pthread_mutex_unlock(&s_mutex);

        LOG_INFO("Event published: %s -> %d subscribers",
                 result == ACCESS_RESULT_GRANTED ? "GRANTED" : "DENIED",
                 subscribers);
    }

    return 0;
}

int hal_engine_simulate_badge(uint32_t facility_code, uint32_t card_number) {
    return hal_engine_process_card(facility_code, card_number);
}

void hal_engine_get_stats(hal_engine_stats_t* stats) {
    if (!stats) return;

    pthread_mutex_lock(&s_mutex);
    memcpy(stats, &s_stats, sizeof(hal_engine_stats_t));
    stats->uptime_seconds = get_current_time() - s_start_time;
    pthread_mutex_unlock(&s_mutex);
}

void hal_engine_reset_stats(void) {
    pthread_mutex_lock(&s_mutex);
    memset(&s_stats, 0, sizeof(s_stats));
    s_start_time = get_current_time();
    pthread_mutex_unlock(&s_mutex);
}
