#ifndef HAL_PUBLIC_H
#define HAL_PUBLIC_H
#include "hal_types.h"

typedef struct HAL_Handle HAL_t;

HAL_t* HAL_Create(const HALConfig_t* config);
void HAL_Destroy(HAL_t* hal);
ErrorCode_t HAL_Connect(HAL_t* hal, const char* addr, uint16_t port);
ErrorCode_t HAL_Disconnect(HAL_t* hal);
uint8_t HAL_IsConnected(HAL_t* hal);

ErrorCode_t HAL_SubscribeToEvents(HAL_t* hal, const EventSubscription_t* sub);
ErrorCode_t HAL_UnsubscribeFromEvents(HAL_t* hal);
ErrorCode_t HAL_SendEventAck(HAL_t* hal, const EventAck_t* ack);

ErrorCode_t HAL_AddCard(HAL_t* hal, const Card_t* card);
ErrorCode_t HAL_GetCard(HAL_t* hal, CardId_t card_id, Card_t* out);
ErrorCode_t HAL_UpdateCard(HAL_t* hal, const Card_t* card);
ErrorCode_t HAL_DeleteCard(HAL_t* hal, CardId_t card_id);

ErrorCode_t HAL_DecideAccess(HAL_t* hal, CardId_t card_id, LPA_t reader, AccessResult_t* result);
ErrorCode_t HAL_EnergizeRelay(HAL_t* hal, uint32_t relay_id, uint32_t duration_ms);

ErrorCode_t HAL_GetEventBufferStatus(HAL_t* hal, EventBufferStatus_t* status);
ErrorCode_t HAL_ClearEventBuffer(HAL_t* hal);
ErrorCode_t HAL_SetLogLevel(HAL_t* hal, uint8_t level);

#endif
