#include "event_manager.h"
#include "../sdk_modules/events/access_event.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct EventSubscriber {
    char name[50];
    void (*handler)(AccessEvent_t*);
    struct EventSubscriber* next;
} EventSubscriber_t;

typedef struct {
    EventSubscriber_t* subscribers;
    AccessEvent_t** buffer;
    int buffer_size;
    int buffer_count;
} EventManager_t;

static EventManager_t* g_manager = NULL;

ErrorCode_t EventManager_Initialize(void) {
    if (g_manager) return ErrorCode_OK;
    
    g_manager = malloc(sizeof(EventManager_t));
    g_manager->subscribers = NULL;
    g_manager->buffer_size = 10000;
    g_manager->buffer = malloc(sizeof(AccessEvent_t*) * g_manager->buffer_size);
    g_manager->buffer_count = 0;
    
    printf("Event Manager initialized with %d event buffer\n", g_manager->buffer_size);
    return ErrorCode_OK;
}

void EventManager_Subscribe(const char* name, void (*handler)(AccessEvent_t*)) {
    EventSubscriber_t* sub = malloc(sizeof(EventSubscriber_t));
    strcpy(sub->name, name);
    sub->handler = handler;
    sub->next = g_manager->subscribers;
    g_manager->subscribers = sub;
    printf("Subscriber '%s' registered\n", name);
}

void EventManager_PublishEvent(AccessEvent_t* event) {
    if (!g_manager || !event) return;
    
    if (g_manager->buffer_count < g_manager->buffer_size) {
        g_manager->buffer[g_manager->buffer_count++] = event;
    }
    
    EventSubscriber_t* sub = g_manager->subscribers;
    while (sub) {
        if (sub->handler) {
            sub->handler(event);
        }
        sub = sub->next;
    }
}

void EventManager_Shutdown(void) {
    if (g_manager) {
        while (g_manager->subscribers) {
            EventSubscriber_t* next = g_manager->subscribers->next;
            free(g_manager->subscribers);
            g_manager->subscribers = next;
        }
        free(g_manager->buffer);
        free(g_manager);
        g_manager = NULL;
    }
}
