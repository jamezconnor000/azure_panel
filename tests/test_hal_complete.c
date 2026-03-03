#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "../src/hal_core/access_logic.h"
#include "../src/hal_core/event_manager.h"
#include "../src/sdk_modules/events/access_event.h"
#include "../src/sdk_modules/relays/relay.h"

void ambient_handler(AccessEvent_t* event) {
    char* json = AccessEvent_ToJSON(event);
    printf("[AMBIENT.AI]: %s\n", json);
    free(json);
}

int main() {
    printf("=== COMPLETE HAL SYSTEM TEST ===\n\n");
    
    printf("Initializing all systems...\n");
    AccessLogic_Initialize();
    EventManager_Initialize();
    Relay_Init();
    
    EventManager_Subscribe("Ambient.ai", ambient_handler);
    
    printf("\n--- Simulating Card Swipe ---\n");
    printf("Card 123456 swiped at Door 1\n");
    
    AccessDecision_t decision = AccessLogic_ProcessCardRead(123456, 1);
    printf("Access Decision: %s - %s\n",
           decision.granted ? "GRANTED" : "DENIED",
           decision.reason);
    
    if(decision.granted) {
        Relay_Unlock(1, 5000);
    }
    
    AccessEvent_t* event = AccessEvent_Create(
        decision.granted ? EVENT_ACCESS_GRANTED : EVENT_ACCESS_DENIED);
    strcpy(event->cardNumber, "123456");
    event->doorNumber = 1;
    event->granted = decision.granted;
    
    EventManager_PublishEvent(event);
    
    if(decision.granted) {
        printf("\nDOOR UNLOCKED - Person can enter\n");
        printf("Ambient.ai will now monitor video for tailgating\n");
    }
    
    AccessEvent_Destroy(event);
    
    printf("\n=== HAL SYSTEM OPERATIONAL ===\n");
    return 0;
}
