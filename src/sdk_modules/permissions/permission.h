#ifndef SDK_PERMISSION_H
#define SDK_PERMISSION_H

#include "../common/sdk_types.h"

/*
 * Azure Access Technology SDK - Permission Module
 * Based on Permission.h, PermissionEntry.h, ExclusionEntry.h documentation
 */

// =============================================================================
// Permission Entry Structure
// =============================================================================

/**
 * PermissionEntry - Links access objects to time zones with override flags
 *
 * Defines which access objects (readers, doors) a permission grants access to,
 * along with time restrictions and permission flag overrides.
 */
typedef struct {
    LPA_t AccessObject;                 // Reader, door, or area LPA
    LPA_t Strike;                       // Strike/relay to energize (0 = default)
    uint16_t TimeZone;                  // TimeZone ID controlling access
    uint32_t OverridePermissionFlagsMask;   // Bit field: which flags to override
    uint32_t OverridePermissionFlags;       // Bit field: override values
} PermissionEntry_t;

// PermissionEntry Standard Functions
PermissionEntry_t* PermissionEntry_Create(void);
void PermissionEntry_Destroy(PermissionEntry_t* entry);
PermissionEntry_t* PermissionEntry_Clone(const PermissionEntry_t* entry);

// =============================================================================
// Exclusion Entry Structure
// =============================================================================

/**
 * ExclusionEntry - Explicit denial for specific access objects
 *
 * Provides explicit DENY for specific access objects, overriding any
 * PermissionEntry grants. Used for temporary restrictions.
 */
typedef struct {
    LPA_t AccessObject;                 // Reader, door, or area to deny
    LPA_t Strike;                       // Strike ID (typically 0)
} ExclusionEntry_t;

// ExclusionEntry Standard Functions
ExclusionEntry_t* ExclusionEntry_Create(void);
void ExclusionEntry_Destroy(ExclusionEntry_t* entry);
ExclusionEntry_t* ExclusionEntry_Clone(const ExclusionEntry_t* entry);

// =============================================================================
// Permission Structure
// =============================================================================

/**
 * Permission - Collection of permission entries with activation dates
 *
 * Defines a complete permission set that can be assigned to cardholders.
 * Contains lists of granted and excluded access objects.
 */
typedef struct {
    uint32_t Id;                        // Permission ID
    uint64_t ActivationDateTime;        // Unix timestamp when permission becomes active
    uint64_t DeactivationDateTime;      // Unix timestamp when permission expires
    Vector_t* PermissionEntryList;      // List of PermissionEntry_t*
    Vector_t* ExclusionEntryList;       // List of ExclusionEntry_t*
} Permission_t;

// Permission Standard Functions
Permission_t* Permission_Create(uint32_t id);
void Permission_Destroy(Permission_t* permission);

// Permission Entry Management
void Permission_AddEntry(Permission_t* permission, PermissionEntry_t* entry);
void Permission_RemoveEntry(Permission_t* permission, int index);
void Permission_ClearEntries(Permission_t* permission);
PermissionEntry_t* Permission_GetEntry(Permission_t* permission, int index);
int Permission_GetEntryCount(Permission_t* permission);

// Exclusion Entry Management
void Permission_AddExclusion(Permission_t* permission, ExclusionEntry_t* exclusion);
void Permission_RemoveExclusion(Permission_t* permission, int index);
void Permission_ClearExclusions(Permission_t* permission);
ExclusionEntry_t* Permission_GetExclusion(Permission_t* permission, int index);
int Permission_GetExclusionCount(Permission_t* permission);

// =============================================================================
// Permission Evaluation Functions
// =============================================================================

/**
 * Check if permission is currently active (within activation/deactivation window)
 */
int Permission_IsActive(Permission_t* permission, time_t current_time);

/**
 * Find a PermissionEntry that matches the given access object
 * Returns NULL if not found
 */
PermissionEntry_t* Permission_FindEntryForAccessObject(Permission_t* permission, LPA_t access_object);

/**
 * Check if an access object is explicitly excluded
 * Returns 1 if excluded, 0 if not
 */
int Permission_IsExcluded(Permission_t* permission, LPA_t access_object);

/**
 * Evaluate permission for a given access object at current time
 *
 * Returns:
 *   1 = Access granted
 *   0 = Access denied (not in permission list, excluded, or time restriction)
 *  -1 = Permission not active (outside activation/deactivation window)
 */
int Permission_EvaluateAccess(Permission_t* permission, LPA_t access_object,
                               time_t current_time, uint32_t holiday_types);

// =============================================================================
// Permission Flag Constants
// =============================================================================

// Override flags for PermissionEntry
typedef enum {
    PermissionFlags_None = 0x00000000,
    PermissionFlags_APB = 0x00000001,           // Anti-passback
    PermissionFlags_TwoMan = 0x00000002,        // Two-person rule
    PermissionFlags_Escort = 0x00000004,        // Requires escort
    PermissionFlags_UseLimit = 0x00000008,      // Limited uses
    PermissionFlags_ExtendedGrant = 0x00000010, // Extended access time
    PermissionFlags_Trace = 0x00000020,         // Enable tracing/audit
    PermissionFlags_Disabled = 0x00000040,      // Temporarily disabled
} PermissionFlags_t;

#endif // SDK_PERMISSION_H
