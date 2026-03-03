/**
 * @file osdp_secure_channel.h
 * @brief OSDP Secure Channel (AES-128) Implementation
 *
 * Implements OSDP Secure Channel Protocol as per SIA OSDP v2.2 specification.
 * Provides end-to-end encryption between CP (Control Panel) and PD (Peripheral Device).
 */

#ifndef OSDP_SECURE_CHANNEL_H
#define OSDP_SECURE_CHANNEL_H

#include "../../include/osdp_types.h"
#include "../../include/hal_types.h"
#include <stdint.h>
#include <stdbool.h>

// =============================================================================
// Secure Channel Constants
// =============================================================================

#define OSDP_KEY_SIZE           16      // AES-128 key size (128 bits)
#define OSDP_IV_SIZE            16      // AES IV size
#define OSDP_MAC_SIZE           16      // MAC size
#define OSDP_RANDOM_SIZE        8       // Random number size
#define OSDP_CRYPTOGRAM_SIZE    16      // Cryptogram size

// =============================================================================
// Secure Channel State
// =============================================================================

typedef enum {
    SC_STATE_INIT = 0,          // Initial state, no security
    SC_STATE_CHALLENGE_SENT,    // CP sent challenge to PD
    SC_STATE_CHALLENGE_RECV,    // CP received cryptogram from PD
    SC_STATE_ESTABLISHED,       // Secure channel established
    SC_STATE_ERROR              // Error state
} SecureChannelState_t;

// =============================================================================
// Key Storage
// =============================================================================

typedef struct {
    uint8_t scbk[OSDP_KEY_SIZE];        // Secure Channel Base Key
    uint8_t s_enc[OSDP_KEY_SIZE];       // Session Encryption Key
    uint8_t s_mac1[OSDP_KEY_SIZE];      // Session MAC Key 1
    uint8_t s_mac2[OSDP_KEY_SIZE];      // Session MAC Key 2
    bool keys_derived;                  // Session keys have been derived
} SecureChannelKeys_t;

// =============================================================================
// Secure Channel Context
// =============================================================================

typedef struct {
    SecureChannelState_t state;         // Current state
    SecureChannelKeys_t keys;           // Cryptographic keys
    uint8_t cp_random[OSDP_RANDOM_SIZE]; // CP random number
    uint8_t pd_random[OSDP_RANDOM_SIZE]; // PD random number
    uint8_t cp_cryptogram[OSDP_CRYPTOGRAM_SIZE]; // CP cryptogram
    uint8_t pd_cryptogram[OSDP_CRYPTOGRAM_SIZE]; // PD cryptogram
    uint32_t cp_seq;                    // CP sequence number
    uint32_t pd_seq;                    // PD sequence number
    bool enabled;                       // Secure channel enabled
} SecureChannelContext_t;

// =============================================================================
// AES-128 Functions
// =============================================================================

/**
 * AES-128 ECB encryption
 *
 * @param key 128-bit encryption key
 * @param input 128-bit input block
 * @param output 128-bit output block
 * @return ErrorCode_OK on success
 */
ErrorCode_t OSDP_AES128_Encrypt(const uint8_t* key, const uint8_t* input, uint8_t* output);

/**
 * AES-128 ECB decryption
 *
 * @param key 128-bit decryption key
 * @param input 128-bit input block
 * @param output 128-bit output block
 * @return ErrorCode_OK on success
 */
ErrorCode_t OSDP_AES128_Decrypt(const uint8_t* key, const uint8_t* input, uint8_t* output);

/**
 * AES-128 CBC encryption
 *
 * @param key 128-bit encryption key
 * @param iv 128-bit initialization vector
 * @param input Input data (must be multiple of 16 bytes)
 * @param input_len Input length in bytes
 * @param output Output buffer (same size as input)
 * @return ErrorCode_OK on success
 */
ErrorCode_t OSDP_AES128_CBC_Encrypt(const uint8_t* key, const uint8_t* iv,
                                     const uint8_t* input, uint16_t input_len,
                                     uint8_t* output);

/**
 * AES-128 CBC decryption
 *
 * @param key 128-bit decryption key
 * @param iv 128-bit initialization vector
 * @param input Input data (must be multiple of 16 bytes)
 * @param input_len Input length in bytes
 * @param output Output buffer (same size as input)
 * @return ErrorCode_OK on success
 */
ErrorCode_t OSDP_AES128_CBC_Decrypt(const uint8_t* key, const uint8_t* iv,
                                     const uint8_t* input, uint16_t input_len,
                                     uint8_t* output);

// =============================================================================
// Key Derivation Functions
// =============================================================================

/**
 * Derive session keys from SCBK and random numbers
 *
 * @param scbk Secure Channel Base Key (128-bit)
 * @param cp_random CP random number (64-bit)
 * @param pd_random PD random number (64-bit)
 * @param keys Output: derived session keys
 * @return ErrorCode_OK on success
 */
ErrorCode_t OSDP_DeriveSessionKeys(const uint8_t* scbk,
                                    const uint8_t* cp_random,
                                    const uint8_t* pd_random,
                                    SecureChannelKeys_t* keys);

// =============================================================================
// Cryptogram Generation/Verification
// =============================================================================

/**
 * Generate server cryptogram (CP -> PD)
 *
 * @param s_enc Session encryption key
 * @param cp_random CP random number
 * @param pd_random PD random number
 * @param cryptogram Output: 128-bit cryptogram
 * @return ErrorCode_OK on success
 */
ErrorCode_t OSDP_GenerateServerCryptogram(const uint8_t* s_enc,
                                           const uint8_t* cp_random,
                                           const uint8_t* pd_random,
                                           uint8_t* cryptogram);

