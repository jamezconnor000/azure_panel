#include "../../include/hal_public.h"
#include "hal.h"
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>

// =============================================================================
// Event Buffer Implementation
// =============================================================================

void HAL_EventBuffer_Init(HAL_EventBuffer_t* buffer) {
    if (!buffer) return;
    buffer->head = 0;
    buffer->tail = 0;
    buffer->count = 0;
    pthread_mutex_init(&buffer->mutex, NULL);
}

void HAL_EventBuffer_Destroy(HAL_EventBuffer_t* buffer) {
    if (!buffer) return;
    pthread_mutex_destroy(&buffer->mutex);
}

bool HAL_EventBuffer_Push(HAL_EventBuffer_t* buffer, const HAL_Event_t* event) {
    if (!buffer || !event) return false;

    pthread_mutex_lock(&buffer->mutex);

    if (buffer->count >= HAL_EVENT_BUFFER_SIZE) {
        // Buffer full - drop oldest event
        buffer->tail = (buffer->tail + 1) % HAL_EVENT_BUFFER_SIZE;
        buffer->count--;
    }

    memcpy(&buffer->events[buffer->head], event, sizeof(HAL_Event_t));
    buffer->head = (buffer->head + 1) % HAL_EVENT_BUFFER_SIZE;
    buffer->count++;

    pthread_mutex_unlock(&buffer->mutex);
    return true;
}

bool HAL_EventBuffer_Pop(HAL_EventBuffer_t* buffer, HAL_Event_t* event) {
    if (!buffer || !event) return false;

    pthread_mutex_lock(&buffer->mutex);

    if (buffer->count == 0) {
        pthread_mutex_unlock(&buffer->mutex);
        return false;
    }

    memcpy(event, &buffer->events[buffer->tail], sizeof(HAL_Event_t));
    buffer->tail = (buffer->tail + 1) % HAL_EVENT_BUFFER_SIZE;
    buffer->count--;

    pthread_mutex_unlock(&buffer->mutex);
    return true;
}

uint32_t HAL_EventBuffer_Count(HAL_EventBuffer_t* buffer) {
    if (!buffer) return 0;

    pthread_mutex_lock(&buffer->mutex);
    uint32_t count = buffer->count;
    pthread_mutex_unlock(&buffer->mutex);

    return count;
}

void HAL_EventBuffer_Clear(HAL_EventBuffer_t* buffer) {
    if (!buffer) return;

    pthread_mutex_lock(&buffer->mutex);
    buffer->head = 0;
    buffer->tail = 0;
    buffer->count = 0;
    pthread_mutex_unlock(&buffer->mutex);
}

// =============================================================================
// HAL Core Functions
// =============================================================================

HAL_t* HAL_Create(const HAL_RuntimeConfig_t* config) {
    HAL_Instance_t* hal = (HAL_Instance_t*)malloc(sizeof(HAL_Instance_t));
    if (!hal) return NULL;

    memset(hal, 0, sizeof(HAL_Instance_t));
    memcpy(&hal->config, config, sizeof(HAL_RuntimeConfig_t));
    hal->is_connected = 0;

    // Initialize event buffer
    HAL_EventBuffer_Init(&hal->event_buffer);

    return (HAL_t*)hal;
}

void HAL_Destroy(HAL_t* hal) {
    if (!hal) return;
    HAL_Instance_t* h = (HAL_Instance_t*)hal;
    HAL_EventBuffer_Destroy(&h->event_buffer);
    free(hal);
}

ErrorCode_t HAL_Connect(HAL_t* hal, const char* addr, uint16_t port) {
    HAL_Instance_t* h = (HAL_Instance_t*)hal;
    h->is_connected = 1;
    return ErrorCode_OK;
}

ErrorCode_t HAL_Disconnect(HAL_t* hal) {
    HAL_Instance_t* h = (HAL_Instance_t*)hal;
    h->is_connected = 0;
    return ErrorCode_OK;
}

uint8_t HAL_IsConnected(HAL_t* hal) {
    return ((HAL_Instance_t*)hal)->is_connected;
}

