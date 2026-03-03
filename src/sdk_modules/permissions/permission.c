#include "permission.h"
#include <stdlib.h>
#include <string.h>
#include <time.h>

// =============================================================================
// PermissionEntry Implementation
// =============================================================================

PermissionEntry_t* PermissionEntry_Create(void) {
    PermissionEntry_t* entry = (PermissionEntry_t*)malloc(sizeof(PermissionEntry_t));
    if (entry) {
        memset(entry, 0, sizeof(PermissionEntry_t));
        entry->AccessObject = c_lpaNULL;
        entry->Strike = c_lpaNULL;
        entry->TimeZone = 0;
        entry->OverridePermissionFlagsMask = 0;
        entry->OverridePermissionFlags = 0;
    }
    return entry;
}

void PermissionEntry_Destroy(PermissionEntry_t* entry) {
    if (entry) {
        free(entry);
    }
}

PermissionEntry_t* PermissionEntry_Clone(const PermissionEntry_t* entry) {
    if (!entry) return NULL;

    PermissionEntry_t* clone = PermissionEntry_Create();
    if (clone) {
        memcpy(clone, entry, sizeof(PermissionEntry_t));
    }
    return clone;
}

// =============================================================================
// ExclusionEntry Implementation
// =============================================================================

ExclusionEntry_t* ExclusionEntry_Create(void) {
    ExclusionEntry_t* entry = (ExclusionEntry_t*)malloc(sizeof(ExclusionEntry_t));
    if (entry) {
        memset(entry, 0, sizeof(ExclusionEntry_t));
        entry->AccessObject = c_lpaNULL;
        entry->Strike = c_lpaNULL;
    }
    return entry;
}

void ExclusionEntry_Destroy(ExclusionEntry_t* entry) {
    if (entry) {
        free(entry);
    }
}

ExclusionEntry_t* ExclusionEntry_Clone(const ExclusionEntry_t* entry) {
    if (!entry) return NULL;

    ExclusionEntry_t* clone = ExclusionEntry_Create();
    if (clone) {
        memcpy(clone, entry, sizeof(ExclusionEntry_t));
    }
    return clone;
}

// =============================================================================
// Permission Implementation
// =============================================================================

Permission_t* Permission_Create(uint32_t id) {
    Permission_t* permission = (Permission_t*)malloc(sizeof(Permission_t));
    if (permission) {
        permission->Id = id;
        permission->ActivationDateTime = 0;      // 0 = always active
        permission->DeactivationDateTime = 0;    // 0 = never expires
        permission->PermissionEntryList = Vector_Create(10);
        permission->ExclusionEntryList = Vector_Create(10);
    }
    return permission;
}

void Permission_Destroy(Permission_t* permission) {
    if (!permission) return;

    // Free all permission entries
    if (permission->PermissionEntryList) {
        for (int i = 0; i < permission->PermissionEntryList->count; i++) {
            PermissionEntry_t* entry = (PermissionEntry_t*)permission->PermissionEntryList->data[i];
            PermissionEntry_Destroy(entry);
        }
        Vector_Destroy(permission->PermissionEntryList);
    }

    // Free all exclusion entries
    if (permission->ExclusionEntryList) {
        for (int i = 0; i < permission->ExclusionEntryList->count; i++) {
            ExclusionEntry_t* entry = (ExclusionEntry_t*)permission->ExclusionEntryList->data[i];
            ExclusionEntry_Destroy(entry);
        }
        Vector_Destroy(permission->ExclusionEntryList);
    }

    free(permission);
}

// =============================================================================
// Permission Entry Management
// =============================================================================

void Permission_AddEntry(Permission_t* permission, PermissionEntry_t* entry) {
    if (permission && permission->PermissionEntryList && entry) {
        Vector_Add(permission->PermissionEntryList, entry);
    }
}

void Permission_RemoveEntry(Permission_t* permission, int index) {
    if (permission && permission->PermissionEntryList) {
        if (index >= 0 && index < permission->PermissionEntryList->count) {
            PermissionEntry_t* entry = (PermissionEntry_t*)permission->PermissionEntryList->data[index];
            PermissionEntry_Destroy(entry);
            Vector_RemoveAt(permission->PermissionEntryList, index);
        }
    }
}

void Permission_ClearEntries(Permission_t* permission) {
    if (permission && permission->PermissionEntryList) {
        for (int i = 0; i < permission->PermissionEntryList->count; i++) {
            PermissionEntry_t* entry = (PermissionEntry_t*)permission->PermissionEntryList->data[i];
            PermissionEntry_Destroy(entry);
        }
        Vector_Clear(permission->PermissionEntryList);
    }
}

