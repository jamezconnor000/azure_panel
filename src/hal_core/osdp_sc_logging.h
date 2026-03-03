/**
 * @file osdp_sc_logging.h
 * @brief OSDP Secure Channel Logging and Diagnostics API
 *
 * Provides comprehensive logging and troubleshooting for secure channel operations.
 */

#ifndef OSDP_SC_LOGGING_H
#define OSDP_SC_LOGGING_H

#include "osdp_secure_channel.h"
#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

// =============================================================================
// Logging Functions
// =============================================================================

/**
 * @brief Log the start of secure channel handshake
 * @param ctx Secure channel context
 */
void OSDP_SC_LogHandshakeStart(const SecureChannelContext_t* ctx);

/**
 * @brief Log cryptogram exchange during handshake
 * @param ctx Secure channel context
 * @param pd_random PD random number received
 * @param pd_cryptogram PD cryptogram received
 * @param verification_passed Whether cryptogram verification passed
 */
void OSDP_SC_LogCryptogramExchange(const SecureChannelContext_t* ctx,
                                     const uint8_t* pd_random,
                                     const uint8_t* pd_cryptogram,
                                     bool verification_passed);

/**
 * @brief Log successful completion of handshake
 * @param ctx Secure channel context
 */
void OSDP_SC_LogHandshakeComplete(const SecureChannelContext_t* ctx);

/**
 * @brief Log packet encryption operation
 * @param plaintext Plaintext data
 * @param plaintext_len Plaintext length
 * @param ciphertext Ciphertext output
 * @param ciphertext_len Ciphertext length (includes MAC)
 * @param sequence_num Packet sequence number
 */
void OSDP_SC_LogEncryption(const uint8_t* plaintext, uint16_t plaintext_len,
                            const uint8_t* ciphertext, uint16_t ciphertext_len,
                            uint32_t sequence_num);

/**
 * @brief Log packet decryption operation
 * @param ciphertext Ciphertext input
 * @param ciphertext_len Ciphertext length
 * @param plaintext Plaintext output
 * @param plaintext_len Plaintext length
 * @param sequence_num Packet sequence number
 * @param mac_valid Whether MAC verification passed
 */
void OSDP_SC_LogDecryption(const uint8_t* ciphertext, uint16_t ciphertext_len,
                            const uint8_t* plaintext, uint16_t plaintext_len,
                            uint32_t sequence_num,
                            bool mac_valid);

/**
 * @brief Log secure channel error
 * @param operation Operation that failed
 * @param error_code Error code
 */
void OSDP_SC_LogError(const char* operation, ErrorCode_t error_code);

/**
 * @brief Log secure channel statistics
 * @param ctx Secure channel context
 * @param packets_encrypted Number of packets encrypted
 * @param packets_decrypted Number of packets decrypted
 * @param errors Number of errors encountered
 */
void OSDP_SC_LogStatistics(const SecureChannelContext_t* ctx,
                            uint32_t packets_encrypted,
                            uint32_t packets_decrypted,
                            uint32_t errors);

/**
 * @brief Log secure channel reset
 */
void OSDP_SC_LogReset(void);

// =============================================================================
// Troubleshooting Helpers
// =============================================================================

/**
 * @brief Diagnose a secure channel error and provide troubleshooting guidance
 * @param error Error code
 * @param state Current secure channel state
 * @return Human-readable diagnosis and troubleshooting steps
 */
const char* OSDP_SC_DiagnoseError(ErrorCode_t error, SecureChannelState_t state);

#ifdef __cplusplus
}
#endif

#endif // OSDP_SC_LOGGING_H
