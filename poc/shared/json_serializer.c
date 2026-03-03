/**
 * @file json_serializer.c
 * @brief JSON serialization/deserialization implementation
 *
 * @author FAM-HAL-v1.0-001
 * @date February 10, 2026
 */

#include "json_serializer.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

/* ============================================================================
 * Utility Functions
 * ========================================================================== */

int json_get_string(const cJSON* obj, const char* key, char* dest, size_t max_len) {
    if (!obj || !key || !dest || max_len == 0) {
        return -1;
    }

    cJSON* item = cJSON_GetObjectItemCaseSensitive(obj, key);
    if (!item || !cJSON_IsString(item) || !item->valuestring) {
        return -1;
    }

    strncpy(dest, item->valuestring, max_len - 1);
    dest[max_len - 1] = '\0';
    return 0;
}

int json_get_int(const cJSON* obj, const char* key, int* dest) {
    if (!obj || !key || !dest) {
        return -1;
    }

    cJSON* item = cJSON_GetObjectItemCaseSensitive(obj, key);
    if (!item || !cJSON_IsNumber(item)) {
        return -1;
    }

    *dest = item->valueint;
    return 0;
}

int json_get_int64(const cJSON* obj, const char* key, int64_t* dest) {
    if (!obj || !key || !dest) {
        return -1;
    }

    cJSON* item = cJSON_GetObjectItemCaseSensitive(obj, key);
    if (!item || !cJSON_IsNumber(item)) {
        return -1;
    }

    /* cJSON stores doubles internally, cast to int64 */
    *dest = (int64_t)item->valuedouble;
    return 0;
}

int json_get_bool(const cJSON* obj, const char* key, bool* dest) {
    if (!obj || !key || !dest) {
        return -1;
    }

    cJSON* item = cJSON_GetObjectItemCaseSensitive(obj, key);
    if (!item) {
        return -1;
    }

    if (cJSON_IsBool(item)) {
        *dest = cJSON_IsTrue(item);
        return 0;
    }

    return -1;
}

/* ============================================================================
 * Event Serialization
 * ========================================================================== */

cJSON* event_to_cjson(const hal_event_t* event) {
    if (!event) {
        return NULL;
    }

    cJSON* root = cJSON_CreateObject();
    if (!root) {
        return NULL;
    }

    /* Event identification */
    cJSON_AddStringToObject(root, "event_uid", event->event_uid);
    cJSON_AddNumberToObject(root, "event_type", event->event_type);
    cJSON_AddNumberToObject(root, "version", event->version);

    /* Device information */
    cJSON_AddStringToObject(root, "device_uid", event->device_uid);
    cJSON_AddStringToObject(root, "device_name", event->device_name);
    cJSON_AddStringToObject(root, "device_type", event->device_type);

    /* Alarm information */
    cJSON_AddStringToObject(root, "alarm_uid", event->alarm_uid);
    cJSON_AddStringToObject(root, "alarm_name", event->alarm_name);

    /* Timestamps */
    cJSON_AddNumberToObject(root, "occurred_at", (double)event->occurred_timestamp);
    cJSON_AddNumberToObject(root, "published_at", (double)event->published_timestamp);

    /* Access-specific fields */
    if (event->has_person) {
        cJSON_AddStringToObject(root, "person_uid", event->person_uid);
    } else {
        cJSON_AddNullToObject(root, "person_uid");
    }
    cJSON_AddStringToObject(root, "access_item_key", event->access_item_key);
    cJSON_AddNumberToObject(root, "access_result", event->access_result);

    /* Wiegand data */
    cJSON_AddNumberToObject(root, "facility_code", event->facility_code);
    cJSON_AddNumberToObject(root, "card_number", event->card_number);
    cJSON_AddNumberToObject(root, "reader_port", event->reader_port);

    return root;
}

char* event_to_json(const hal_event_t* event) {
    cJSON* root = event_to_cjson(event);
    if (!root) {
        return NULL;
    }

    char* json_str = cJSON_PrintUnformatted(root);
    cJSON_Delete(root);

    return json_str;
}

