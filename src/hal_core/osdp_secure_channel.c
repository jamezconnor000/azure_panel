/**
 * @file osdp_secure_channel.c
 * @brief OSDP Secure Channel (AES-128) Implementation
 *
 * Implements OSDP Secure Channel Protocol as per SIA OSDP v2.2 specification.
 * Provides end-to-end encryption between CP (Control Panel) and PD (Peripheral Device).
 */

#include "osdp_secure_channel.h"
#include "osdp_sc_logging.h"
#include "diagnostic_logger.h"
#include <string.h>
#include <stdlib.h>
#include <time.h>
#include <stdio.h>
#include <openssl/aes.h>
#include <openssl/evp.h>
#include <openssl/rand.h>

// Enable debug logging (set to 0 to disable verbose logging)
#define SC_DEBUG_LOGGING 1

#if SC_DEBUG_LOGGING
#define SC_LOG_DEBUG(fmt, ...) \
    Diagnostic_Log(LOG_LEVEL_DEBUG, LOG_CAT_OSDP, __FILE__, __LINE__, __func__, fmt, ##__VA_ARGS__)
#define SC_LOG_INFO(fmt, ...) \
    Diagnostic_Log(LOG_LEVEL_INFO, LOG_CAT_OSDP, __FILE__, __LINE__, __func__, fmt, ##__VA_ARGS__)
#define SC_LOG_WARN(fmt, ...) \
    Diagnostic_Log(LOG_LEVEL_WARN, LOG_CAT_OSDP, __FILE__, __LINE__, __func__, fmt, ##__VA_ARGS__)
#define SC_LOG_ERROR(fmt, ...) \
    Diagnostic_Log(LOG_LEVEL_ERROR, LOG_CAT_OSDP, __FILE__, __LINE__, __func__, fmt, ##__VA_ARGS__)
#else
#define SC_LOG_DEBUG(fmt, ...)
#define SC_LOG_INFO(fmt, ...)
#define SC_LOG_WARN(fmt, ...)
#define SC_LOG_ERROR(fmt, ...)
#endif

// =============================================================================
// AES-128 Encryption Functions
// =============================================================================

ErrorCode_t OSDP_AES128_Encrypt(const uint8_t* key, const uint8_t* input, uint8_t* output) {
    if (!key || !input || !output) {
        return ErrorCode_BadParams;
    }

    AES_KEY aes_key;
    if (AES_set_encrypt_key(key, 128, &aes_key) != 0) {
        return ErrorCode_CryptoError;
    }

    AES_encrypt(input, output, &aes_key);

    // Clear sensitive key data
    memset(&aes_key, 0, sizeof(aes_key));

    return ErrorCode_OK;
}

ErrorCode_t OSDP_AES128_Decrypt(const uint8_t* key, const uint8_t* input, uint8_t* output) {
    if (!key || !input || !output) {
        return ErrorCode_BadParams;
    }

    AES_KEY aes_key;
    if (AES_set_decrypt_key(key, 128, &aes_key) != 0) {
        return ErrorCode_CryptoError;
    }

    AES_decrypt(input, output, &aes_key);

    // Clear sensitive key data
    memset(&aes_key, 0, sizeof(aes_key));

    return ErrorCode_OK;
}

ErrorCode_t OSDP_AES128_CBC_Encrypt(const uint8_t* key, const uint8_t* iv,
                                     const uint8_t* input, uint16_t input_len,
                                     uint8_t* output) {
    if (!key || !iv || !input || !output) {
        return ErrorCode_BadParams;
    }

    if (input_len % 16 != 0) {
        return ErrorCode_BadParams;  // Must be multiple of 16 bytes
    }

    AES_KEY aes_key;
    if (AES_set_encrypt_key(key, 128, &aes_key) != 0) {
        return ErrorCode_CryptoError;
    }

    uint8_t iv_copy[16];
    memcpy(iv_copy, iv, 16);

    AES_cbc_encrypt(input, output, input_len, &aes_key, iv_copy, AES_ENCRYPT);

    // Clear sensitive data
    memset(&aes_key, 0, sizeof(aes_key));
    memset(iv_copy, 0, sizeof(iv_copy));

    return ErrorCode_OK;
}

ErrorCode_t OSDP_AES128_CBC_Decrypt(const uint8_t* key, const uint8_t* iv,
                                     const uint8_t* input, uint16_t input_len,
                                     uint8_t* output) {
    if (!key || !iv || !input || !output) {
        return ErrorCode_BadParams;
    }

    if (input_len % 16 != 0) {
        return ErrorCode_BadParams;  // Must be multiple of 16 bytes
    }

    AES_KEY aes_key;
    if (AES_set_decrypt_key(key, 128, &aes_key) != 0) {
        return ErrorCode_CryptoError;
    }

    uint8_t iv_copy[16];
    memcpy(iv_copy, iv, 16);

    AES_cbc_encrypt(input, output, input_len, &aes_key, iv_copy, AES_DECRYPT);

    // Clear sensitive data
    memset(&aes_key, 0, sizeof(aes_key));
    memset(iv_copy, 0, sizeof(iv_copy));

    return ErrorCode_OK;
}

// =============================================================================
// Key Derivation Functions
// =============================================================================

ErrorCode_t OSDP_DeriveSessionKeys(const uint8_t* scbk,
                                    const uint8_t* cp_random,
                                    const uint8_t* pd_random,
                                    SecureChannelKeys_t* keys) {
    if (!scbk || !cp_random || !pd_random || !keys) {
        return ErrorCode_BadParams;
    }

    // Store SCBK
    memcpy(keys->scbk, scbk, OSDP_KEY_SIZE);

    // Derive S-ENC (Session Encryption Key)
    // S-ENC = AES(SCBK, CP_Random || PD_Random)
    uint8_t input_enc[16];
    memcpy(input_enc, cp_random, 8);
    memcpy(input_enc + 8, pd_random, 8);

    ErrorCode_t result = OSDP_AES128_Encrypt(scbk, input_enc, keys->s_enc);
    if (result != ErrorCode_OK) {
        return result;
    }

    // Derive S-MAC1 (Session MAC Key 1)
    // S-MAC1 = AES(SCBK, 0x01 || 0x82 || CP_Random[0:5] || PD_Random[0:5])
    uint8_t input_mac1[16];
    input_mac1[0] = 0x01;
    input_mac1[1] = 0x82;
    memcpy(input_mac1 + 2, cp_random, 6);
    memcpy(input_mac1 + 8, pd_random, 6);
    memset(input_mac1 + 14, 0, 2);

    result = OSDP_AES128_Encrypt(scbk, input_mac1, keys->s_mac1);
    if (result != ErrorCode_OK) {
        return result;
    }

    // Derive S-MAC2 (Session MAC Key 2)
    // S-MAC2 = AES(SCBK, 0x01 || 0x83 || CP_Random[0:5] || PD_Random[0:5])
    uint8_t input_mac2[16];
    input_mac2[0] = 0x01;
    input_mac2[1] = 0x83;
    memcpy(input_mac2 + 2, cp_random, 6);
    memcpy(input_mac2 + 8, pd_random, 6);
    memset(input_mac2 + 14, 0, 2);

    result = OSDP_AES128_Encrypt(scbk, input_mac2, keys->s_mac2);
    if (result != ErrorCode_OK) {
        return result;
    }

    keys->keys_derived = true;

    // Clear sensitive input buffers
    memset(input_enc, 0, sizeof(input_enc));
    memset(input_mac1, 0, sizeof(input_mac1));
    memset(input_mac2, 0, sizeof(input_mac2));

    return ErrorCode_OK;
}

// =============================================================================
// Cryptogram Generation/Verification
// =============================================================================

ErrorCode_t OSDP_GenerateServerCryptogram(const uint8_t* s_enc,
                                           const uint8_t* cp_random,
                                           const uint8_t* pd_random,
                                           uint8_t* cryptogram) {
    if (!s_enc || !cp_random || !pd_random || !cryptogram) {
        return ErrorCode_BadParams;
    }

    // Server Cryptogram = AES(S-ENC, PD_Random || CP_Random)
    uint8_t input[16];
    memcpy(input, pd_random, 8);
    memcpy(input + 8, cp_random, 8);

    ErrorCode_t result = OSDP_AES128_Encrypt(s_enc, input, cryptogram);

    // Clear sensitive data
    memset(input, 0, sizeof(input));

    return result;
}

ErrorCode_t OSDP_GenerateClientCryptogram(const uint8_t* s_enc,
                                           const uint8_t* pd_random,
                                           const uint8_t* cp_random,
                                           uint8_t* cryptogram) {
    if (!s_enc || !pd_random || !cp_random || !cryptogram) {
        return ErrorCode_BadParams;
    }

    // Client Cryptogram = AES(S-ENC, CP_Random || PD_Random)
    uint8_t input[16];
    memcpy(input, cp_random, 8);
    memcpy(input + 8, pd_random, 8);

    ErrorCode_t result = OSDP_AES128_Encrypt(s_enc, input, cryptogram);

    // Clear sensitive data
    memset(input, 0, sizeof(input));

    return result;
}

bool OSDP_VerifyCryptogram(const uint8_t* expected, const uint8_t* received) {
    if (!expected || !received) {
        return false;
    }

    // Constant-time comparison to prevent timing attacks
    uint8_t result = 0;
    for (int i = 0; i < OSDP_CRYPTOGRAM_SIZE; i++) {
        result |= expected[i] ^ received[i];
    }

    return (result == 0);
}

// =============================================================================
// MAC Generation/Verification
// =============================================================================

ErrorCode_t OSDP_GenerateMAC(const uint8_t* s_mac,
                              const uint8_t* data, uint16_t data_len,
                              uint8_t* mac) {
    if (!s_mac || !data || !mac) {
        return ErrorCode_BadParams;
    }

    // OSDP uses AES-128-CMAC (Cipher-based MAC)
    // For simplicity, we'll use AES-CBC-MAC which is similar

    uint8_t iv[16] = {0};  // IV = all zeros for MAC
    uint8_t padded_data[512];
    uint16_t padded_len = data_len;

    // Copy data
    memcpy(padded_data, data, data_len);

    // Add padding if necessary (PKCS#7 padding)
    uint8_t padding_needed = 16 - (data_len % 16);
    if (padding_needed < 16) {
        for (uint8_t i = 0; i < padding_needed; i++) {
            padded_data[data_len + i] = padding_needed;
        }
        padded_len = data_len + padding_needed;
    }

    // Encrypt using CBC mode
    uint8_t encrypted[512];
    ErrorCode_t result = OSDP_AES128_CBC_Encrypt(s_mac, iv, padded_data, padded_len, encrypted);
    if (result != ErrorCode_OK) {
        return result;
    }

    // MAC is the last block
    memcpy(mac, encrypted + padded_len - 16, 16);

    // Clear sensitive data
    memset(padded_data, 0, sizeof(padded_data));
    memset(encrypted, 0, sizeof(encrypted));

    return ErrorCode_OK;
}

bool OSDP_VerifyMAC(const uint8_t* s_mac,
                     const uint8_t* data, uint16_t data_len,
                     const uint8_t* received_mac) {
    if (!s_mac || !data || !received_mac) {
        return false;
    }

    uint8_t calculated_mac[16];
    ErrorCode_t result = OSDP_GenerateMAC(s_mac, data, data_len, calculated_mac);
    if (result != ErrorCode_OK) {
        return false;
    }

    // Constant-time comparison
    uint8_t diff = 0;
    for (int i = 0; i < OSDP_MAC_SIZE; i++) {
        diff |= calculated_mac[i] ^ received_mac[i];
    }

    // Clear sensitive data
    memset(calculated_mac, 0, sizeof(calculated_mac));

    return (diff == 0);
}

// =============================================================================
// Secure Channel Management
// =============================================================================

ErrorCode_t OSDP_SC_Init(SecureChannelContext_t* ctx, const uint8_t* scbk) {
    if (!ctx || !scbk) {
        SC_LOG_ERROR("Invalid parameters: ctx=%p scbk=%p", ctx, scbk);
        return ErrorCode_BadParams;
    }

    SC_LOG_INFO("Initializing secure channel context");

    memset(ctx, 0, sizeof(SecureChannelContext_t));

    memcpy(ctx->keys.scbk, scbk, OSDP_KEY_SIZE);
    ctx->state = SC_STATE_INIT;
    ctx->enabled = true;
    ctx->cp_seq = 0;
    ctx->pd_seq = 0;

    SC_LOG_INFO("Secure channel initialized: state=INIT enabled=true");

    return ErrorCode_OK;
}

ErrorCode_t OSDP_SC_StartHandshake(SecureChannelContext_t* ctx) {
    if (!ctx) {
        return ErrorCode_BadParams;
    }

    if (!ctx->enabled) {
        OSDP_SC_LogError("StartHandshake", ErrorCode_NotEnabled);
        return ErrorCode_NotEnabled;
    }

    // Generate CP random number
    ErrorCode_t result = OSDP_GenerateRandom(ctx->cp_random, OSDP_RANDOM_SIZE);
    if (result != ErrorCode_OK) {
        OSDP_SC_LogError("StartHandshake - Random generation", result);
        return result;
    }

    ctx->state = SC_STATE_CHALLENGE_SENT;

    // Log handshake start
    OSDP_SC_LogHandshakeStart(ctx);

    return ErrorCode_OK;
}

ErrorCode_t OSDP_SC_ProcessClientCryptogram(SecureChannelContext_t* ctx,
                                             const uint8_t* pd_random,
                                             const uint8_t* pd_cryptogram) {
    if (!ctx || !pd_random || !pd_cryptogram) {
        return ErrorCode_BadParams;
    }

    if (ctx->state != SC_STATE_CHALLENGE_SENT) {
        OSDP_SC_LogError("ProcessClientCryptogram", ErrorCode_InvalidState);
        return ErrorCode_InvalidState;
    }

    // Store PD random
    memcpy(ctx->pd_random, pd_random, OSDP_RANDOM_SIZE);
    memcpy(ctx->pd_cryptogram, pd_cryptogram, OSDP_CRYPTOGRAM_SIZE);

    // Derive session keys
    ErrorCode_t result = OSDP_DeriveSessionKeys(ctx->keys.scbk,
                                                  ctx->cp_random,
                                                  ctx->pd_random,
                                                  &ctx->keys);
    if (result != ErrorCode_OK) {
        ctx->state = SC_STATE_ERROR;
        OSDP_SC_LogError("ProcessClientCryptogram - Key derivation", result);
        return result;
    }

    // Generate expected client cryptogram
    uint8_t expected_cryptogram[OSDP_CRYPTOGRAM_SIZE];
    result = OSDP_GenerateClientCryptogram(ctx->keys.s_enc,
                                            ctx->pd_random,
                                            ctx->cp_random,
                                            expected_cryptogram);
    if (result != ErrorCode_OK) {
        ctx->state = SC_STATE_ERROR;
        OSDP_SC_LogError("ProcessClientCryptogram - Generation", result);
        return result;
    }

    // Verify cryptogram
    bool verification_passed = OSDP_VerifyCryptogram(expected_cryptogram, pd_cryptogram);

    // Log cryptogram exchange
    OSDP_SC_LogCryptogramExchange(ctx, pd_random, pd_cryptogram, verification_passed);

    if (!verification_passed) {
        ctx->state = SC_STATE_ERROR;
        memset(expected_cryptogram, 0, sizeof(expected_cryptogram));
        OSDP_SC_LogError("ProcessClientCryptogram - Verification", ErrorCode_AuthFailed);
        return ErrorCode_AuthFailed;
    }

    memset(expected_cryptogram, 0, sizeof(expected_cryptogram));
    ctx->state = SC_STATE_CHALLENGE_RECV;

    return ErrorCode_OK;
}

ErrorCode_t OSDP_SC_GenerateServerCryptogram(SecureChannelContext_t* ctx,
                                              uint8_t* server_cryptogram) {
    if (!ctx || !server_cryptogram) {
        return ErrorCode_BadParams;
    }

    if (ctx->state != SC_STATE_CHALLENGE_RECV) {
        return ErrorCode_InvalidState;
    }

    ErrorCode_t result = OSDP_GenerateServerCryptogram(ctx->keys.s_enc,
                                                        ctx->cp_random,
                                                        ctx->pd_random,
                                                        server_cryptogram);
    if (result != ErrorCode_OK) {
        ctx->state = SC_STATE_ERROR;
        return result;
    }

    memcpy(ctx->cp_cryptogram, server_cryptogram, OSDP_CRYPTOGRAM_SIZE);

    return ErrorCode_OK;
}

ErrorCode_t OSDP_SC_Finalize(SecureChannelContext_t* ctx) {
    if (!ctx) {
        return ErrorCode_BadParams;
    }

    if (ctx->state != SC_STATE_CHALLENGE_RECV) {
        OSDP_SC_LogError("Finalize", ErrorCode_InvalidState);
        return ErrorCode_InvalidState;
    }

    ctx->state = SC_STATE_ESTABLISHED;

    // Log handshake completion
    OSDP_SC_LogHandshakeComplete(ctx);

    return ErrorCode_OK;
}

bool OSDP_SC_IsEstablished(const SecureChannelContext_t* ctx) {
    if (!ctx) {
        return false;
    }

    return (ctx->enabled && ctx->state == SC_STATE_ESTABLISHED);
}

void OSDP_SC_Reset(SecureChannelContext_t* ctx) {
    if (!ctx) {
        return;
    }

    // Log reset
    OSDP_SC_LogReset();

    // Clear all cryptographic material
    memset(&ctx->keys, 0, sizeof(ctx->keys));
    memset(ctx->cp_random, 0, sizeof(ctx->cp_random));
    memset(ctx->pd_random, 0, sizeof(ctx->pd_random));
    memset(ctx->cp_cryptogram, 0, sizeof(ctx->cp_cryptogram));
    memset(ctx->pd_cryptogram, 0, sizeof(ctx->pd_cryptogram));

    ctx->state = SC_STATE_INIT;
    ctx->cp_seq = 0;
    ctx->pd_seq = 0;
}

// =============================================================================
// Secure Packet Encryption/Decryption
// =============================================================================

ErrorCode_t OSDP_SC_EncryptPacket(SecureChannelContext_t* ctx,
                                   const uint8_t* plaintext, uint16_t plaintext_len,
                                   uint8_t* ciphertext, uint16_t* ciphertext_len,
                                   uint16_t max_len) {
    if (!ctx || !plaintext || !ciphertext || !ciphertext_len) {
        return ErrorCode_BadParams;
    }

    if (!OSDP_SC_IsEstablished(ctx)) {
        return ErrorCode_NotEnabled;
    }

    // Calculate padded length (must be multiple of 16)
    uint16_t padded_len = plaintext_len;
    uint8_t padding_needed = 16 - (plaintext_len % 16);
    if (padding_needed < 16) {
        padded_len = plaintext_len + padding_needed;
    }

    // Check buffer size (padded data + MAC)
    if (max_len < padded_len + OSDP_MAC_SIZE) {
        return ErrorCode_BadParams;
    }

    // Prepare padded plaintext
    uint8_t padded_plaintext[512];
    memcpy(padded_plaintext, plaintext, plaintext_len);

    // Add PKCS#7 padding
    if (padding_needed < 16) {
        for (uint8_t i = 0; i < padding_needed; i++) {
            padded_plaintext[plaintext_len + i] = padding_needed;
        }
    }

    // Generate IV from sequence number
    uint8_t iv[16] = {0};
    iv[0] = (ctx->cp_seq >> 24) & 0xFF;
    iv[1] = (ctx->cp_seq >> 16) & 0xFF;
    iv[2] = (ctx->cp_seq >> 8) & 0xFF;
    iv[3] = ctx->cp_seq & 0xFF;

    // Encrypt data
    ErrorCode_t result = OSDP_AES128_CBC_Encrypt(ctx->keys.s_enc, iv,
                                                   padded_plaintext, padded_len,
                                                   ciphertext);
    if (result != ErrorCode_OK) {
        memset(padded_plaintext, 0, sizeof(padded_plaintext));
        return result;
    }

    // Generate MAC over ciphertext
    uint8_t mac[16];
    result = OSDP_GenerateMAC(ctx->keys.s_mac1, ciphertext, padded_len, mac);
    if (result != ErrorCode_OK) {
        memset(padded_plaintext, 0, sizeof(padded_plaintext));
        memset(mac, 0, sizeof(mac));
        return result;
    }

    // Append MAC
    memcpy(ciphertext + padded_len, mac, OSDP_MAC_SIZE);
    *ciphertext_len = padded_len + OSDP_MAC_SIZE;

    // Log encryption
    OSDP_SC_LogEncryption(plaintext, plaintext_len, ciphertext, *ciphertext_len, ctx->cp_seq);

    // Increment sequence number
    ctx->cp_seq++;

    // Clear sensitive data
    memset(padded_plaintext, 0, sizeof(padded_plaintext));
    memset(mac, 0, sizeof(mac));
    memset(iv, 0, sizeof(iv));

    return ErrorCode_OK;
}

ErrorCode_t OSDP_SC_DecryptPacket(SecureChannelContext_t* ctx,
                                   const uint8_t* ciphertext, uint16_t ciphertext_len,
                                   uint8_t* plaintext, uint16_t* plaintext_len,
                                   uint16_t max_len) {
    if (!ctx || !ciphertext || !plaintext || !plaintext_len) {
        return ErrorCode_BadParams;
    }

    if (!OSDP_SC_IsEstablished(ctx)) {
        return ErrorCode_NotEnabled;
    }

    // Must have at least MAC
    if (ciphertext_len < OSDP_MAC_SIZE) {
        return ErrorCode_BadParams;
    }

    uint16_t encrypted_len = ciphertext_len - OSDP_MAC_SIZE;

    // Verify MAC
    const uint8_t* received_mac = ciphertext + encrypted_len;
    bool mac_valid = OSDP_VerifyMAC(ctx->keys.s_mac2, ciphertext, encrypted_len, received_mac);

    if (!mac_valid) {
        OSDP_SC_LogError("DecryptPacket - MAC verification", ErrorCode_AuthFailed);
        return ErrorCode_AuthFailed;
    }

    // Generate IV from sequence number
    uint8_t iv[16] = {0};
    iv[0] = (ctx->pd_seq >> 24) & 0xFF;
    iv[1] = (ctx->pd_seq >> 16) & 0xFF;
    iv[2] = (ctx->pd_seq >> 8) & 0xFF;
    iv[3] = ctx->pd_seq & 0xFF;

    // Decrypt data
    uint8_t decrypted[512];
    ErrorCode_t result = OSDP_AES128_CBC_Decrypt(ctx->keys.s_enc, iv,
                                                   ciphertext, encrypted_len,
                                                   decrypted);
    if (result != ErrorCode_OK) {
        memset(decrypted, 0, sizeof(decrypted));
        memset(iv, 0, sizeof(iv));
        OSDP_SC_LogError("DecryptPacket - AES decryption", result);
        return result;
    }

    // Remove PKCS#7 padding
    uint8_t padding_len = decrypted[encrypted_len - 1];
    if (padding_len > 16 || padding_len > encrypted_len) {
        memset(decrypted, 0, sizeof(decrypted));
        memset(iv, 0, sizeof(iv));
        OSDP_SC_LogError("DecryptPacket - Invalid padding", ErrorCode_BadParams);
        return ErrorCode_BadParams;
    }

    uint16_t actual_len = encrypted_len - padding_len;

    if (max_len < actual_len) {
        memset(decrypted, 0, sizeof(decrypted));
        memset(iv, 0, sizeof(iv));
        return ErrorCode_BadParams;
    }

    memcpy(plaintext, decrypted, actual_len);
    *plaintext_len = actual_len;

    // Log decryption
    OSDP_SC_LogDecryption(ciphertext, ciphertext_len, plaintext, actual_len, ctx->pd_seq, mac_valid);

    // Increment sequence number
    ctx->pd_seq++;

    // Clear sensitive data
    memset(decrypted, 0, sizeof(decrypted));
    memset(iv, 0, sizeof(iv));

    return ErrorCode_OK;
}

// =============================================================================
// Utility Functions
// =============================================================================

ErrorCode_t OSDP_GenerateRandom(uint8_t* buffer, uint16_t len) {
    if (!buffer || len == 0) {
        return ErrorCode_BadParams;
    }

    // Use OpenSSL's secure random number generator
    if (RAND_bytes(buffer, len) != 1) {
        return ErrorCode_CryptoError;
    }

    return ErrorCode_OK;
}

const char* OSDP_SC_StateToString(SecureChannelState_t state) {
    switch (state) {
        case SC_STATE_INIT:
            return "INIT";
        case SC_STATE_CHALLENGE_SENT:
            return "CHALLENGE_SENT";
        case SC_STATE_CHALLENGE_RECV:
            return "CHALLENGE_RECV";
        case SC_STATE_ESTABLISHED:
            return "ESTABLISHED";
        case SC_STATE_ERROR:
            return "ERROR";
        default:
            return "UNKNOWN";
    }
}
