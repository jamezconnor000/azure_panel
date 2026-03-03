#include "sdk_types.h"
#include <stdlib.h>
#include <string.h>

// =============================================================================
// LPA Helper Functions
// =============================================================================

int LPA_Equals(const LPA_t* a, const LPA_t* b) {
    if (!a || !b) return 0;
    return (a->type == b->type && a->id == b->id && a->node_id == b->node_id);
}

/*
 * Vector Implementation - Dynamic Array
 */

Vector_t* Vector_Create(uint32_t initial_capacity) {
    Vector_t* vec = (Vector_t*)malloc(sizeof(Vector_t));
    if (!vec) return NULL;
    
    vec->capacity = initial_capacity > 0 ? initial_capacity : 10;
    vec->count = 0;
    vec->data = (void**)malloc(sizeof(void*) * vec->capacity);
    
    if (!vec->data) {
        free(vec);
        return NULL;
    }
    
    return vec;
}

void Vector_Destroy(Vector_t* vec) {
    if (!vec) return;
    
    if (vec->data) {
        // Note: This doesn't free the items themselves, just the array
        // Caller is responsible for freeing items if needed
        free(vec->data);
    }
    
    free(vec);
}

void Vector_Add(Vector_t* vec, void* item) {
    if (!vec) return;
    
    // Resize if needed
    if (vec->count >= vec->capacity) {
        uint32_t new_capacity = vec->capacity * 2;
        void** new_data = (void**)realloc(vec->data, sizeof(void*) * new_capacity);
        
        if (!new_data) {
            // Out of memory - can't add item
            return;
        }
        
        vec->data = new_data;
        vec->capacity = new_capacity;
    }
    
    vec->data[vec->count++] = item;
}

void* Vector_Get(Vector_t* vec, uint32_t index) {
    if (!vec || index >= vec->count) {
        return NULL;
    }

    return vec->data[index];
}

void Vector_RemoveAt(Vector_t* vec, uint32_t index) {
    if (!vec || index >= vec->count) return;

    // Shift elements down
    for (uint32_t i = index; i < vec->count - 1; i++) {
        vec->data[i] = vec->data[i + 1];
    }
    vec->count--;
}

void Vector_Clear(Vector_t* vec) {
    if (!vec) return;
    vec->count = 0;
}

/*
 * Time Helper Functions
 */

Time_t Time_FromHMS(uint8_t hour, uint8_t minute, uint8_t second) {
    return (Time_t)(hour * 3600 + minute * 60 + second);
}

void Time_ToHMS(Time_t time, uint8_t* hour, uint8_t* minute, uint8_t* second) {
    if (hour) *hour = time / 3600;
    if (minute) *minute = (time % 3600) / 60;
    if (second) *second = time % 60;
}