PermissionEntry_t* Permission_GetEntry(Permission_t* permission, int index) {
    if (permission && permission->PermissionEntryList) {
        if (index >= 0 && index < permission->PermissionEntryList->count) {
            return (PermissionEntry_t*)permission->PermissionEntryList->data[index];
        }
    }
    return NULL;
}

int Permission_GetEntryCount(Permission_t* permission) {
    if (permission && permission->PermissionEntryList) {
        return permission->PermissionEntryList->count;
    }
    return 0;
}

// =============================================================================
// Exclusion Entry Management
// =============================================================================

void Permission_AddExclusion(Permission_t* permission, ExclusionEntry_t* exclusion) {
    if (permission && permission->ExclusionEntryList && exclusion) {
        Vector_Add(permission->ExclusionEntryList, exclusion);
    }
}

void Permission_RemoveExclusion(Permission_t* permission, int index) {
    if (permission && permission->ExclusionEntryList) {
        if (index >= 0 && index < permission->ExclusionEntryList->count) {
            ExclusionEntry_t* entry = (ExclusionEntry_t*)permission->ExclusionEntryList->data[index];
            ExclusionEntry_Destroy(entry);
            Vector_RemoveAt(permission->ExclusionEntryList, index);
        }
    }
}

void Permission_ClearExclusions(Permission_t* permission) {
    if (permission && permission->ExclusionEntryList) {
        for (int i = 0; i < permission->ExclusionEntryList->count; i++) {
            ExclusionEntry_t* entry = (ExclusionEntry_t*)permission->ExclusionEntryList->data[i];
            ExclusionEntry_Destroy(entry);
        }
        Vector_Clear(permission->ExclusionEntryList);
    }
}

ExclusionEntry_t* Permission_GetExclusion(Permission_t* permission, int index) {
    if (permission && permission->ExclusionEntryList) {
        if (index >= 0 && index < permission->ExclusionEntryList->count) {
            return (ExclusionEntry_t*)permission->ExclusionEntryList->data[index];
        }
    }
    return NULL;
}

int Permission_GetExclusionCount(Permission_t* permission) {
    if (permission && permission->ExclusionEntryList) {
        return permission->ExclusionEntryList->count;
    }
    return 0;
}

// =============================================================================
// Permission Evaluation Functions
// =============================================================================

int Permission_IsActive(Permission_t* permission, time_t current_time) {
    if (!permission) return 0;

    // Check activation time (0 = always active)
    if (permission->ActivationDateTime > 0) {
        if ((uint64_t)current_time < permission->ActivationDateTime) {
            return 0;  // Not yet active
        }
    }

    // Check deactivation time (0 = never expires)
    if (permission->DeactivationDateTime > 0) {
        if ((uint64_t)current_time >= permission->DeactivationDateTime) {
            return 0;  // Expired
        }
    }

    return 1;  // Active
}

PermissionEntry_t* Permission_FindEntryForAccessObject(Permission_t* permission, LPA_t access_object) {
    if (!permission || !permission->PermissionEntryList) return NULL;

    for (int i = 0; i < permission->PermissionEntryList->count; i++) {
        PermissionEntry_t* entry = (PermissionEntry_t*)permission->PermissionEntryList->data[i];
        if (LPA_Equals(&entry->AccessObject, &access_object)) {
            return entry;
        }
    }

    return NULL;
}

int Permission_IsExcluded(Permission_t* permission, LPA_t access_object) {
    if (!permission || !permission->ExclusionEntryList) return 0;

    for (int i = 0; i < permission->ExclusionEntryList->count; i++) {
        ExclusionEntry_t* entry = (ExclusionEntry_t*)permission->ExclusionEntryList->data[i];
        if (LPA_Equals(&entry->AccessObject, &access_object)) {
            return 1;  // Excluded
        }
    }

    return 0;  // Not excluded
}

int Permission_EvaluateAccess(Permission_t* permission, LPA_t access_object,
                               time_t current_time, uint32_t holiday_types) {
    if (!permission) return 0;

    // Step 1: Check if permission is active
    if (!Permission_IsActive(permission, current_time)) {
        return -1;  // Permission not active
    }

    // Step 2: Check for explicit exclusion (always denies)
    if (Permission_IsExcluded(permission, access_object)) {
        return 0;  // Explicitly denied
    }

    // Step 3: Find matching permission entry
    PermissionEntry_t* entry = Permission_FindEntryForAccessObject(permission, access_object);
    if (!entry) {
        return 0;  // Not in permission list
    }

    // Step 4: Check timezone restriction (if specified)
    // Note: TimeZone evaluation would be done by calling code
    // This function just indicates if the entry exists

    return 1;  // Access granted
}
