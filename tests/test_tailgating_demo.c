#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <unistd.h>
#include "../src/sdk_modules/events/access_event.h"

void simulate_ambient_ai(AccessEvent_t* event, int people_count) {
    char* json = AccessEvent_ToJSON(event);
    printf("\n[HAL -> Ambient.ai]: %s\n", json);
    
    if (event->type == EVENT_ACCESS_GRANTED) {
        printf("[Ambient.ai Camera]: Detected %d person(s) entering\n", people_count);
        
        if (people_count > 1) {
            printf("\n🚨 TAILGATING ALERT! 🚨\n");
            printf("   1 badge swipe but %d people entered!\n", people_count);
            printf("   Location: %s\n", event->doorName);
            printf("   Card: %s\n\n", event->cardNumber);
        } else {
            printf("✅ Normal entry - counts match\n\n");
        }
    }
    
    free(json);
}

int main() {
    printf("=== TAILGATING DETECTION DEMONSTRATION ===\n");
    printf("This shows how HAL + Ambient.ai work together\n");
    printf("==========================================\n");
    
    printf("\nScenario 1: Normal Entry\n");
    printf("------------------------\n");
    AccessEvent_t* event1 = AccessEvent_Create(EVENT_ACCESS_GRANTED);
    strcpy(event1->doorName, "Main Entrance");
    strcpy(event1->cardNumber, "123456");
    event1->doorNumber = 1;
    simulate_ambient_ai(event1, 1);
    AccessEvent_Destroy(event1);
    
    printf("\nScenario 2: TAILGATING!\n");
    printf("------------------------\n");
    AccessEvent_t* event2 = AccessEvent_Create(EVENT_ACCESS_GRANTED);
    strcpy(event2->doorName, "Server Room");
    strcpy(event2->cardNumber, "789012");
    event2->doorNumber = 2;
    simulate_ambient_ai(event2, 2);
    AccessEvent_Destroy(event2);
    
    printf("=== DEMONSTRATION COMPLETE ===\n");
    return 0;
}
