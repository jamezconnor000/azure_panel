#ifndef SDK_DATABASE_H
#define SDK_DATABASE_H

#include "sdk_types.h"
#include "../permissions/permission.h"
#include "../timezones/timezone.h"
#include "../relays/relay.h"
#include "../readers/reader.h"
#include "../group_lists/group_list.h"
#include "../holidays/holiday.h"
#include "../access_points/access_point.h"
#include "../areas/area.h"
#include "../card_formats/card_format.h"
#include <sqlite3.h>

/**
 * SDK Database Module
 *
 * Provides persistence for all SDK modules using SQLite3.
 * Each module has CRUD operations (Create, Read, Update, Delete).
 */

// =============================================================================
// Database Initialization
// =============================================================================

/**
 * Initialize database connection
 *
 * @param db_path Path to SQLite database file
 * @return ErrorCode_OK on success
 */
ErrorCode_t SDK_Database_Initialize(const char* db_path);

/**
 * Close database connection
 */
void SDK_Database_Shutdown(void);

/**
 * Get current database connection (for custom queries)
 */
sqlite3* SDK_Database_GetConnection(void);

// =============================================================================
// Permission Database Operations
// =============================================================================

/**
 * Save permission to database
 *
 * @param permission Permission object to save
 * @return ErrorCode_OK on success
 */
ErrorCode_t Permission_SaveToDB(const Permission_t* permission);

/**
 * Load permission from database by ID
 *
 * @param id Permission ID
 * @return Permission object or NULL if not found
 */
Permission_t* Permission_LoadFromDB(uint32_t id);

/**
 * Load all permissions from database
 *
 * @param out_permissions Array to store permission pointers
 * @param max_count Maximum number of permissions to load
 * @return Number of permissions loaded
 */
int Permission_LoadAllFromDB(Permission_t** out_permissions, int max_count);

/**
 * Update permission in database
 *
 * @param permission Permission object with updated data
 * @return ErrorCode_OK on success
 */
ErrorCode_t Permission_UpdateInDB(const Permission_t* permission);

/**
 * Delete permission from database
 *
 * @param id Permission ID to delete
 * @return ErrorCode_OK on success
 */
ErrorCode_t Permission_DeleteFromDB(uint32_t id);

// =============================================================================
// TimeZone Database Operations
// =============================================================================

/**
 * Save timezone to database
 *
 * @param timezone TimeZone object to save
 * @return ErrorCode_OK on success
 */
ErrorCode_t TimeZone_SaveToDB(const TimeZone_t* timezone);

/**
 * Load timezone from database by ID
 *
 * @param id TimeZone ID
 * @return TimeZone object or NULL if not found
 */
TimeZone_t* TimeZone_LoadFromDB(uint16_t id);

/**
 * Load all timezones from database
 *
 * @param out_timezones Array to store timezone pointers
 * @param max_count Maximum number of timezones to load
 * @return Number of timezones loaded
 */
int TimeZone_LoadAllFromDB(TimeZone_t** out_timezones, int max_count);

/**
 * Update timezone in database
 *
 * @param timezone TimeZone object with updated data
 * @return ErrorCode_OK on success
 */
ErrorCode_t TimeZone_UpdateInDB(const TimeZone_t* timezone);

/**
 * Delete timezone from database
 *
 * @param id TimeZone ID to delete
 * @return ErrorCode_OK on success
 */
ErrorCode_t TimeZone_DeleteFromDB(uint16_t id);

// =============================================================================
// Relay Database Operations
// =============================================================================

/**
 * Save relay to database
 *
 * @param relay Relay object to save
 * @return ErrorCode_OK on success
 */
ErrorCode_t Relay_SaveToDB(const Relay_t* relay);

/**
 * Load relay from database by LPA
 *
 * @param lpa Relay LPA
 * @return Relay object or NULL if not found
 */
Relay_t* Relay_LoadFromDB(LPA_t lpa);

/**
 * Load all relays from database
 *
 * @param out_relays Array to store relay pointers
 * @param max_count Maximum number of relays to load
 * @return Number of relays loaded
 */
int Relay_LoadAllFromDB(Relay_t** out_relays, int max_count);

/**
 * Update relay in database
 *
 * @param relay Relay object with updated data
 * @return ErrorCode_OK on success
 */
ErrorCode_t Relay_UpdateInDB(const Relay_t* relay);

/**
 * Delete relay from database
 *
 * @param lpa Relay LPA to delete
 * @return ErrorCode_OK on success
 */
ErrorCode_t Relay_DeleteFromDB(LPA_t lpa);

/**
 * Save relay link to database
 *
 * @param link RelayLink object to save
 * @return ErrorCode_OK on success
 */
ErrorCode_t RelayLink_SaveToDB(const RelayLink_t* link);

/**
 * Load all relay links from database
 *
 * @param out_links Array to store relay link pointers
 * @param max_count Maximum number of links to load
 * @return Number of links loaded
 */
