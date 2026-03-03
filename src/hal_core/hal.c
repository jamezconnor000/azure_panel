#include "../../include/hal_public.h"
#include "hal.h"
#include <stdlib.h>
#include <string.h>

HAL_t* HAL_Create(const HALConfig_t* config) {
    HAL_Instance_t* hal = (HAL_Instance_t*)malloc(sizeof(HAL_Instance_t));
    if (!hal) return NULL;
    memcpy(&hal->config, config, sizeof(HALConfig_t));
    hal->is_connected = 0;
    return (HAL_t*)hal;
}

void HAL_Destroy(HAL_t* hal) { free(hal); }
ErrorCode_t HAL_Connect(HAL_t* hal, const char* addr, uint16_t port) { HAL_Instance_t* h = (HAL_Instance_t*)hal; h->is_connected = 1; return ErrorCode_OK; }
ErrorCode_t HAL_Disconnect(HAL_t* hal) { HAL_Instance_t* h = (HAL_Instance_t*)hal; h->is_connected = 0; return ErrorCode_OK; }
uint8_t HAL_IsConnected(HAL_t* hal) { return ((HAL_Instance_t*)hal)->is_connected; }

ErrorCode_t HAL_SubscribeToEvents(HAL_t* hal, const EventSubscription_t* sub) { return ErrorCode_OK; }
ErrorCode_t HAL_UnsubscribeFromEvents(HAL_t* hal) { return ErrorCode_OK; }
ErrorCode_t HAL_SendEventAck(HAL_t* hal, const EventAck_t* ack) { return ErrorCode_OK; }

ErrorCode_t HAL_AddCard(HAL_t* hal, const Card_t* card) { return ErrorCode_OK; }
ErrorCode_t HAL_GetCard(HAL_t* hal, CardId_t id, Card_t* out) { return ErrorCode_OK; }
ErrorCode_t HAL_UpdateCard(HAL_t* hal, const Card_t* card) { return ErrorCode_OK; }
ErrorCode_t HAL_DeleteCard(HAL_t* hal, CardId_t id) { return ErrorCode_OK; }

ErrorCode_t HAL_DecideAccess(HAL_t* hal, CardId_t id, LPA_t reader, AccessResult_t* result) { result->decision = AccessDecision_Grant; result->strike_time_ms = 1000; return ErrorCode_OK; }
ErrorCode_t HAL_EnergizeRelay(HAL_t* hal, uint32_t id, uint32_t duration) { return ErrorCode_OK; }

ErrorCode_t HAL_GetEventBufferStatus(HAL_t* hal, EventBufferStatus_t* status) { memset(status, 0, sizeof(EventBufferStatus_t)); return ErrorCode_OK; }
ErrorCode_t HAL_ClearEventBuffer(HAL_t* hal) { return ErrorCode_OK; }
ErrorCode_t HAL_SetLogLevel(HAL_t* hal, uint8_t level) { return ErrorCode_OK; }
