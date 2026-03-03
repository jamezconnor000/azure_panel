#ifndef EVENT_DATABASE_H
#define EVENT_DATABASE_H

#include "../sdk_modules/events/access_event.h"
#include "../sdk_modules/common/sdk_types.h"

ErrorCode_t EventDatabase_Initialize(const char* db_path);
ErrorCode_t EventDatabase_StoreEvent(AccessEvent_t* event);
int EventDatabase_GetUnsentCount(void);
AccessEvent_t** EventDatabase_GetUnsentEvents(int limit);
ErrorCode_t EventDatabase_MarkAsSent(const char* event_id);
void EventDatabase_Shutdown(void);

#endif
