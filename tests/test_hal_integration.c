#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "../src/hal_core/access_logic.h"
#include "../src/hal_core/event_manager.h"
#include "../src/sdk_modules/events/access_event.h"

void ambient_handler(AccessEvent_t* event) {
    char* json = AccessEvent_ToJSON(event);
    printf("[TO AMBIENT.AI]: %s\n", json);
    free(json);
}

void audit_handler(AccessEvent_t* event) {
    printf("[AUDIT LOG]: Card %s - %s\n", 
           event->cardNumber,
           event->granted ? "GRANTED" : "DENIED");
}

int main() {
    printf("=== HAL INTEGRATION TEST ===\n\n");
    
    printf("Initializing HAL components...\n");
    AccessLogic_Initialize();
    EventManager_Initialize();
    
    printf("\nRegistering event handlers...\n");
    EventManager_Subscribe("Ambient.ai", ambient_handler);
    EventManager_Subscribe("Audit", audit_handler);
    
    printf("\n--- Test 1: Valid Card ---\n");
    AccessDecision_t decision1 = AccessLogic_ProcessCardRead(123456, 1);
    printf("Decision: %s - %s\n", 
           decision1.granted ? "GRANTED" : "DENIED",
           decision1.reason);
    
    AccessEvent_t* event1 = AccessEvent_Create(
        decision1.granted ? EVENT_ACCESS_GRANTED : EVENT_ACCESS_DENIED);
    strcpy(event1->cardNumber, "123456");
    event1->doorNumber = 1;
    strcpy(event1->doorName, "Main Entrance");
    event1->granted = decision1.granted;
    
    EventManager_PublishEvent(event1);
    
    printf("\n--- Test 2: Invalid Card ---\n");
    AccessDecision_t decision2 = AccessLogic_ProcessCardRead(999999, 1);
    printf("Decision: %s - %s\n",
           decision2.granted ? "GRANTED" : "DENIED", 
           decision2.reason);
    
    AccessEvent_t* event2 = AccessEvent_Create(EVENT_ACCESS_DENIED);
    strcpy(event2->cardNumber, "999999");
    event2->doorNumber = 1;
    strcpy(event2->doorName, "Main Entrance");
    event2->granted = false;
    
    EventManager_PublishEvent(event2);
    
    printf("\n=== TEST COMPLETE ===\n");
    printf("HAL is processing access decisions and sending events!\n");
    
    AccessEvent_Destroy(event1);
    AccessEvent_Destroy(event2);
    AccessLogic_Shutdown();
    EventManager_Shutdown();
    
    return 0;
}
