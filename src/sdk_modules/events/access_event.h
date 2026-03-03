#ifndef ACCESS_EVENT_H
#define ACCESS_EVENT_H

#include <stdint.h>
#include <time.h>
#include <stdbool.h>

typedef enum {
    EVENT_ACCESS_GRANTED,
    EVENT_ACCESS_DENIED,
    EVENT_DOOR_FORCED,
    EVENT_DOOR_HELD
} AccessEventType_t;

typedef struct {
    char eventId[40];
    AccessEventType_t type;
    time_t timestamp;
    char doorName[50];
    uint8_t doorNumber;
    char cardNumber[20];
    bool granted;
} AccessEvent_t;

AccessEvent_t* AccessEvent_Create(AccessEventType_t type);
void AccessEvent_Destroy(AccessEvent_t* event);
char* AccessEvent_ToJSON(AccessEvent_t* event);

#endif
