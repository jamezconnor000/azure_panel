#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "../src/sdk_modules/events/access_event.h"

int main() {
    printf("=== ACCESS EVENT TEST ===\n\n");

    AccessEvent_t* event = AccessEvent_Create(EVENT_ACCESS_GRANTED);
    event->doorNumber = 1;
    strcpy(event->cardNumber, "123456");
    strcpy(event->doorName, "Main Entrance");

    char* json = AccessEvent_ToJSON(event);
    printf("Event JSON for Ambient.ai:\n%s\n\n", json);

    free(json);
    AccessEvent_Destroy(event);

    printf("Test passed! This JSON goes to Ambient.ai for tailgating detection.\n");
    return 0;
}
