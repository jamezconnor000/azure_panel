#include "access_event.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

AccessEvent_t* AccessEvent_Create(AccessEventType_t type) {
    AccessEvent_t* event = malloc(sizeof(AccessEvent_t));
    if (!event) return NULL;
    
    memset(event, 0, sizeof(AccessEvent_t));
    sprintf(event->eventId, "evt-%ld", time(NULL));
    event->type = type;
    event->timestamp = time(NULL);
    event->granted = (type == EVENT_ACCESS_GRANTED);
    
    return event;
}

void AccessEvent_Destroy(AccessEvent_t* event) {
    if (event) free(event);
}

char* AccessEvent_ToJSON(AccessEvent_t* event) {
    if (!event) return NULL;
    
    char* json = malloc(1024);
    if (!json) return NULL;
    
    const char* typeStr = (event->type == EVENT_ACCESS_GRANTED) ? 
                          "access.granted" : "access.denied";
    
    sprintf(json, 
        "{ \"eventId\": \"%s\", \"eventType\": \"%s\", \"doorNumber\": %d, \"cardNumber\": \"%s\", \"granted\": %s }",
        event->eventId, typeStr, event->doorNumber, 
        event->cardNumber, event->granted ? "true" : "false"
    );
    
    return json;
}
