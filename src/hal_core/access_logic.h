#ifndef ACCESS_LOGIC_H
#define ACCESS_LOGIC_H

#include <stdint.h>
#include <stdbool.h>
#include <time.h>
#include "../sdk_modules/common/sdk_types.h"

typedef struct {
    uint32_t card_number;
    uint8_t door_number;
    bool granted;
    time_t timestamp;
    char cardholder_name[100];
    char reason[100];
} AccessLogicResult_t;

ErrorCode_t AccessLogic_Initialize(void);
AccessLogicResult_t AccessLogic_ProcessCardRead(uint32_t card_number, uint8_t door_number);
void AccessLogic_Shutdown(void);

#endif
