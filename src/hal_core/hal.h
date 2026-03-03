#ifndef HAL_CORE_H
#define HAL_CORE_H
#include "../../include/hal_types.h"
typedef struct {
    void* event_manager;
    void* card_database;
    void* access_logic;
    HALConfig_t config;
    uint8_t is_connected;
    char last_error[256];
} HAL_Instance_t;
#endif