int cjson_to_event(const cJSON* json_obj, hal_event_t* event) {
    if (!json_obj || !event) {
        return -1;
    }

    /* Initialize event */
    event_init(event);

    /* Event identification */
    json_get_string(json_obj, "event_uid", event->event_uid, UUID_STRING_LEN);

    int event_type_int = 0;
    if (json_get_int(json_obj, "event_type", &event_type_int) == 0) {
        event->event_type = (event_type_t)event_type_int;
    }

    json_get_int(json_obj, "version", &event->version);

    /* Device information */
    json_get_string(json_obj, "device_uid", event->device_uid, UUID_STRING_LEN);
    json_get_string(json_obj, "device_name", event->device_name, DEVICE_NAME_MAX_LEN);
    json_get_string(json_obj, "device_type", event->device_type, DEVICE_TYPE_MAX_LEN);

    /* Alarm information */
    json_get_string(json_obj, "alarm_uid", event->alarm_uid, UUID_STRING_LEN);
    json_get_string(json_obj, "alarm_name", event->alarm_name, ALARM_NAME_MAX_LEN);

    /* Timestamps */
    json_get_int64(json_obj, "occurred_at", &event->occurred_timestamp);
    json_get_int64(json_obj, "published_at", &event->published_timestamp);

    /* Access-specific fields */
    cJSON* person_uid_item = cJSON_GetObjectItemCaseSensitive(json_obj, "person_uid");
    if (person_uid_item && cJSON_IsString(person_uid_item) && person_uid_item->valuestring) {
        strncpy(event->person_uid, person_uid_item->valuestring, UUID_STRING_LEN - 1);
        event->has_person = true;
    } else {
        event->has_person = false;
    }

    json_get_string(json_obj, "access_item_key", event->access_item_key, ACCESS_ITEM_KEY_MAX_LEN);

    int access_result_int = 0;
    if (json_get_int(json_obj, "access_result", &access_result_int) == 0) {
        event->access_result = (access_result_t)access_result_int;
    }

    /* Wiegand data */
    int fc = 0, cn = 0, port = 0;
    if (json_get_int(json_obj, "facility_code", &fc) == 0) {
        event->facility_code = (uint32_t)fc;
    }
    if (json_get_int(json_obj, "card_number", &cn) == 0) {
        event->card_number = (uint32_t)cn;
    }
    if (json_get_int(json_obj, "reader_port", &port) == 0) {
        event->reader_port = (uint32_t)port;
    }

    return 0;
}

int json_to_event(const char* json, hal_event_t* event) {
    if (!json || !event) {
        return -1;
    }

    cJSON* root = cJSON_Parse(json);
    if (!root) {
        return -1;
    }

    int result = cjson_to_event(root, event);
    cJSON_Delete(root);

    return result;
}

/* ============================================================================
 * IPC Message Serialization
 * ========================================================================== */

char* create_ipc_message(const hal_event_t* event, ipc_msg_type_t msg_type) {
    if (!event) {
        return NULL;
    }

    cJSON* root = cJSON_CreateObject();
    if (!root) {
        return NULL;
    }

    /* Message envelope */
    cJSON_AddStringToObject(root, "msg_type",
        msg_type == IPC_MSG_TYPE_EVENT ? "EVENT" :
        msg_type == IPC_MSG_TYPE_ACK ? "ACK" :
        msg_type == IPC_MSG_TYPE_HEARTBEAT ? "HEARTBEAT" :
        msg_type == IPC_MSG_TYPE_STATUS ? "STATUS" : "UNKNOWN");

    cJSON_AddNumberToObject(root, "version", EVENT_VERSION);

    /* Add event payload */
    cJSON* payload = event_to_cjson(event);
    if (payload) {
        cJSON_AddItemToObject(root, "payload", payload);
    }

    char* json_str = cJSON_PrintUnformatted(root);
    cJSON_Delete(root);

    return json_str;
}

int parse_ipc_message(const char* json, hal_event_t* event, ipc_msg_type_t* msg_type) {
    if (!json || !event) {
        return -1;
    }

    cJSON* root = cJSON_Parse(json);
    if (!root) {
        return -1;
    }

    /* Extract message type */
    if (msg_type) {
        char type_str[32] = {0};
        if (json_get_string(root, "msg_type", type_str, sizeof(type_str)) == 0) {
            if (strcmp(type_str, "EVENT") == 0) {
                *msg_type = IPC_MSG_TYPE_EVENT;
            } else if (strcmp(type_str, "ACK") == 0) {
                *msg_type = IPC_MSG_TYPE_ACK;
            } else if (strcmp(type_str, "HEARTBEAT") == 0) {
                *msg_type = IPC_MSG_TYPE_HEARTBEAT;
            } else if (strcmp(type_str, "STATUS") == 0) {
                *msg_type = IPC_MSG_TYPE_STATUS;
            } else {
                *msg_type = IPC_MSG_TYPE_UNKNOWN;
            }
        }
    }

    /* Extract payload */
    cJSON* payload = cJSON_GetObjectItemCaseSensitive(root, "payload");
    if (!payload) {
        cJSON_Delete(root);
        return -1;
    }

    int result = cjson_to_event(payload, event);
    cJSON_Delete(root);

    return result;
}

/* ============================================================================
 * Ambient.ai Format Serialization
 * ========================================================================== */

