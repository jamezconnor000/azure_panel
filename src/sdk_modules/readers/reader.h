#ifndef SDK_READER_H
#define SDK_READER_H

#include "../common/sdk_types.h"
#include "../../../include/osdp_types.h"
#include <stdint.h>
#include <stdbool.h>

/*
 * Azure Access Technology SDK - Reader Module
 * Based on Reader.h, ReaderControl.h, ReaderIndication.h,
 * LEDConfig.h, BuzzerConfig.h documentation
 */

// =============================================================================
// Reader Mode Constants
// =============================================================================

typedef enum {
    ReaderMode_Unknown = 255,
    ReaderMode_Locked = 0,              // No access
    ReaderMode_CardOnly = 1,            // Card required
    ReaderMode_CardAndPin = 2,          // Card + PIN required
    ReaderMode_PinOnly = 3,             // PIN only
    ReaderMode_Unlocked = 4,            // Free access (REX active)
    ReaderMode_CardOrPin = 5,           // Card OR PIN
    ReaderMode_CredentialOrPin = 6,     // Credential OR PIN
    ReaderMode_CredentialAndPin = 7,    // Credential + PIN
    ReaderMode_PinAndCard = 8,          // PIN first, then card
    ReaderMode_SiteCode = 9,            // Site code required
    ReaderMode_SiteCodeAndPin = 10      // Site code + PIN
} ReaderMode_t;

// =============================================================================
// Reader Flags
// =============================================================================

typedef enum {
    ReaderFlags_None = 0x00000000,
    ReaderFlags_APBEnabled = 0x00000001,        // Anti-passback enabled
    ReaderFlags_SupervisedInput = 0x00000002,   // Supervised input monitoring
    ReaderFlags_REXEnabled = 0x00000004,        // Request to exit enabled
    ReaderFlags_TwoPersonRule = 0x00000008,     // Requires two valid cards
    ReaderFlags_EscortRequired = 0x00000010,    // Requires escort
    ReaderFlags_DiddleCard = 0x00000020,        // Detect diddle/repeated swipes
    ReaderFlags_ExtendedAccess = 0x00000040,    // Extended access time
    ReaderFlags_PINMandatory = 0x00000080,      // PIN always required
    ReaderFlags_DisableLED = 0x00000100,        // Disable LED output
    ReaderFlags_DisableBuzzer = 0x00000200,     // Disable buzzer
    ReaderFlags_ThreatLevel1 = 0x00001000,      // Threat level flags
    ReaderFlags_ThreatLevel2 = 0x00002000,
    ReaderFlags_ThreatLevel3 = 0x00004000,
    ReaderFlags_ThreatLevel4 = 0x00008000
} ReaderFlags_t;

// =============================================================================
// Reader Indication States
// =============================================================================

typedef enum {
    ReaderIndicationState_Unlocked = 0,
    ReaderIndicationState_Locked = 1,
    ReaderIndicationState_Card = 2,
    ReaderIndicationState_CardAndPin = 3,
    ReaderIndicationState_PinOnly = 4,
    ReaderIndicationState_CardOrPin = 5,
    ReaderIndicationState_Grant = 6,
    ReaderIndicationState_Deny = 7,
    ReaderIndicationState_Echo = 8,
    ReaderIndicationState_DoorRelease = 9,
    ReaderIndicationState_HeldOpenAlarm = 10,
    ReaderIndicationState_ForceOpenAlarm = 11,
    ReaderIndicationState_Tamper = 12,
    ReaderIndicationState_APBViolation = 13,
    ReaderIndicationState_PINEcho = 14,
    ReaderIndicationState_TimeExpired = 15,
    ReaderIndicationState_TwoPersonRule = 16,
    ReaderIndicationState_EscortRequired = 17,
    ReaderIndicationState_Offline = 18,
    ReaderIndicationState_Online = 19,
    ReaderIndicationState_Command = 20,
    ReaderIndicationState_HostAcc = 21,
    ReaderIndicationState_Fire = 22,
    ReaderIndicationState_Security = 23,
    ReaderIndicationState_Threat = 24
} ReaderIndicationState_t;

// =============================================================================
// LED Configuration
// =============================================================================

typedef enum {
    LEDId_Red = 0,
    LEDId_Yellow = 1,
    LEDId_Green = 2
} LEDId_t;

