#include <stdio.h>
#include "../src/hal_core/config.h"
#include "../src/hal_core/access_logic.h"
#include "../src/hal_core/event_manager.h"
#include "../src/sdk_modules/relays/relay.h"

int main() {
    printf("=== HAL CONFIG TEST ===\n\n");
    
    HALConfig_t* config = Config_Load("../config/hal_config.json");
    if (!config) {
        printf("Failed to load configuration!\n");
        return 1;
    }
    
    Config_Print(config);
    
    printf("Initializing systems with config values...\n");
    AccessLogic_Initialize();
    EventManager_Initialize();
    Relay_Init();
    
    printf("\nSimulating access with configured door unlock time: %dms\n", 
           config->hardware.door_unlock_time_ms);
    
    for (int i = 0; i < config->door_count; i++) {
        printf("\nDoor %d (%s) using relay %d\n", 
               config->doors[i].id,
               config->doors[i].name,
               config->doors[i].relay_id);
        
        if (i == 0) {
            Relay_Unlock(config->doors[i].relay_id, 
                        config->hardware.door_unlock_time_ms);
        }
    }
    
    Config_Free(config);
    printf("\n=== CONFIG TEST COMPLETE ===\n");
    return 0;
}