char* event_to_ambient_json(const hal_event_t* event, const char* source_system_uid) {
    if (!event || !source_system_uid) {
        return NULL;
    }

    cJSON* root = cJSON_CreateObject();
    if (!root) {
        return NULL;
    }

    /* Required fields per Ambient.ai Generic Cloud Event Ingestion spec */
    cJSON_AddStringToObject(root, "sourceSystemUid", source_system_uid);
    cJSON_AddStringToObject(root, "deviceUid", event->device_uid);
    cJSON_AddStringToObject(root, "deviceName", event->device_name);
    cJSON_AddStringToObject(root, "deviceType", event->device_type);
    cJSON_AddStringToObject(root, "eventUid", event->event_uid);
    cJSON_AddStringToObject(root, "alarmName", event->alarm_name);
    cJSON_AddStringToObject(root, "alarmUid", event->alarm_uid);
    cJSON_AddNumberToObject(root, "occurredTimestamp", (double)event->occurred_timestamp);
    cJSON_AddNumberToObject(root, "publishedTimestamp", (double)event->published_timestamp);

    /* Optional fields */
    if (event->has_person && event->person_uid[0] != '\0') {
        cJSON_AddStringToObject(root, "personUid", event->person_uid);
    }

    /* accessItemKey is mandatory for access granted/denied events */
    if (event->event_type == EVENT_TYPE_ACCESS_GRANTED ||
        event->event_type == EVENT_TYPE_ACCESS_DENIED) {
        cJSON_AddStringToObject(root, "accessItemKey", event->access_item_key);
    }

    char* json_str = cJSON_PrintUnformatted(root);
    cJSON_Delete(root);

    return json_str;
}

/* ============================================================================
 * Card/Device Serialization
 * ========================================================================== */

char* card_info_to_json(const card_info_t* card) {
    if (!card) {
        return NULL;
    }

    cJSON* root = cJSON_CreateObject();
    if (!root) {
        return NULL;
    }

    cJSON_AddNumberToObject(root, "id", (double)card->id);
    cJSON_AddNumberToObject(root, "card_number", card->card_number);
    cJSON_AddNumberToObject(root, "facility_code", card->facility_code);
    cJSON_AddStringToObject(root, "card_uid", card->card_uid);
    cJSON_AddStringToObject(root, "person_uid", card->person_uid);
    cJSON_AddStringToObject(root, "first_name", card->first_name);
    cJSON_AddStringToObject(root, "last_name", card->last_name);
    cJSON_AddBoolToObject(root, "enabled", card->enabled);
    cJSON_AddNumberToObject(root, "valid_from", (double)card->valid_from);
    cJSON_AddNumberToObject(root, "valid_until", (double)card->valid_until);
    cJSON_AddNumberToObject(root, "permission_group", card->permission_group);

    char* json_str = cJSON_PrintUnformatted(root);
    cJSON_Delete(root);

    return json_str;
}

int json_to_card_info(const char* json, card_info_t* card) {
    if (!json || !card) {
        return -1;
    }

    cJSON* root = cJSON_Parse(json);
    if (!root) {
        return -1;
    }

    memset(card, 0, sizeof(card_info_t));

    json_get_int64(root, "id", &card->id);

    int cn = 0, fc = 0, pg = 0;
    if (json_get_int(root, "card_number", &cn) == 0) {
        card->card_number = (uint32_t)cn;
    }
    if (json_get_int(root, "facility_code", &fc) == 0) {
        card->facility_code = (uint32_t)fc;
    }

    json_get_string(root, "card_uid", card->card_uid, UUID_STRING_LEN);
    json_get_string(root, "person_uid", card->person_uid, UUID_STRING_LEN);
    json_get_string(root, "first_name", card->first_name, sizeof(card->first_name));
    json_get_string(root, "last_name", card->last_name, sizeof(card->last_name));
    json_get_bool(root, "enabled", &card->enabled);
    json_get_int64(root, "valid_from", &card->valid_from);
    json_get_int64(root, "valid_until", &card->valid_until);

    if (json_get_int(root, "permission_group", &pg) == 0) {
        card->permission_group = pg;
    }

    cJSON_Delete(root);
    return 0;
}

char* device_entry_to_json(const device_entry_t* device) {
    if (!device) {
        return NULL;
    }

    cJSON* root = cJSON_CreateObject();
    if (!root) {
        return NULL;
    }

    cJSON_AddStringToObject(root, "device_uid", device->device_uid);
    cJSON_AddStringToObject(root, "device_name", device->device_name);
    cJSON_AddStringToObject(root, "device_type", device_type_to_string(device->device_type));
    cJSON_AddNumberToObject(root, "port", device->port);
    cJSON_AddBoolToObject(root, "enabled", device->enabled);

    char* json_str = cJSON_PrintUnformatted(root);
    cJSON_Delete(root);

    return json_str;
}
