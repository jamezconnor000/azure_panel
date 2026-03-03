#include "access_point.h"
#include <stdlib.h>
#include <string.h>

AccessPoint_t* AccessPoint_Create(uint32_t id) {
    AccessPoint_t* ap = (AccessPoint_t*)malloc(sizeof(AccessPoint_t));
    if (!ap) return NULL;

    memset(ap, 0, sizeof(AccessPoint_t));
    ap->id = id;
    ap->lpa.type = LPAType_AccessPoint;
    ap->lpa.id = id;
    ap->lpa.node_id = 0;
    ap->init_mode = AccessPointMode_Locked;
    ap->short_strike_time = 5;
    ap->long_strike_time = 10;
    ap->short_held_open_time = 30;
    ap->long_held_open_time = 60;
    ap->strike_count = 0;

    return ap;
}

void AccessPoint_Destroy(AccessPoint_t* access_point) {
    if (access_point) {
        free(access_point);
    }
}

ErrorCode_t AccessPoint_AddStrike(AccessPoint_t* access_point, LPA_t strike_lpa, uint16_t pulse_duration) {
    if (!access_point) return ErrorCode_BadParams;
    if (access_point->strike_count >= 8) return ErrorCode_BadParams;

    access_point->strikes[access_point->strike_count].strike_lpa = strike_lpa;
    access_point->strikes[access_point->strike_count].pulse_duration = pulse_duration;
    access_point->strike_count++;

    return ErrorCode_OK;
}

ErrorCode_t AccessPoint_SetMode(AccessPoint_t* access_point, AccessPointMode_t mode) {
    if (!access_point) return ErrorCode_BadParams;
    access_point->init_mode = mode;
    return ErrorCode_OK;
}

ErrorCode_t AccessPoint_SetAreas(AccessPoint_t* access_point, LPA_t area_a, LPA_t area_b) {
    if (!access_point) return ErrorCode_BadParams;
    access_point->area_a = area_a;
    access_point->area_b = area_b;
    return ErrorCode_OK;
}
