/**
 * @file osdp_reader.h
 * @brief OSDP Reader Communication Interface
 *
 * Provides functions for communicating with OSDP-compatible card readers.
 */

#ifndef OSDP_READER_H
#define OSDP_READER_H

#include "../../include/osdp_types.h"
#include "../../include/hal_types.h"

// =============================================================================
// OSDP Reader Management
// =============================================================================

/**
 * Create an OSDP reader instance
 *
 * @param lpa Reader logical-physical address
 * @param config OSDP configuration
 * @return Pointer to OSDP reader handle, or NULL on error
 */
OSDP_Reader_t* OSDP_Reader_Create(LPA_t lpa, const OSDP_Config_t* config);

/**
 * Destroy an OSDP reader instance
 *
 * @param reader Reader handle
 */
void OSDP_Reader_Destroy(OSDP_Reader_t* reader);

/**
 * Initialize OSDP reader communication
 *
 * @param reader Reader handle
 * @param port Serial port device path (e.g., "/dev/ttyUSB0")
 * @return ErrorCode_OK on success, error code otherwise
 */
ErrorCode_t OSDP_Reader_Init(OSDP_Reader_t* reader, const char* port);

/**
 * Close OSDP reader communication
 *
 * @param reader Reader handle
 * @return ErrorCode_OK on success, error code otherwise
 */
ErrorCode_t OSDP_Reader_Close(OSDP_Reader_t* reader);

// =============================================================================
// OSDP Secure Channel
// =============================================================================

/**
 * Establish secure channel with OSDP reader
 *
 * @param reader Reader handle (must have secure_channel enabled in config)
 * @return ErrorCode_OK on success, error code otherwise
 */
ErrorCode_t OSDP_Reader_EstablishSecureChannel(OSDP_Reader_t* reader);

/**
 * Check if secure channel is established
 *
 * @param reader Reader handle
 * @return true if secure channel is active, false otherwise
 */
bool OSDP_Reader_IsSecureChannelActive(OSDP_Reader_t* reader);

/**
 * Reset secure channel (teardown)
 *
 * @param reader Reader handle
 */
void OSDP_Reader_ResetSecureChannel(OSDP_Reader_t* reader);

// =============================================================================
// OSDP Communication
// =============================================================================

/**
 * Poll OSDP reader
 *
 * @param reader Reader handle
 * @return ErrorCode_OK on success, error code otherwise
 */
ErrorCode_t OSDP_Reader_Poll(OSDP_Reader_t* reader);

/**
 * Send command to OSDP reader
 *
 * @param reader Reader handle
 * @param cmd Command code
 * @param data Command data
 * @param data_len Length of command data
 * @return ErrorCode_OK on success, error code otherwise
 */
ErrorCode_t OSDP_Reader_SendCommand(OSDP_Reader_t* reader, OSDP_Command_t cmd,
                                     const uint8_t* data, uint16_t data_len);

/**
 * Receive reply from OSDP reader
 *
 * @param reader Reader handle
 * @param reply Output buffer for reply code
 * @param data Output buffer for reply data
 * @param max_len Maximum length of data buffer
 * @param actual_len Output: actual length of reply data
 * @return ErrorCode_OK on success, error code otherwise
 */
ErrorCode_t OSDP_Reader_ReceiveReply(OSDP_Reader_t* reader, OSDP_Reply_t* reply,
                                      uint8_t* data, uint16_t max_len, uint16_t* actual_len);

// =============================================================================
// OSDP Device Information
// =============================================================================

/**
 * Request device identification from OSDP reader
 *
 * @param reader Reader handle
 * @param vendor_code Output: vendor code
 * @param model Output: model number
 * @param version Output: firmware version
 * @param serial Output: serial number
 * @return ErrorCode_OK on success, error code otherwise
 */
ErrorCode_t OSDP_Reader_GetDeviceID(OSDP_Reader_t* reader, uint32_t* vendor_code,
                                     uint8_t* model, uint32_t* version, uint32_t* serial);

/**
 * Request device capabilities from OSDP reader
 *
 * @param reader Reader handle
 * @param caps Output buffer for capabilities
 * @param max_caps Maximum number of capabilities
 * @param actual_caps Output: actual number of capabilities
 * @return ErrorCode_OK on success, error code otherwise
 */
ErrorCode_t OSDP_Reader_GetCapabilities(OSDP_Reader_t* reader, OSDP_PD_Capability_t* caps,
                                         uint8_t max_caps, uint8_t* actual_caps);

// =============================================================================
// OSDP LED Control
// =============================================================================

/**
 * Set LED state on OSDP reader
 *
 * @param reader Reader handle
 * @param led_cmd LED control command
 * @return ErrorCode_OK on success, error code otherwise
 */
ErrorCode_t OSDP_Reader_SetLED(OSDP_Reader_t* reader, const OSDP_LED_Cmd_t* led_cmd);

/**
 * Set LED to solid color (convenience function)
 *
 * @param reader Reader handle
 * @param led_number LED number (0-based)
 * @param color LED color
 * @return ErrorCode_OK on success, error code otherwise
 */
ErrorCode_t OSDP_Reader_SetLED_Solid(OSDP_Reader_t* reader, uint8_t led_number, OSDP_LED_Color_t color);

/**
 * Set LED to blink (convenience function)
 *
 * @param reader Reader handle
 * @param led_number LED number (0-based)
 * @param color LED color
 * @param on_time On time in 100ms units
 * @param off_time Off time in 100ms units
 * @return ErrorCode_OK on success, error code otherwise
 */
