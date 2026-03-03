#include <stdio.h>
#include <assert.h>
#include "../include/hal_public.h"

int main() {
    printf("HAL Card Database Tests\\n");
    
    HALConfig_t config = { .event_buffer_size = 100000, .log_level = 6 };
    HAL_t* hal = HAL_Create(&config);
    assert(hal != NULL);
    
    Card_t card = { .card_id = 12345, .facility_code = 100 };
    assert(HAL_AddCard(hal, &card) == 0);
    printf("✓ Test 1: Add card - PASS\\n");
    
    Card_t out_card;
    assert(HAL_GetCard(hal, 12345, &out_card) == 0);
    printf("✓ Test 2: Get card - PASS\\n");
    
    HAL_Destroy(hal);
    printf("\\n✓ All tests passed\\n");
    return 0;
}
