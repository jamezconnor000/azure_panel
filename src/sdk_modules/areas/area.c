#include "area.h"
#include <stdlib.h>
#include <string.h>

Area_t* Area_Create(uint32_t id) {
    Area_t* area = (Area_t*)malloc(sizeof(Area_t));
    if (!area) return NULL;

    memset(area, 0, sizeof(Area_t));
    area->id = id;
    area->lpa.type = LPAType_Area;
    area->lpa.id = id;
    area->lpa.node_id = 0;
    area->timed_apb = 0;  // Disabled by default
    area->current_occupancy = 0;

    return area;
}

void Area_Destroy(Area_t* area) {
    if (area) {
        free(area);
    }
}

ErrorCode_t Area_SetName(Area_t* area, const char* name) {
    if (!area || !name) return ErrorCode_BadParams;
    strncpy(area->name, name, sizeof(area->name) - 1);
    area->name[sizeof(area->name) - 1] = '\0';
    return ErrorCode_OK;
}

ErrorCode_t Area_SetTimedAPB(Area_t* area, uint8_t minutes) {
    if (!area) return ErrorCode_BadParams;
    area->timed_apb = minutes;
    return ErrorCode_OK;
}

ErrorCode_t Area_SetOccupancyLimits(Area_t* area, uint8_t min, uint8_t max, uint8_t limit, uint8_t min_required) {
    if (!area) return ErrorCode_BadParams;
    area->min_occupancy = min;
    area->max_occupancy = max;
    area->occupancy_limit = limit;
    area->min_required_occupancy = min_required;
    return ErrorCode_OK;
}

ErrorCode_t Area_UpdateOccupancy(Area_t* area, int16_t delta) {
    if (!area) return ErrorCode_BadParams;

    int32_t new_occupancy = (int32_t)area->current_occupancy + delta;
    if (new_occupancy < 0) new_occupancy = 0;
    if (new_occupancy > 65535) new_occupancy = 65535;

    area->current_occupancy = (uint16_t)new_occupancy;
    return ErrorCode_OK;
}
