#include <stdio.h>
#include "../include/hal_public.h"

int main(int argc, char* argv[]) {
    printf("HAL Basic Access Example\\n");
    
    HAL_RuntimeConfig_t config = {
        .event_buffer_size = 100000,
        .max_events_before_ack = 50,
        .connection_timeout_ms = 5000,
        .log_level = 6,
    };
    
    HAL_t* hal = HAL_Create(&config);
    if (!hal) {
        printf("Failed to create HAL\\n");
        return 1;
    }
    
    if (HAL_Connect(hal, "localhost", 5000) != 0) {
        printf("Failed to connect\\n");
        HAL_Destroy(hal);
        return 1;
    }
    
    printf("✓ Connected to HAL\\n");
    
    Card_t card = {
        .card_id = 12345,
        .facility_code = 100,
        .card_number = 0x11223344,
        .is_blocked = 0,
    };
    
    if (HAL_AddCard(hal, &card) == 0) {
        printf("✓ Card 12345 added\\n");
    }
    
    LPA_t reader = {.type = LPAType_Reader, .id = 1, .node_id = 0};
    AccessResult_t result;
    
    if (HAL_DecideAccess(hal, 12345, reader, &result) == 0) {
        printf("✓ Access decision made: %s\\n", 
               result.decision ? "DENY" : "GRANT");
    }
    
    HAL_Disconnect(hal);
    HAL_Destroy(hal);
    
    printf("✓ Example complete\\n");
    return 0;
}
