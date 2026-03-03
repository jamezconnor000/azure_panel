/**
 * @file osdp_types.h
 * @brief OSDP (Open Supervised Device Protocol) Type Definitions
 *
 * Defines types and structures for OSDP reader communication.
 * Based on SIA OSDP v2.2 specification.
 */

#ifndef OSDP_TYPES_H
#define OSDP_TYPES_H

#include <stdint.h>
#include <stdbool.h>
#include "hal_types.h"

// =============================================================================
// Protocol Constants
// =============================================================================

#define OSDP_SOM                0x53    // Start of Message
#define OSDP_VERSION            0x02    // OSDP Version 2
#define OSDP_MAX_PACKET_SIZE    512     // Maximum packet size
#define OSDP_QUEUE_SIZE         64      // Event queue size

// =============================================================================
// Signal Types (extends Reader.SignalType field)
// =============================================================================

typedef enum {
    SignalType_None = 0,
    SignalType_Wiegand = 1,
    SignalType_OSDP = 2,
    SignalType_ClockData = 3,
    SignalType_RS485 = 4
} SignalType_t;

// =============================================================================
// OSDP Command Codes
// =============================================================================

typedef enum {
    OSDP_POLL      = 0x60,  // Poll
    OSDP_ID        = 0x61,  // ID Report Request
    OSDP_CAP       = 0x62,  // Device Capabilities Request
    OSDP_LSTAT     = 0x64,  // Local Status Request
    OSDP_ISTAT     = 0x65,  // Input Status Request
    OSDP_OSTAT     = 0x66,  // Output Status Request
    OSDP_RSTAT     = 0x67,  // Reader Status Request
    OSDP_OUT       = 0x68,  // Output Control
    OSDP_LED       = 0x69,  // LED Control
    OSDP_BUZ       = 0x6A,  // Buzzer Control
    OSDP_TEXT      = 0x6B,  // Text Output
    OSDP_COMSET    = 0x6E,  // Communication Configuration
    OSDP_KEYSET    = 0x75,  // Encryption Key Set
    OSDP_CHLNG     = 0x76,  // Challenge
    OSDP_SCRYPT    = 0x77,  // Server Cryptogram
    OSDP_ACURXSIZE = 0x7B,  // Max ACU Receive Size
    OSDP_MFG       = 0x80   // Manufacturer Specific
} OSDP_Command_t;

// =============================================================================
// OSDP Reply Codes
// =============================================================================

typedef enum {
    OSDP_ACK       = 0x40,  // Command Accepted
    OSDP_NAK       = 0x41,  // Command Not Accepted
    OSDP_PDID      = 0x45,  // PD ID Report
    OSDP_PDCAP     = 0x46,  // PD Capabilities
    OSDP_LSTATR    = 0x48,  // Local Status Report
    OSDP_ISTATR    = 0x49,  // Input Status Report
    OSDP_OSTATR    = 0x4A,  // Output Status Report
    OSDP_RSTATR    = 0x4B,  // Reader Status Report
    OSDP_RAW       = 0x50,  // Raw Card Data
    OSDP_FMT       = 0x51,  // Formatted Card Data
    OSDP_KEYPPAD   = 0x53,  // Keypad Data
    OSDP_COM       = 0x54,  // Communication Configuration Report
    OSDP_CCRYPT    = 0x76,  // Client Cryptogram
    OSDP_RMACK     = 0x77,  // RM ACU Receive Size
    OSDP_MFGREP    = 0x90,  // Manufacturer Specific Reply
    OSDP_BUSY      = 0x79,  // PD Busy
    OSDP_XRD       = 0xB1   // Extended Read
} OSDP_Reply_t;

// =============================================================================
// OSDP NAK Error Codes
// =============================================================================

typedef enum {
    OSDP_NAK_NONE          = 0x00,  // No error
    OSDP_NAK_MSG_CHK       = 0x01,  // Message check character error
    OSDP_NAK_CMD_LEN       = 0x02,  // Command length error
    OSDP_NAK_UNKNOWN_CMD   = 0x03,  // Unknown command code
    OSDP_NAK_SEQ_NUM       = 0x04,  // Unexpected sequence number
    OSDP_NAK_SC_UNSUP      = 0x05,  // Secure channel not supported
    OSDP_NAK_SC_COND       = 0x06,  // Secure channel condition error
    OSDP_NAK_BIO_TYPE      = 0x07,  // BIO type not supported
    OSDP_NAK_BIO_FMT       = 0x08   // BIO format not supported
} OSDP_NAK_Code_t;

// =============================================================================
// OSDP LED Colors
// =============================================================================

typedef enum {
    OSDP_LED_COLOR_NONE   = 0,
    OSDP_LED_COLOR_RED    = 1,
    OSDP_LED_COLOR_GREEN  = 2,
    OSDP_LED_COLOR_AMBER  = 3,
    OSDP_LED_COLOR_BLUE   = 4
} OSDP_LED_Color_t;

// =============================================================================
// OSDP Buzzer Tones
// =============================================================================

typedef enum {
    OSDP_BUZZER_NONE   = 0,
    OSDP_BUZZER_OFF    = 1,
    OSDP_BUZZER_ON     = 2
} OSDP_Buzzer_Tone_t;

// =============================================================================
// OSDP Card Formats
// =============================================================================

typedef enum {
    OSDP_CARD_FORMAT_RAW       = 0x01,  // Raw card data
    OSDP_CARD_FORMAT_WIEGAND   = 0x02,  // Wiegand format
    OSDP_CARD_FORMAT_ASCII     = 0x03   // ASCII data
} OSDP_Card_Format_t;

// =============================================================================
// OSDP Packet Structure
// =============================================================================

