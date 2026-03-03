#ifndef EVENT_MANAGER_H
#define EVENT_MANAGER_H

#include "../sdk_modules/events/access_event.h"
#include "../sdk_modules/common/sdk_types.h"

ErrorCode_t EventManager_Initialize(void);
void EventManager_Subscribe(const char* name, void (*handler)(AccessEvent_t*));
void EventManager_PublishEvent(AccessEvent_t* event);
void EventManager_Shutdown(void);

#endif
