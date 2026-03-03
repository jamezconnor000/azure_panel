#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "../src/hal_core/access_logic.h"
#include "../src/hal_core/event_manager.h"
#include "../src/hal_core/event_database.h"
#include "../src/sdk_modules/events/access_event.h"
#include "../src/sdk_modules/relays/relay.h"

void database_handler(AccessEvent_t* event) {
    EventDatabase_StoreEvent(event);
}

void ambient_handler(AccessEvent_t* event) {
    char* json = AccessEvent_ToJSON(event);
    printf("[AMBIENT.AI]: %s\n", json);
    EventDatabase_MarkAsSent(event->eventId);
    free(json);
}

int main() {
    printf("=== HAL WITH DATABASE TEST ===\n\n");
    
    printf("Initializing all systems...\n");
    AccessLogic_Initialize();
    EventManager_Initialize();
    EventDatabase_Initialize("hal_events.db");
    Relay_Init();
    
    EventManager_Subscribe("Database", database_handler);
    EventManager_Subscribe("Ambient.ai", ambient_handler);
    
    printf("\n--- Test 1: Valid Card ---\n");
    AccessDecision_t decision = AccessLogic_ProcessCardRead(123456, 1);
    
    if(decision.granted) {
        Relay_Unlock(1, 5000);
    }
    
    AccessEvent_t* event1 = AccessEvent_Create(
        decision.granted ? EVENT_ACCESS_GRANTED : EVENT_ACCESS_DENIED);
    sprintf(event1->eventId, "evt-%ld-001", time(NULL));
    strcpy(event1->cardNumber, "123456");
    event1->doorNumber = 1;
    event1->granted = decision.granted;
    
    EventManager_PublishEvent(event1);
    
    printf("\n--- Test 2: Invalid Card ---\n");
    decision = AccessLogic_ProcessCardRead(999999, 2);
    
    AccessEvent_t* event2 = AccessEvent_Create(EVENT_ACCESS_DENIED);
    sprintf(event2->eventId, "evt-%ld-002", time(NULL));
    strcpy(event2->cardNumber, "999999");
    event2->doorNumber = 2;
    event2->granted = false;
    
    EventManager_PublishEvent(event2);
    
    int unsent = EventDatabase_GetUnsentCount();
    printf("\nDatabase Status: %d events pending upload\n", unsent);
    
    AccessEvent_Destroy(event1);
    AccessEvent_Destroy(event2);
    
    EventDatabase_Shutdown();
    
    printf("\n=== TEST COMPLETE - Events stored in hal_events.db ===\n");
    return 0;
}