typedef struct {
    uint8_t som;                        // Start of Message (0x53)
    uint8_t addr;                       // PD Address (0-126, 127=broadcast)
    uint16_t len;                       // Packet length (includes header + data + crc)
    uint8_t ctrl;                       // Control byte (sequence + flags)
    uint8_t data[OSDP_MAX_PACKET_SIZE]; // Command/Reply data
    uint16_t crc;                       // CRC-16 checksum
} OSDP_Packet_t;

// =============================================================================
// OSDP Device Capabilities
// =============================================================================

typedef enum {
    OSDP_CAP_CONTACT_STATUS    = 1,   // Contact status monitoring
    OSDP_CAP_OUTPUT_CONTROL    = 2,   // Output control
    OSDP_CAP_LED_CONTROL       = 3,   // LED control
    OSDP_CAP_AUDIBLE_OUTPUT    = 4,   // Audible output (buzzer)
    OSDP_CAP_TEXT_OUTPUT       = 5,   // Text output
    OSDP_CAP_TIME_KEEPING      = 6,   // Time keeping
    OSDP_CAP_CHECK_CHARACTER   = 7,   // Check character support
    OSDP_CAP_COMM_SECURITY     = 8,   // Communication security
    OSDP_CAP_RECEIVE_BUFSIZE   = 9,   // Receive buffer size
    OSDP_CAP_LARGEST_MSG       = 10,  // Largest combined message
    OSDP_CAP_SMART_CARD        = 11,  // Smart card support
    OSDP_CAP_READERS           = 12,  // Number of readers
    OSDP_CAP_BIOMETRICS        = 13   // Biometric support
} OSDP_Capability_t;

typedef struct {
    uint8_t function_code;              // Capability function code
    uint8_t compliance;                 // Compliance level
    uint8_t num_items;                  // Number of items
} OSDP_PD_Capability_t;

// =============================================================================
// OSDP LED Control
// =============================================================================

typedef struct {
    uint8_t reader;                     // Reader number
    uint8_t led_number;                 // LED number (0-based)
    uint8_t temp_control;               // Temporary control code
    uint8_t temp_on_time;               // Temporary on time (100ms units)
    uint8_t temp_off_time;              // Temporary off time (100ms units)
    uint8_t temp_color;                 // Temporary color
    uint8_t perm_control;               // Permanent control code
    uint8_t perm_on_time;               // Permanent on time (100ms units)
    uint8_t perm_off_time;              // Permanent off time (100ms units)
    uint8_t perm_color;                 // Permanent color
} OSDP_LED_Cmd_t;

// =============================================================================
// OSDP Buzzer Control
// =============================================================================

typedef struct {
    uint8_t reader;                     // Reader number
    uint8_t tone_code;                  // Tone code
    uint8_t on_time;                    // On time (100ms units)
    uint8_t off_time;                   // Off time (100ms units)
    uint8_t count;                      // Repeat count (0 = infinite)
} OSDP_Buzzer_Cmd_t;

// =============================================================================
// OSDP Card Data
// =============================================================================

typedef struct {
    uint8_t reader;                     // Reader number
    uint8_t format;                     // Format code
    uint16_t bit_count;                 // Number of bits
    uint8_t data[64];                   // Card data (max 64 bytes)
} OSDP_Card_Data_t;

// =============================================================================
// OSDP Reader Configuration
// =============================================================================

typedef struct {
    uint8_t address;                    // PD address (0-126)
    uint32_t baud_rate;                 // Baud rate (9600, 19200, 38400, 115200)
    bool secure_channel;                // Use secure channel
    uint8_t scbk[16];                   // Secure Channel Base Key (128-bit)
    uint8_t poll_interval_ms;           // Poll interval in milliseconds
    uint8_t retry_count;                // Number of retries on failure
    uint16_t timeout_ms;                // Response timeout in milliseconds
} OSDP_Config_t;

// =============================================================================
// OSDP Device State
// =============================================================================

typedef enum {
    OSDP_STATE_INIT = 0,                // Initializing
    OSDP_STATE_IDLE,                    // Idle (not connected)
    OSDP_STATE_ONLINE,                  // Online (polling)
    OSDP_STATE_SECURE,                  // Secure channel established
    OSDP_STATE_ERROR,                   // Error state
    OSDP_STATE_OFFLINE                  // Offline
} OSDP_State_t;

// =============================================================================
// OSDP Event Types
// =============================================================================

typedef enum {
    OSDP_EVENT_CARD_READ = 0x01,        // Card read event
    OSDP_EVENT_KEYPRESS = 0x02,         // Keypress event
    OSDP_EVENT_INPUT_CHANGE = 0x03,     // Input status change
    OSDP_EVENT_OUTPUT_CHANGE = 0x04,    // Output status change
    OSDP_EVENT_TAMPER = 0x05,           // Tamper event
    OSDP_EVENT_POWER_FAIL = 0x06,       // Power failure
    OSDP_EVENT_COMM_ERROR = 0x07        // Communication error
} OSDP_Event_Type_t;

// =============================================================================
// OSDP Reader Handle
// =============================================================================

typedef struct OSDP_Reader OSDP_Reader_t;

struct OSDP_Reader {
    LPA_t lpa;                          // Reader LPA
    OSDP_Config_t config;               // Configuration
    OSDP_State_t state;                 // Current state
    uint8_t sequence;                   // Sequence number
    int fd;                             // File descriptor (serial/network)
    void* event_queue;                  // Event queue
    void* sc_ctx;                       // Secure channel context (SecureChannelContext_t*)
    uint32_t packets_sent;              // Statistics
    uint32_t packets_received;          // Statistics
    uint32_t errors;                    // Error count
    uint64_t last_poll_time;            // Last successful poll (ms)
};

#endif // OSDP_TYPES_H