ErrorCode_t OSDP_Reader_SetLED_Blink(OSDP_Reader_t* reader, uint8_t led_number,
                                      OSDP_LED_Color_t color, uint8_t on_time, uint8_t off_time);

// =============================================================================
// OSDP Buzzer Control
// =============================================================================

/**
 * Activate buzzer on OSDP reader
 *
 * @param reader Reader handle
 * @param buzzer_cmd Buzzer control command
 * @return ErrorCode_OK on success, error code otherwise
 */
ErrorCode_t OSDP_Reader_SetBuzzer(OSDP_Reader_t* reader, const OSDP_Buzzer_Cmd_t* buzzer_cmd);

/**
 * Beep buzzer once (convenience function)
 *
 * @param reader Reader handle
 * @param duration Duration in 100ms units
 * @return ErrorCode_OK on success, error code otherwise
 */
ErrorCode_t OSDP_Reader_Beep(OSDP_Reader_t* reader, uint8_t duration);

// =============================================================================
// OSDP Output Control
// =============================================================================

/**
 * Control output on OSDP reader
 *
 * @param reader Reader handle
 * @param output_number Output number (0-based)
 * @param state Output state (true = ON, false = OFF)
 * @return ErrorCode_OK on success, error code otherwise
 */
ErrorCode_t OSDP_Reader_SetOutput(OSDP_Reader_t* reader, uint8_t output_number, bool state);

/**
 * Pulse output on OSDP reader
 *
 * @param reader Reader handle
 * @param output_number Output number (0-based)
 * @param duration Pulse duration in 100ms units
 * @return ErrorCode_OK on success, error code otherwise
 */
ErrorCode_t OSDP_Reader_PulseOutput(OSDP_Reader_t* reader, uint8_t output_number, uint8_t duration);

// =============================================================================
// OSDP Event Handling
// =============================================================================

/**
 * Check for pending events from OSDP reader
 *
 * @param reader Reader handle
 * @return true if events are pending, false otherwise
 */
bool OSDP_Reader_HasEvents(OSDP_Reader_t* reader);

/**
 * Get next event from OSDP reader
 *
 * @param reader Reader handle
 * @param event_type Output: event type
 * @param card_data Output: card data (if applicable)
 * @return ErrorCode_OK on success, error code otherwise
 */
ErrorCode_t OSDP_Reader_GetEvent(OSDP_Reader_t* reader, OSDP_Event_Type_t* event_type,
                                  OSDP_Card_Data_t* card_data);

/**
 * Queue an event for the OSDP reader (internal use)
 *
 * @param reader Reader handle
 * @param event_type Event type to queue
 * @param card_data Card data (may be NULL)
 * @return ErrorCode_OK on success, error code otherwise
 */
ErrorCode_t OSDP_Reader_QueueEvent(OSDP_Reader_t* reader, OSDP_Event_Type_t event_type,
                                    const OSDP_Card_Data_t* card_data);

/**
 * Get number of pending events
 *
 * @param reader Reader handle
 * @return Number of events in queue
 */
uint8_t OSDP_Reader_GetEventCount(OSDP_Reader_t* reader);

// =============================================================================
// OSDP Status
// =============================================================================

/**
 * Get OSDP reader state
 *
 * @param reader Reader handle
 * @return Current reader state
 */
OSDP_State_t OSDP_Reader_GetState(OSDP_Reader_t* reader);

/**
 * Get OSDP reader statistics
 *
 * @param reader Reader handle
 * @param packets_sent Output: number of packets sent
 * @param packets_received Output: number of packets received
 * @param errors Output: number of errors
 * @return ErrorCode_OK on success, error code otherwise
 */
ErrorCode_t OSDP_Reader_GetStats(OSDP_Reader_t* reader, uint32_t* packets_sent,
                                  uint32_t* packets_received, uint32_t* errors);

/**
 * Check if OSDP reader is online
 *
 * @param reader Reader handle
 * @return true if reader is online, false otherwise
 */
bool OSDP_Reader_IsOnline(OSDP_Reader_t* reader);

// =============================================================================
// OSDP Utility Functions
// =============================================================================

/**
 * Calculate CRC-16 checksum for OSDP packet
 *
 * @param data Data buffer
 * @param len Length of data
 * @return CRC-16 checksum
 */
uint16_t OSDP_CalcCRC16(const uint8_t* data, uint16_t len);

/**
 * Build OSDP packet
 *
 * @param addr PD address
 * @param sequence Sequence number
 * @param cmd Command code
 * @param data Command data
 * @param data_len Length of command data
 * @param packet Output buffer for packet
 * @param max_len Maximum packet length
 * @param actual_len Output: actual packet length
 * @return ErrorCode_OK on success, error code otherwise
 */
ErrorCode_t OSDP_BuildPacket(uint8_t addr, uint8_t sequence, uint8_t cmd,
                              const uint8_t* data, uint16_t data_len,
                              uint8_t* packet, uint16_t max_len, uint16_t* actual_len);

/**
 * Parse OSDP packet
 *
 * @param packet Packet buffer
 * @param packet_len Packet length
 * @param reply Output: reply code
 * @param data Output buffer for reply data
 * @param max_len Maximum data length
 * @param actual_len Output: actual data length
 * @return ErrorCode_OK on success, error code otherwise
 */
ErrorCode_t OSDP_ParsePacket(const uint8_t* packet, uint16_t packet_len,
                              uint8_t* reply, uint8_t* data, uint16_t max_len, uint16_t* actual_len);

#endif // OSDP_READER_H
