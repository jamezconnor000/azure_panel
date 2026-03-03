#include <stdio.h>
#include "../include/hal_public.h"

int main() {
    printf("HAL Card Provisioning Example\\n");
    
    HAL_RuntimeConfig_t config = { .event_buffer_size = 100000, .log_level = 6 };
    HAL_t* hal = HAL_Create(&config);
    HAL_Connect(hal, "localhost", 5000);
    
    for (int i = 1; i <= 5; i++) {
        Card_t card = {
            .card_id = 10000 + i,
            .facility_code = 100,
            .card_number = 0x11000000 + i,
            .is_blocked = 0,
        };
        
        if (HAL_AddCard(hal, &card) == 0) {
            printf("✓ Card %u added\\n", card.card_id);
        }
    }
    
    HAL_Disconnect(hal);
    HAL_Destroy(hal);
    return 0;
}
