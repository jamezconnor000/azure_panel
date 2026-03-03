#include <stdio.h>
#include "../include/hal_public.h"

int main() {
    printf("HAL Event Subscription Example\\n");
    
    HALConfig_t config = {
        .event_buffer_size = 100000,
        .max_events_before_ack = 50,
        .connection_timeout_ms = 5000,
        .log_level = 6,
    };
    
    HAL_t* hal = HAL_Create(&config);
    HAL_Connect(hal, "localhost", 5000);
    
    EventSubscription_t sub = {
        .max_events_before_ack = 50,
        .src_node = 0,
        .start_event_serial_number = 0,
    };
    
    HAL_SubscribeToEvents(hal, &sub);
    printf("✓ Subscribed to events\\n");
    
    EventBufferStatus_t status;
    if (HAL_GetEventBufferStatus(hal, &status) == 0) {
        printf("Event buffer status: %u events\\n", status.total_events);
    }
    
    HAL_Disconnect(hal);
    HAL_Destroy(hal);
    return 0;
}
