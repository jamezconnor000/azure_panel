#ifndef HAL_CORE_H
#define HAL_CORE_H
#include "../../include/hal_types.h"
#include <pthread.h>

// Event buffer for HAL instance
#define HAL_EVENT_BUFFER_SIZE 10000

typedef struct {
    HAL_Event_t events[HAL_EVENT_BUFFER_SIZE];
    uint32_t head;           // Next write position
    uint32_t tail;           // Next read position
    uint32_t count;          // Number of events in buffer
    pthread_mutex_t mutex;   // Thread safety
} HAL_EventBuffer_t;

typedef struct {
    void* event_manager;
    void* card_database;
    void* access_logic;
    HAL_RuntimeConfig_t config;
    HAL_EventBuffer_t event_buffer;
    uint8_t is_connected;
    char last_error[256];
} HAL_Instance_t;

// Internal event buffer functions
void HAL_EventBuffer_Init(HAL_EventBuffer_t* buffer);
void HAL_EventBuffer_Destroy(HAL_EventBuffer_t* buffer);
bool HAL_EventBuffer_Push(HAL_EventBuffer_t* buffer, const HAL_Event_t* event);
bool HAL_EventBuffer_Pop(HAL_EventBuffer_t* buffer, HAL_Event_t* event);
uint32_t HAL_EventBuffer_Count(HAL_EventBuffer_t* buffer);
void HAL_EventBuffer_Clear(HAL_EventBuffer_t* buffer);

#endif
