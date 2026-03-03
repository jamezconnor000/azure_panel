#include "group_list.h"
#include <stdlib.h>
#include <string.h>

// Simple in-memory storage
#define MAX_GROUP_LISTS 100

static GroupList_t* g_group_lists[MAX_GROUP_LISTS];
static int g_group_list_count = 0;

// =============================================================================
// Group List Implementation
// =============================================================================

GroupList_t* GroupList_Create(LPA_t id) {
    GroupList_t* list = (GroupList_t*)malloc(sizeof(GroupList_t));
    if (list) {
        list->Id = id;
        list->Count = 0;
        memset(list->Groups, 0, sizeof(list->Groups));
    }
    return list;
}

void GroupList_Destroy(GroupList_t* list) {
    if (list) {
        free(list);
    }
}

int GroupList_AddGroup(GroupList_t* list, uint32_t group_id) {
    if (!list || group_id == 0) return -1;
    if (list->Count >= MAX_GROUPS_PER_LIST) return -1;

    // Check if already exists
    if (GroupList_FindGroup(list, group_id) >= 0) {
        return -1;  // Already in list
    }

    // Add to first available position
    for (int i = 0; i < MAX_GROUPS_PER_LIST; i++) {
        if (list->Groups[i] == 0) {
            list->Groups[i] = group_id;
            list->Count++;
            return i;
        }
    }

    return -1;
}

ErrorCode_t GroupList_RemoveGroupAt(GroupList_t* list, int position) {
    if (!list || position < 0 || position >= MAX_GROUPS_PER_LIST) {
        return ErrorCode_BadParams;
    }

    if (list->Groups[position] == 0) {
        return ErrorCode_ObjectNotFound;
    }

    list->Groups[position] = 0;
    list->Count--;
    return ErrorCode_OK;
}

ErrorCode_t GroupList_RemoveGroup(GroupList_t* list, uint32_t group_id) {
    int position = GroupList_FindGroup(list, group_id);
    if (position < 0) {
        return ErrorCode_ObjectNotFound;
    }

    return GroupList_RemoveGroupAt(list, position);
}

void GroupList_Clear(GroupList_t* list) {
    if (list) {
        memset(list->Groups, 0, sizeof(list->Groups));
        list->Count = 0;
    }
}

uint32_t GroupList_GetGroupAt(GroupList_t* list, int position) {
    if (!list || position < 0 || position >= MAX_GROUPS_PER_LIST) {
        return 0;
    }
    return list->Groups[position];
}

int GroupList_FindGroup(GroupList_t* list, uint32_t group_id) {
    if (!list || group_id == 0) return -1;

    for (int i = 0; i < MAX_GROUPS_PER_LIST; i++) {
        if (list->Groups[i] == group_id) {
            return i;
        }
    }

    return -1;
}

int GroupList_GetCount(GroupList_t* list) {
    return list ? list->Count : 0;
}

int GroupList_IsFull(GroupList_t* list) {
    return list && list->Count >= MAX_GROUPS_PER_LIST;
}

int GroupList_IsEmpty(GroupList_t* list) {
    return list && list->Count == 0;
}

const uint32_t* GroupList_GetGroups(GroupList_t* list) {
    return list ? list->Groups : NULL;
}

// =============================================================================
// Internal Helper Functions
// =============================================================================

static int FindGroupListIndex(LPA_t id) {
    for (int i = 0; i < g_group_list_count; i++) {
        if (g_group_lists[i] && LPA_Equals(&g_group_lists[i]->Id, &id)) {
            return i;
        }
    }
    return -1;
}

// =============================================================================
// Group List Management (Global)
// =============================================================================

ErrorCode_t GroupList_Add(GroupList_t* list) {
    if (!list) return ErrorCode_BadParams;
    if (g_group_list_count >= MAX_GROUP_LISTS) return ErrorCode_OutOfMemory;

    // Check if already exists
    if (FindGroupListIndex(list->Id) >= 0) {
        return ErrorCode_AlreadyExists;
    }

    g_group_lists[g_group_list_count++] = list;
    return ErrorCode_OK;
}

GroupList_t* GroupList_Get(LPA_t id) {
    int index = FindGroupListIndex(id);
    if (index >= 0) {
        return g_group_lists[index];
    }
    return NULL;
}

ErrorCode_t GroupList_Update(GroupList_t* list) {
    if (!list) return ErrorCode_BadParams;

    int index = FindGroupListIndex(list->Id);
    if (index < 0) return ErrorCode_ObjectNotFound;

    // Replace group list
    GroupList_Destroy(g_group_lists[index]);
    g_group_lists[index] = list;

    return ErrorCode_OK;
}

ErrorCode_t GroupList_Delete(LPA_t id) {
    int index = FindGroupListIndex(id);
    if (index < 0) return ErrorCode_ObjectNotFound;

    GroupList_Destroy(g_group_lists[index]);

    // Shift remaining lists
    for (int i = index; i < g_group_list_count - 1; i++) {
        g_group_lists[i] = g_group_lists[i + 1];
    }
    g_group_list_count--;

    return ErrorCode_OK;
}

int GroupList_GetTotalCount(void) {
    return g_group_list_count;
}