/**
 * Generate client cryptogram (PD -> CP)
 *
 * @param s_enc Session encryption key
 * @param pd_random PD random number
 * @param cp_random CP random number
 * @param cryptogram Output: 128-bit cryptogram
 * @return ErrorCode_OK on success
 */
ErrorCode_t OSDP_GenerateClientCryptogram(const uint8_t* s_enc,
                                           const uint8_t* pd_random,
                                           const uint8_t* cp_random,
                                           uint8_t* cryptogram);

/**
 * Verify received cryptogram
 *
 * @param expected Expected cryptogram
 * @param received Received cryptogram
 * @return true if cryptograms match
 */
bool OSDP_VerifyCryptogram(const uint8_t* expected, const uint8_t* received);

// =============================================================================
// MAC Generation/Verification
// =============================================================================

/**
 * Generate MAC for message authentication
 *
 * @param s_mac MAC key
 * @param data Data to authenticate
 * @param data_len Length of data
 * @param mac Output: 128-bit MAC
 * @return ErrorCode_OK on success
 */
ErrorCode_t OSDP_GenerateMAC(const uint8_t* s_mac,
                              const uint8_t* data, uint16_t data_len,
                              uint8_t* mac);

/**
 * Verify MAC
 *
 * @param s_mac MAC key
 * @param data Data to verify
 * @param data_len Length of data
 * @param received_mac Received MAC
 * @return true if MAC is valid
 */
bool OSDP_VerifyMAC(const uint8_t* s_mac,
                     const uint8_t* data, uint16_t data_len,
                     const uint8_t* received_mac);

// =============================================================================
// Secure Channel Management
// =============================================================================

/**
 * Initialize secure channel context
 *
 * @param ctx Secure channel context
 * @param scbk Secure Channel Base Key (128-bit)
 * @return ErrorCode_OK on success
 */
ErrorCode_t OSDP_SC_Init(SecureChannelContext_t* ctx, const uint8_t* scbk);

/**
 * Start secure channel handshake (CP initiates)
 *
 * @param ctx Secure channel context
 * @return ErrorCode_OK on success
 */
ErrorCode_t OSDP_SC_StartHandshake(SecureChannelContext_t* ctx);

/**
 * Process received client cryptogram (CP receives from PD)
 *
 * @param ctx Secure channel context
 * @param pd_random PD random number (64-bit)
 * @param pd_cryptogram PD cryptogram (128-bit)
 * @return ErrorCode_OK on success
 */
ErrorCode_t OSDP_SC_ProcessClientCryptogram(SecureChannelContext_t* ctx,
                                             const uint8_t* pd_random,
                                             const uint8_t* pd_cryptogram);

/**
 * Generate server cryptogram (CP sends to PD)
 *
 * @param ctx Secure channel context
 * @param server_cryptogram Output: 128-bit server cryptogram
 * @return ErrorCode_OK on success
 */
ErrorCode_t OSDP_SC_GenerateServerCryptogram(SecureChannelContext_t* ctx,
                                              uint8_t* server_cryptogram);

/**
 * Finalize secure channel establishment
 *
 * @param ctx Secure channel context
 * @return ErrorCode_OK on success
 */
ErrorCode_t OSDP_SC_Finalize(SecureChannelContext_t* ctx);

/**
 * Check if secure channel is established
 *
 * @param ctx Secure channel context
 * @return true if secure channel is active
 */
bool OSDP_SC_IsEstablished(const SecureChannelContext_t* ctx);

/**
 * Reset secure channel (teardown)
 *
 * @param ctx Secure channel context
 */
void OSDP_SC_Reset(SecureChannelContext_t* ctx);

// =============================================================================
// Secure Packet Encryption/Decryption
// =============================================================================

/**
 * Encrypt OSDP packet using secure channel
 *
 * @param ctx Secure channel context
 * @param plaintext Plaintext packet data
 * @param plaintext_len Length of plaintext
 * @param ciphertext Output: encrypted packet
 * @param ciphertext_len Output: length of ciphertext (includes MAC)
 * @param max_len Maximum output buffer size
 * @return ErrorCode_OK on success
 */
ErrorCode_t OSDP_SC_EncryptPacket(SecureChannelContext_t* ctx,
                                   const uint8_t* plaintext, uint16_t plaintext_len,
                                   uint8_t* ciphertext, uint16_t* ciphertext_len,
                                   uint16_t max_len);

/**
 * Decrypt OSDP packet using secure channel
 *
 * @param ctx Secure channel context
 * @param ciphertext Encrypted packet data (includes MAC)
 * @param ciphertext_len Length of ciphertext
 * @param plaintext Output: decrypted packet
 * @param plaintext_len Output: length of plaintext
 * @param max_len Maximum output buffer size
 * @return ErrorCode_OK on success
 */
ErrorCode_t OSDP_SC_DecryptPacket(SecureChannelContext_t* ctx,
                                   const uint8_t* ciphertext, uint16_t ciphertext_len,
                                   uint8_t* plaintext, uint16_t* plaintext_len,
                                   uint16_t max_len);

// =============================================================================
// Utility Functions
// =============================================================================

/**
 * Generate random bytes (for challenge/nonce)
 *
 * @param buffer Output buffer
 * @param len Number of random bytes to generate
 * @return ErrorCode_OK on success
 */
ErrorCode_t OSDP_GenerateRandom(uint8_t* buffer, uint16_t len);

/**
 * Get secure channel state string
 *
 * @param state Secure channel state
 * @return State name as string
 */
const char* OSDP_SC_StateToString(SecureChannelState_t state);

#endif // OSDP_SECURE_CHANNEL_H
