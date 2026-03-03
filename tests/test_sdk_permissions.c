#include <stdio.h>
#include <assert.h>
#include <time.h>
#include "../src/sdk_modules/permissions/permission.h"
#include "../src/sdk_modules/common/sdk_types.h"

int main() {
    printf("=== SDK Permissions Module Test ===\n\n");

    // Create a permission
    Permission_t* perm = Permission_Create(1);
    assert(perm != NULL);
    printf("✓ Created Permission ID=1\n");

    // Set activation/deactivation times
    perm->ActivationDateTime = 0;  // Always active
    perm->DeactivationDateTime = 0;  // Never expires
    printf("✓ Set as always active, never expires\n");

    // Create permission entries
    PermissionEntry_t* entry1 = PermissionEntry_Create();
    entry1->AccessObject.type = LPAType_Reader;
    entry1->AccessObject.id = 1;
    entry1->AccessObject.node_id = 0;
    entry1->TimeZone = 2;  // TimeZoneConsts_Always
    entry1->Strike.type = LPAType_Relay;
    entry1->Strike.id = 1;
    entry1->Strike.node_id = 0;
    Permission_AddEntry(perm, entry1);
    printf("✓ Added entry for Reader 1 with TimeZone Always\n");

    PermissionEntry_t* entry2 = PermissionEntry_Create();
    entry2->AccessObject.type = LPAType_Reader;
    entry2->AccessObject.id = 2;
    entry2->AccessObject.node_id = 0;
    entry2->TimeZone = 1;  // TimeZoneConsts_Never
    Permission_AddEntry(perm, entry2);
    printf("✓ Added entry for Reader 2 with TimeZone Never\n");

    // Create exclusion entry
    ExclusionEntry_t* exclusion = ExclusionEntry_Create();
    exclusion->AccessObject.type = LPAType_Reader;
    exclusion->AccessObject.id = 3;
    exclusion->AccessObject.node_id = 0;
    Permission_AddExclusion(perm, exclusion);
    printf("✓ Added exclusion for Reader 3\n");

    // Test permission evaluation
    printf("\n--- Permission Evaluation ---\n");

    // Check if permission is active
    time_t now = time(NULL);
    int active = Permission_IsActive(perm, now);
    printf("Permission is %s\n", active ? "ACTIVE ✓" : "INACTIVE ✗");
    assert(active == 1);

    // Check entry count
    int entry_count = Permission_GetEntryCount(perm);
    printf("Permission has %d entries\n", entry_count);
    assert(entry_count == 2);

    int exclusion_count = Permission_GetExclusionCount(perm);
    printf("Permission has %d exclusions\n", exclusion_count);
    assert(exclusion_count == 1);

    // Find entry for Reader 1
    LPA_t reader1 = {.type = LPAType_Reader, .id = 1, .node_id = 0};
    PermissionEntry_t* found = Permission_FindEntryForAccessObject(perm, reader1);
    printf("Entry for Reader 1: %s (TimeZone=%d)\n",
           found ? "FOUND ✓" : "NOT FOUND ✗",
           found ? found->TimeZone : 0);
    assert(found != NULL);
    assert(found->TimeZone == 2);

    // Check if Reader 3 is excluded
    LPA_t reader3 = {.type = LPAType_Reader, .id = 3, .node_id = 0};
    int excluded = Permission_IsExcluded(perm, reader3);
    printf("Reader 3 is %s\n", excluded ? "EXCLUDED ✓" : "ALLOWED ✗");
    assert(excluded == 1);

    // Evaluate access for Reader 1 (should grant)
    int access = Permission_EvaluateAccess(perm, reader1, now, 0);
    printf("Access for Reader 1: %s\n", access == 1 ? "GRANTED ✓" : "DENIED ✗");
    assert(access == 1);

    // Evaluate access for Reader 3 (should deny - excluded)
    access = Permission_EvaluateAccess(perm, reader3, now, 0);
    printf("Access for Reader 3: %s (excluded)\n", access == 0 ? "DENIED ✓" : "GRANTED ✗");
    assert(access == 0);

    // Test permission entry removal
    printf("\n--- Entry Management ---\n");
    Permission_RemoveEntry(perm, 0);
    entry_count = Permission_GetEntryCount(perm);
    printf("After removing entry 0: %d entries remaining\n", entry_count);
    assert(entry_count == 1);

    // Clean up
    Permission_Destroy(perm);
    printf("\n✓ All tests passed!\n");

    return 0;
}
