#ifndef ACCESS_LOGIC_SDK_H
#define ACCESS_LOGIC_SDK_H

#include "../sdk_modules/common/sdk_types.h"
#include "../sdk_modules/permissions/permission.h"
#include "../sdk_modules/timezones/timezone.h"
#include "../sdk_modules/readers/reader.h"
#include "access_logic.h"

/**
 * Enhanced Access Logic with Full SDK Integration
 *
 * This module provides production-ready access control using:
 * - Permissions for fine-grained access control
 * - TimeZones for schedule-based restrictions
 * - Holidays for special day handling
 * - Relays for physical access control
 * - Readers for card/PIN validation
 */

// =============================================================================
// Initialization & Shutdown
// =============================================================================

/**
 * Initialize enhanced access logic with SDK integration
 */
ErrorCode_t AccessLogic_SDK_Initialize(void);

/**
 * Shutdown and cleanup
 */
void AccessLogic_SDK_Shutdown(void);

// =============================================================================
// Permission Management
// =============================================================================

/**
 * Add a permission to the access control system
 */
ErrorCode_t AccessLogic_SDK_AddPermission(Permission_t* permission);

/**
 * Find a permission by ID
 */
Permission_t* AccessLogic_SDK_FindPermission(uint32_t permission_id);

// =============================================================================
// TimeZone Management
// =============================================================================

/**
 * Add a timezone to the access control system
 */
ErrorCode_t AccessLogic_SDK_AddTimeZone(TimeZone_t* timezone);

/**
 * Find a timezone by ID
 */
TimeZone_t* AccessLogic_SDK_FindTimeZone(uint16_t timezone_id);

// =============================================================================
// Access Decision Logic
// =============================================================================

/**
 * Process card read with full SDK integration
 *
 * @param card_number Card number presented
 * @param permission_id Permission ID associated with card
 * @param reader_lpa Reader where card was presented
 * @param relay_lpa Relay to control if access granted
 * @return Access decision with grant/deny and reason
 */
AccessLogicResult_t AccessLogic_SDK_ProcessCardRead(
    uint32_t card_number,
    uint32_t permission_id,
    LPA_t reader_lpa,
    LPA_t relay_lpa
);

/**
 * Simplified access decision for backward compatibility
 *
 * @param card_number Card number presented
 * @param door_number Door number (legacy interface)
 * @return Access decision
 */
AccessLogicResult_t AccessLogic_SDK_ProcessCardRead_Simple(
    uint32_t card_number,
    uint8_t door_number
);

// =============================================================================
// Reader Integration
// =============================================================================

/**
 * Set reader mode and update indication
 *
 * @param reader_lpa Reader LPA
 * @param mode New reader mode
 * @return ErrorCode_OK on success
 */
ErrorCode_t AccessLogic_SDK_SetReaderMode(LPA_t reader_lpa, ReaderMode_t mode);

// =============================================================================
// Event Generation
// =============================================================================

/**
 * Generate and publish access event
 *
 * @param decision Access decision to generate event from
 */
void AccessLogic_SDK_GenerateAccessEvent(AccessLogicResult_t* decision);

#endif // ACCESS_LOGIC_SDK_H