// Note: LEDColor_t is defined in sdk_types.h
// LEDColor_Off = 0, LEDColor_Red = 1, LEDColor_Green = 2, LEDColor_Amber = 3, LEDColor_Blue = 4

typedef struct {
    LPA_t Id;                       // LED Config LPA
    LEDId_t LEDId;                  // Which LED (Red/Yellow/Green)
    uint8_t CancelTemp;             // Cancel temporary LED state
    uint16_t OnTime;                // On time in 100ms units
    uint16_t OffTime;               // Off time in 100ms units
    LEDColor_t OnColor;             // Color when on
    LEDColor_t OffColor;            // Color when off (for blinking)
} LEDConfig_t;

// LED Config Functions
LEDConfig_t* LEDConfig_Create(LPA_t id);
void LEDConfig_Destroy(LEDConfig_t* config);

// =============================================================================
// Buzzer Configuration
// =============================================================================

typedef struct {
    LPA_t Id;                       // Buzzer Config LPA
    uint8_t Tone;                   // 0=no tone, 1=off, 2=default
    uint16_t OnTime;                // On time in 100ms units
    uint16_t OffTime;               // Off time in 100ms units
    uint8_t Count;                  // Number of beeps (0=continuous)
} BuzzerConfig_t;

// Buzzer Config Functions
BuzzerConfig_t* BuzzerConfig_Create(LPA_t id);
void BuzzerConfig_Destroy(BuzzerConfig_t* config);

// =============================================================================
// Reader Indication Configuration
// =============================================================================

#define MAX_INDICATION_CONFIGS 8

typedef struct {
    ReaderIndicationState_t State;  // Which state this configures
    LPA_t Configs[MAX_INDICATION_CONFIGS];  // Up to 8 LED/Buzzer configs
} IndicationConfig_t;

typedef struct {
    LPA_t Id;                       // Reader Indication LPA
    IndicationConfig_t States[25];  // Config for each of 25 states
    int ConfigCount;
} ReaderIndication_t;

// Reader Indication Functions
ReaderIndication_t* ReaderIndication_Create(LPA_t id);
void ReaderIndication_Destroy(ReaderIndication_t* indication);
void ReaderIndication_SetState(ReaderIndication_t* indication, ReaderIndicationState_t state, LPA_t* configs, int count);
IndicationConfig_t* ReaderIndication_GetState(ReaderIndication_t* indication, ReaderIndicationState_t state);

// =============================================================================
// Reader Structure
// =============================================================================

typedef struct {
    LPA_t Id;                       // Reader LPA
    LPA_t AccessPoint;              // Associated access point
    uint32_t CipherCode;            // Encryption code
    uint16_t ScriptId;              // Custom script ID
    uint32_t Flags;                 // ReaderFlags_t bit field
    uint16_t TimedAPB;              // Timed anti-passback (minutes)
    uint16_t TimedAPBEx;            // Extended timed APB (seconds)
    uint8_t ThreatLevel;            // Current threat level (0-4)
    uint16_t NextTO;                // Next timeout (seconds)
    uint8_t SignalType;             // Signal type (SignalType_t: Wiegand, OSDP, etc.)
    uint8_t Direction;              // Reader direction (IN/OUT)
    uint8_t NumOfCards;             // Cards required (multi-swipe)
    ReaderMode_t InitMode;          // Initial mode on startup
    ReaderMode_t OfflineMode;       // Mode when offline
    uint16_t UseLimit;              // Use count limit
    uint16_t CardFormatListId;      // Card format list ID
    uint16_t CtrlTimeZone;          // Control timezone
    LPA_t SmartCardFormat;          // Smart card format
    ReaderMode_t TZStartMode;       // Mode when timezone starts
    ReaderMode_t TZEndMode;         // Mode when timezone ends
    uint8_t DiddleThreshold;        // Diddle detection threshold
    LPA_t Indication;               // ReaderIndication LPA
    ReaderMode_t UnlockedMode;      // Mode when unlocked
    ReaderMode_t LockedMode;        // Mode when locked
    uint16_t LockTimeout;           // Auto-lock timeout (seconds)
    LPA_t DisableReaderToggle;      // Toggle to disable reader
    uint16_t CommandTO;             // Command timeout (ms)
    uint8_t DiddleLockoutTO;        // Diddle lockout timeout (seconds)
    uint8_t PINTimeout;             // PIN entry timeout (seconds)

    // Runtime state
    ReaderMode_t CurrentMode;
    time_t LastActivity;

    // OSDP support (NULL if Wiegand)
    void* osdp_handle;              // OSDP_Reader_t* (opaque pointer)
} Reader_t;

