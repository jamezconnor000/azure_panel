#include "access_logic.h"
#include "../sdk_modules/events/access_event.h"
#include "../sdk_modules/timezones/timezone.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

typedef struct {
    uint32_t card_number;
    uint32_t door_mask;
    uint32_t timezone_id;
    char name[100];
} Permission_t;

typedef struct {
    Permission_t* permissions;
    int count;
    int capacity;
} AccessLogic_t;

static AccessLogic_t* g_logic = NULL;

ErrorCode_t AccessLogic_Initialize(void) {
    if (g_logic) return ErrorCode_OK;
    
    g_logic = malloc(sizeof(AccessLogic_t));
    g_logic->capacity = 100;
    g_logic->permissions = malloc(sizeof(Permission_t) * g_logic->capacity);
    g_logic->count = 0;
    
    g_logic->permissions[0].card_number = 123456;
    g_logic->permissions[0].door_mask = 0xFF;
    g_logic->permissions[0].timezone_id = 2;
    strcpy(g_logic->permissions[0].name, "John Smith");
    g_logic->count = 1;
    
    printf("Access Logic initialized with %d permissions\n", g_logic->count);
    return ErrorCode_OK;
}

AccessLogicResult_t AccessLogic_ProcessCardRead(uint32_t card_number, uint8_t door_number) {
    AccessLogicResult_t decision = {0};
    decision.card_number = card_number;
    decision.door_number = door_number;
    decision.granted = false;
    decision.timestamp = time(NULL);
    
    for (int i = 0; i < g_logic->count; i++) {
        if (g_logic->permissions[i].card_number == card_number) {
            if (g_logic->permissions[i].door_mask & (1 << door_number)) {
                decision.granted = true;
                strcpy(decision.cardholder_name, g_logic->permissions[i].name);
                strcpy(decision.reason, "Access permitted");
            } else {
                strcpy(decision.reason, "No permission for this door");
            }
            return decision;
        }
    }
    
    strcpy(decision.reason, "Card not found");
    return decision;
}

void AccessLogic_Shutdown(void) {
    if (g_logic) {
        free(g_logic->permissions);
        free(g_logic);
        g_logic = NULL;
    }
}