int RelayLink_LoadAllFromDB(RelayLink_t** out_links, int max_count);

// =============================================================================
// Reader Database Operations
// =============================================================================

/**
 * Save reader to database
 *
 * @param reader Reader object to save
 * @return ErrorCode_OK on success
 */
ErrorCode_t Reader_SaveToDB(const Reader_t* reader);

/**
 * Load reader from database by LPA
 *
 * @param lpa Reader LPA
 * @return Reader object or NULL if not found
 */
Reader_t* Reader_LoadFromDB(LPA_t lpa);

/**
 * Load all readers from database
 *
 * @param out_readers Array to store reader pointers
 * @param max_count Maximum number of readers to load
 * @return Number of readers loaded
 */
int Reader_LoadAllFromDB(Reader_t** out_readers, int max_count);

/**
 * Update reader in database
 *
 * @param reader Reader object with updated data
 * @return ErrorCode_OK on success
 */
ErrorCode_t Reader_UpdateInDB(const Reader_t* reader);

/**
 * Delete reader from database
 *
 * @param lpa Reader LPA to delete
 * @return ErrorCode_OK on success
 */
ErrorCode_t Reader_DeleteFromDB(LPA_t lpa);

// =============================================================================
// GroupList Database Operations
// =============================================================================

/**
 * Save group list to database
 *
 * @param group_list GroupList object to save
 * @return ErrorCode_OK on success
 */
ErrorCode_t GroupList_SaveToDB(const GroupList_t* group_list);

/**
 * Load group list from database by LPA
 *
 * @param lpa GroupList LPA
 * @return GroupList object or NULL if not found
 */
GroupList_t* GroupList_LoadFromDB(LPA_t lpa);

/**
 * Load all group lists from database
 *
 * @param out_lists Array to store group list pointers
 * @param max_count Maximum number of lists to load
 * @return Number of lists loaded
 */
int GroupList_LoadAllFromDB(GroupList_t** out_lists, int max_count);

/**
 * Delete group list from database
 *
 * @param lpa GroupList LPA to delete
 * @return ErrorCode_OK on success
 */
ErrorCode_t GroupList_DeleteFromDB(LPA_t lpa);

// =============================================================================
// Holiday Database Operations
// =============================================================================

/**
 * Save holiday to database
 *
 * @param date Holiday date (YYYYMMDD format)
 * @param types Holiday types bitmask
 * @return ErrorCode_OK on success
 */
ErrorCode_t Holiday_SaveToDB(uint32_t date, uint32_t types);

/**
 * Load all holidays from database
 *
 * @return Number of holidays loaded into in-memory cache
 */
int Holiday_LoadAllFromDB(void);

/**
 * Delete holiday from database
 *
 * @param date Holiday date to delete
 * @return ErrorCode_OK on success
 */
ErrorCode_t Holiday_DeleteFromDB(uint32_t date);

// =============================================================================
// Bulk Operations
// =============================================================================

/**
 * Load all SDK configuration from database
 *
 * This function loads all permissions, timezones, relays, readers,
 * group lists, and holidays from the database into memory.
 *
 * @return ErrorCode_OK on success
 */
ErrorCode_t SDK_LoadAllFromDatabase(void);

/**
 * Save all SDK configuration to database
 *
 * This function saves all in-memory SDK objects to the database.
 *
 * @return ErrorCode_OK on success
 */
ErrorCode_t SDK_SaveAllToDatabase(void);

// =============================================================================
// Access Point Database Operations
// =============================================================================

ErrorCode_t AccessPoint_SaveToDB(const AccessPoint_t* access_point);
AccessPoint_t* AccessPoint_LoadFromDB(uint32_t id);
int AccessPoint_LoadAllFromDB(AccessPoint_t** out_access_points, int max_count);
ErrorCode_t AccessPoint_DeleteFromDB(uint32_t id);

// =============================================================================
// Area Database Operations
// =============================================================================

ErrorCode_t Area_SaveToDB(const Area_t* area);
Area_t* Area_LoadFromDB(uint32_t id);
int Area_LoadAllFromDB(Area_t** out_areas, int max_count);
ErrorCode_t Area_DeleteFromDB(uint32_t id);

// =============================================================================
// Card Format Database Operations
// =============================================================================

ErrorCode_t CardFormat_SaveToDB(const CardFormat_t* format);
CardFormat_t* CardFormat_LoadFromDB(uint8_t id);
int CardFormat_LoadAllFromDB(CardFormat_t** out_formats, int max_count);
ErrorCode_t CardFormat_DeleteFromDB(uint8_t id);

ErrorCode_t CardFormatList_SaveToDB(const CardFormatList_t* list);
CardFormatList_t* CardFormatList_LoadFromDB(uint8_t id);
ErrorCode_t CardFormatList_DeleteFromDB(uint8_t id);

#endif // SDK_DATABASE_H