// Reader Standard Functions
Reader_t* Reader_Create(LPA_t id);
void Reader_Destroy(Reader_t* reader);

// =============================================================================
// Reader Management Functions
// =============================================================================

/**
 * Add reader configuration
 */
ErrorCode_t Reader_Add(Reader_t* reader);

/**
 * Get reader by ID
 */
Reader_t* Reader_Get(LPA_t id);

/**
 * Update reader configuration
 */
ErrorCode_t Reader_Update(Reader_t* reader);

/**
 * Delete reader
 */
ErrorCode_t Reader_Delete(LPA_t id);

// =============================================================================
// Reader Control Functions
// =============================================================================

/**
 * Set reader mode
 */
ErrorCode_t Reader_SetMode(LPA_t id, ReaderMode_t mode);

/**
 * Get current reader mode
 */
ReaderMode_t Reader_GetMode(LPA_t id);

/**
 * Lock reader (set to Locked mode)
 */
ErrorCode_t Reader_Lock(LPA_t id);

/**
 * Unlock reader (set to Unlocked mode)
 */
ErrorCode_t Reader_Unlock(LPA_t id);

/**
 * Set reader to Card Only mode
 */
ErrorCode_t Reader_SetCardOnly(LPA_t id);

/**
 * Set reader to Card And PIN mode
 */
ErrorCode_t Reader_SetCardAndPIN(LPA_t id);

// =============================================================================
// Reader Indication Functions
// =============================================================================

/**
 * Set reader visual/audio indication state
 */
ErrorCode_t Reader_SetIndicationState(LPA_t reader_id, ReaderIndicationState_t state);

/**
 * Apply LED pattern to reader
 */
void Reader_ApplyLEDPattern(LPA_t reader_id, LEDConfig_t* config);

/**
 * Apply buzzer pattern to reader
 */
void Reader_ApplyBuzzerPattern(LPA_t reader_id, BuzzerConfig_t* config);

// =============================================================================
// OSDP Reader Functions
// =============================================================================

/**
 * Initialize OSDP reader
 *
 * @param reader_id Reader LPA
 * @param config OSDP configuration
 * @param port Serial port path (e.g., "/dev/ttyUSB0")
 * @return ErrorCode_OK on success
 */
ErrorCode_t Reader_InitOSDP(LPA_t reader_id, const OSDP_Config_t* config, const char* port);

/**
 * Poll OSDP reader for events
 *
 * @param reader_id Reader LPA
 * @return ErrorCode_OK on success
 */
ErrorCode_t Reader_PollOSDP(LPA_t reader_id);

/**
 * Set OSDP reader LED
 *
 * @param reader_id Reader LPA
 * @param led_number LED number (0-based)
 * @param color LED color
 * @return ErrorCode_OK on success
 */
ErrorCode_t Reader_SetOSDPLED(LPA_t reader_id, uint8_t led_number, OSDP_LED_Color_t color);

/**
 * Activate OSDP reader buzzer
 *
 * @param reader_id Reader LPA
 * @param duration Duration in 100ms units
 * @return ErrorCode_OK on success
 */
ErrorCode_t Reader_OSDPBeep(LPA_t reader_id, uint8_t duration);

/**
 * Check if OSDP reader is online
 *
 * @param reader_id Reader LPA
 * @return true if online, false otherwise
 */
bool Reader_IsOSDPOnline(LPA_t reader_id);

// =============================================================================
// Testing Functions
// =============================================================================

/**
 * Simulate card presentation
 */
ErrorCode_t Reader_PostCard(LPA_t reader_id, uint64_t card_number);

/**
 * Simulate keypad entry
 */
ErrorCode_t Reader_PostKey(LPA_t reader_id, char key);

/**
 * Simulate PIN entry
 */
ErrorCode_t Reader_PostPIN(LPA_t reader_id, const char* pin);

#endif // SDK_READER_H
