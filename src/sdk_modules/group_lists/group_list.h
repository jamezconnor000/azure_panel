#ifndef SDK_GROUP_LIST_H
#define SDK_GROUP_LIST_H

#include "../common/sdk_types.h"
#include <stdint.h>

/*
 * Azure Access Technology SDK - Group List Module
 * Based on GroupList.h documentation
 *
 * Used for visitor/escort group management. Up to 32 groups can be
 * assigned to a group list.
 */

// =============================================================================
// Group List Structure
// =============================================================================

#define MAX_GROUPS_PER_LIST 32

/**
 * GroupList - Collection of group IDs for visitor/escort management
 *
 * Groups are stored in order with positions 0-31.
 */
typedef struct {
    LPA_t Id;                       // GroupList LPA
    uint32_t Groups[MAX_GROUPS_PER_LIST];  // Group IDs (0 = empty slot)
    int Count;                      // Number of groups in list
} GroupList_t;

// =============================================================================
// Group List Functions
// =============================================================================

/**
 * Create a new group list
 */
GroupList_t* GroupList_Create(LPA_t id);

/**
 * Destroy group list
 */
void GroupList_Destroy(GroupList_t* list);

/**
 * Add a group to the list
 * Returns position (0-31) or -1 if list is full
 */
int GroupList_AddGroup(GroupList_t* list, uint32_t group_id);

/**
 * Remove a group from the list by position
 */
ErrorCode_t GroupList_RemoveGroupAt(GroupList_t* list, int position);

/**
 * Remove a group from the list by ID
 */
ErrorCode_t GroupList_RemoveGroup(GroupList_t* list, uint32_t group_id);

/**
 * Clear all groups from the list
 */
void GroupList_Clear(GroupList_t* list);

/**
 * Get group at specific position
 */
uint32_t GroupList_GetGroupAt(GroupList_t* list, int position);

/**
 * Check if a group is in the list
 * Returns position if found, -1 if not found
 */
int GroupList_FindGroup(GroupList_t* list, uint32_t group_id);

/**
 * Get number of groups in list
 */
int GroupList_GetCount(GroupList_t* list);

/**
 * Check if list is full
 */
int GroupList_IsFull(GroupList_t* list);

/**
 * Check if list is empty
 */
int GroupList_IsEmpty(GroupList_t* list);

/**
 * Get all group IDs as an array
 * Returns pointer to internal array
 */
const uint32_t* GroupList_GetGroups(GroupList_t* list);

// =============================================================================
// Group List Management (Global)
// =============================================================================

/**
 * Add group list to global storage
 */
ErrorCode_t GroupList_Add(GroupList_t* list);

/**
 * Get group list by ID
 */
GroupList_t* GroupList_Get(LPA_t id);

/**
 * Update group list
 */
ErrorCode_t GroupList_Update(GroupList_t* list);

/**
 * Delete group list
 */
ErrorCode_t GroupList_Delete(LPA_t id);

/**
 * Get count of all group lists
 */
int GroupList_GetTotalCount(void);

#endif // SDK_GROUP_LIST_H