ErrorCode_t HAL_SubscribeToEvents(HAL_t* hal, const EventSubscription_t* sub) { return ErrorCode_OK; }
ErrorCode_t HAL_UnsubscribeFromEvents(HAL_t* hal) { return ErrorCode_OK; }
ErrorCode_t HAL_SendEventAck(HAL_t* hal, const EventAck_t* ack) { return ErrorCode_OK; }

ErrorCode_t HAL_AddCard(HAL_t* hal, const Card_t* card) { return ErrorCode_OK; }
ErrorCode_t HAL_GetCard(HAL_t* hal, CardId_t id, Card_t* out) { return ErrorCode_OK; }
ErrorCode_t HAL_UpdateCard(HAL_t* hal, const Card_t* card) { return ErrorCode_OK; }
ErrorCode_t HAL_DeleteCard(HAL_t* hal, CardId_t id) { return ErrorCode_OK; }

ErrorCode_t HAL_DecideAccess(HAL_t* hal, CardId_t id, LPA_t reader, AccessResult_t* result) {
    result->decision = AccessDecision_Grant;
    result->strike_time_ms = 1000;
    return ErrorCode_OK;
}

ErrorCode_t HAL_EnergizeRelay(HAL_t* hal, uint32_t id, uint32_t duration) { return ErrorCode_OK; }

ErrorCode_t HAL_GetEventBufferStatus(HAL_t* hal, EventBufferStatus_t* status) {
    if (!hal || !status) return ErrorCode_BadParams;

    HAL_Instance_t* h = (HAL_Instance_t*)hal;
    memset(status, 0, sizeof(EventBufferStatus_t));

    status->total_capacity = HAL_EVENT_BUFFER_SIZE;
    status->events_pending = HAL_EventBuffer_Count(&h->event_buffer);
    status->events_available = status->total_capacity - status->events_pending;

    return ErrorCode_OK;
}

ErrorCode_t HAL_ClearEventBuffer(HAL_t* hal) {
    if (!hal) return ErrorCode_BadParams;

    HAL_Instance_t* h = (HAL_Instance_t*)hal;
    HAL_EventBuffer_Clear(&h->event_buffer);

    return ErrorCode_OK;
}

ErrorCode_t HAL_SetLogLevel(HAL_t* hal, uint8_t level) { return ErrorCode_OK; }

// =============================================================================
// Event Retrieval Functions
// =============================================================================

ErrorCode_t HAL_GetEvents(HAL_t* hal, HAL_Event_t* events, uint32_t max_events, uint32_t* actual_count) {
    if (!hal || !events || !actual_count) return ErrorCode_BadParams;

    HAL_Instance_t* h = (HAL_Instance_t*)hal;
    *actual_count = 0;

    for (uint32_t i = 0; i < max_events; i++) {
        if (!HAL_EventBuffer_Pop(&h->event_buffer, &events[i])) {
            break;  // No more events
        }
        (*actual_count)++;
    }

    return ErrorCode_OK;
}

ErrorCode_t HAL_GetNextEvent(HAL_t* hal, HAL_Event_t* event) {
    if (!hal || !event) return ErrorCode_BadParams;

    HAL_Instance_t* h = (HAL_Instance_t*)hal;

    if (HAL_EventBuffer_Pop(&h->event_buffer, event)) {
        return ErrorCode_OK;
    }

    return ErrorCode_ObjectNotFound;
}

uint32_t HAL_GetPendingEventCount(HAL_t* hal) {
    if (!hal) return 0;

    HAL_Instance_t* h = (HAL_Instance_t*)hal;
    return HAL_EventBuffer_Count(&h->event_buffer);
}

// =============================================================================
// Event Submission (for internal use)
// =============================================================================

ErrorCode_t HAL_SubmitEvent(HAL_t* hal, const HAL_Event_t* event) {
    if (!hal || !event) return ErrorCode_BadParams;

    HAL_Instance_t* h = (HAL_Instance_t*)hal;

    if (HAL_EventBuffer_Push(&h->event_buffer, event)) {
        return ErrorCode_OK;
    }

    return ErrorCode_Failed;
}
