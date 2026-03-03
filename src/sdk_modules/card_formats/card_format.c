#include "card_format.h"
#include <stdlib.h>
#include <string.h>

CardFormat_t* CardFormat_Create(uint8_t id) {
    CardFormat_t* format = (CardFormat_t*)malloc(sizeof(CardFormat_t));
    if (!format) return NULL;

    memset(format, 0, sizeof(CardFormat_t));
    format->id = id;
    format->type = CardFormatType_Wiegand;
    format->total_bits = 26;  // Default to 26-bit Wiegand

    return format;
}

void CardFormat_Destroy(CardFormat_t* format) {
    if (format) {
        free(format);
    }
}

ErrorCode_t CardFormat_SetWiegand(CardFormat_t* format,
                                   uint8_t total_bits,
                                   uint8_t facility_start, uint8_t facility_length,
                                   uint8_t card_start, uint8_t card_length) {
    if (!format) return ErrorCode_BadParams;

    format->type = CardFormatType_Wiegand;
    format->total_bits = total_bits;
    format->facility_start_bit = facility_start;
    format->facility_bit_length = facility_length;
    format->card_start_bit = card_start;
    format->card_bit_length = card_length;

    return ErrorCode_OK;
}

CardFormatList_t* CardFormatList_Create(uint8_t id) {
    CardFormatList_t* list = (CardFormatList_t*)malloc(sizeof(CardFormatList_t));
    if (!list) return NULL;

    memset(list, 0, sizeof(CardFormatList_t));
    list->id = id;
    list->count = 0;

    return list;
}

void CardFormatList_Destroy(CardFormatList_t* list) {
    if (list) {
        free(list);
    }
}

ErrorCode_t CardFormatList_AddFormat(CardFormatList_t* list, uint8_t format_id) {
    if (!list) return ErrorCode_BadParams;
    if (list->count >= 16) return ErrorCode_BadParams;

    list->format_ids[list->count] = format_id;
    list->count++;

    return ErrorCode_OK;
}
