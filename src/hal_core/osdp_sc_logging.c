/**
 * @file osdp_sc_logging.c
 * @brief OSDP Secure Channel Logging and Diagnostics
 *
 * Provides comprehensive logging and troubleshooting for secure channel operations.
 */

#include "osdp_secure_channel.h"
#include "diagnostic_logger.h"
#include <stdio.h>
#include <string.h>

// =============================================================================
// Helper Functions for Logging
// =============================================================================

static void log_hex(const char* label, const uint8_t* data, uint16_t len) {
    char hex_str[256];
    char* ptr = hex_str;

    for (uint16_t i = 0; i < len && i < 32; i++) {  // Limit to 32 bytes
        ptr += sprintf(ptr, "%02X", data[i]);
        if (i < len - 1 && i < 31) {
            *ptr++ = ':';
        }
    }
    if (len > 32) {
        ptr += sprintf(ptr, "...");
    }
    *ptr = '\0';

    Diagnostic_Log(LOG_LEVEL_DEBUG, LOG_CAT_OSDP, __FILE__, __LINE__, __func__,
                   "%s (%d bytes): %s", label, len, hex_str);
}

void OSDP_SC_LogHandshakeStart(const SecureChannelContext_t* ctx) {
    if (!ctx) return;

    Diagnostic_Log(LOG_LEVEL_INFO, LOG_CAT_OSDP, __FILE__, __LINE__, __func__,
                   "=== SECURE CHANNEL HANDSHAKE START ===");
    Diagnostic_Log(LOG_LEVEL_INFO, LOG_CAT_OSDP, __FILE__, __LINE__, __func__,
                   "State: %s, Enabled: %s",
                   OSDP_SC_StateToString(ctx->state),
                   ctx->enabled ? "YES" : "NO");

    log_hex("CP_Random", ctx->cp_random, OSDP_RANDOM_SIZE);
}

void OSDP_SC_LogCryptogramExchange(const SecureChannelContext_t* ctx,
                                     const uint8_t* pd_random,
                                     const uint8_t* pd_cryptogram,
                                     bool verification_passed) {
    if (!ctx) return;

    Diagnostic_Log(LOG_LEVEL_INFO, LOG_CAT_OSDP, __FILE__, __LINE__, __func__,
                   "=== CRYPTOGRAM EXCHANGE ===");

    log_hex("PD_Random (received)", pd_random, OSDP_RANDOM_SIZE);
    log_hex("PD_Cryptogram (received)", pd_cryptogram, OSDP_CRYPTOGRAM_SIZE);

    Diagnostic_Log(LOG_LEVEL_INFO, LOG_CAT_OSDP, __FILE__, __LINE__, __func__,
                   "Cryptogram Verification: %s",
                   verification_passed ? "PASSED ✓" : "FAILED ✗");

    if (!verification_passed) {
        Diagnostic_Log(LOG_LEVEL_ERROR, LOG_CAT_OSDP, __FILE__, __LINE__, __func__,
                       "SECURITY ALERT: Cryptogram verification failed! Possible causes:");
        Diagnostic_Log(LOG_LEVEL_ERROR, LOG_CAT_OSDP, __FILE__, __LINE__, __func__,
                       "  1. SCBK mismatch between CP and PD");
        Diagnostic_Log(LOG_LEVEL_ERROR, LOG_CAT_OSDP, __FILE__, __LINE__, __func__,
                       "  2. Packet corruption during transmission");
        Diagnostic_Log(LOG_LEVEL_ERROR, LOG_CAT_OSDP, __FILE__, __LINE__, __func__,
                       "  3. Man-in-the-middle attack attempt");
    }
}

void OSDP_SC_LogHandshakeComplete(const SecureChannelContext_t* ctx) {
    if (!ctx) return;

    Diagnostic_Log(LOG_LEVEL_INFO, LOG_CAT_OSDP, __FILE__, __LINE__, __func__,
                   "=== SECURE CHANNEL ESTABLISHED ===");
    Diagnostic_Log(LOG_LEVEL_INFO, LOG_CAT_OSDP, __FILE__, __LINE__, __func__,
                   "State: %s", OSDP_SC_StateToString(ctx->state));
    Diagnostic_Log(LOG_LEVEL_INFO, LOG_CAT_OSDP, __FILE__, __LINE__, __func__,
                   "Session keys derived: %s",
                   ctx->keys.keys_derived ? "YES" : "NO");
    Diagnostic_Log(LOG_LEVEL_INFO, LOG_CAT_OSDP, __FILE__, __LINE__, __func__,
                   "CP Sequence: %u, PD Sequence: %u",
                   ctx->cp_seq, ctx->pd_seq);
    Diagnostic_Log(LOG_LEVEL_INFO, LOG_CAT_OSDP, __FILE__, __LINE__, __func__,
                   "All subsequent packets will be AES-128 encrypted with MAC authentication");
}

void OSDP_SC_LogEncryption(const uint8_t* plaintext, uint16_t plaintext_len,
                            const uint8_t* ciphertext, uint16_t ciphertext_len,
                            uint32_t sequence_num) {
    Diagnostic_Log(LOG_LEVEL_DEBUG, LOG_CAT_OSDP, __FILE__, __LINE__, __func__,
                   "Encrypting packet: plaintext=%d bytes, ciphertext=%d bytes (includes MAC), seq=%u",
                   plaintext_len, ciphertext_len, sequence_num);

    log_hex("Plaintext (first 16 bytes)", plaintext, plaintext_len > 16 ? 16 : plaintext_len);
    log_hex("Ciphertext (first 16 bytes)", ciphertext, ciphertext_len > 16 ? 16 : ciphertext_len);
}

void OSDP_SC_LogDecryption(const uint8_t* ciphertext, uint16_t ciphertext_len,
                            const uint8_t* plaintext, uint16_t plaintext_len,
                            uint32_t sequence_num,
                            bool mac_valid) {
    Diagnostic_Log(LOG_LEVEL_DEBUG, LOG_CAT_OSDP, __FILE__, __LINE__, __func__,
                   "Decrypting packet: ciphertext=%d bytes, plaintext=%d bytes, seq=%u, MAC=%s",
                   ciphertext_len, plaintext_len, sequence_num,
                   mac_valid ? "VALID ✓" : "INVALID ✗");

    if (!mac_valid) {
        Diagnostic_Log(LOG_LEVEL_ERROR, LOG_CAT_OSDP, __FILE__, __LINE__, __func__,
                       "SECURITY ALERT: MAC verification failed! Packet may be tampered!");
        Diagnostic_Log(LOG_LEVEL_ERROR, LOG_CAT_OSDP, __FILE__, __LINE__, __func__,
                       "Possible causes: packet corruption, wrong MAC key, tampering attempt");
    }

    log_hex("Ciphertext (first 16 bytes)", ciphertext, ciphertext_len > 16 ? 16 : ciphertext_len);
    log_hex("Plaintext (first 16 bytes)", plaintext, plaintext_len > 16 ? 16 : plaintext_len);
}

void OSDP_SC_LogError(const char* operation, ErrorCode_t error_code) {
    const char* error_str = "UNKNOWN";

    switch (error_code) {
        case ErrorCode_OK:           error_str = "OK"; break;
        case ErrorCode_BadParams:    error_str = "Bad Parameters"; break;
        case ErrorCode_CryptoError:  error_str = "Cryptographic Error"; break;
        case ErrorCode_NotEnabled:   error_str = "Secure Channel Not Enabled"; break;
        case ErrorCode_InvalidState: error_str = "Invalid State"; break;
        case ErrorCode_AuthFailed:   error_str = "Authentication Failed"; break;
        default: error_str = "Unknown Error"; break;
    }

    Diagnostic_Log(LOG_LEVEL_ERROR, LOG_CAT_OSDP, __FILE__, __LINE__, __func__,
                   "Secure Channel Error in %s: %s (code=%d)",
                   operation, error_str, error_code);
}

void OSDP_SC_LogStatistics(const SecureChannelContext_t* ctx,
                            uint32_t packets_encrypted,
                            uint32_t packets_decrypted,
                            uint32_t errors) {
    if (!ctx) return;

    Diagnostic_Log(LOG_LEVEL_INFO, LOG_CAT_OSDP, __FILE__, __LINE__, __func__,
                   "=== SECURE CHANNEL STATISTICS ===");
    Diagnostic_Log(LOG_LEVEL_INFO, LOG_CAT_OSDP, __FILE__, __LINE__, __func__,
                   "State: %s, Established: %s",
                   OSDP_SC_StateToString(ctx->state),
                   OSDP_SC_IsEstablished(ctx) ? "YES" : "NO");
    Diagnostic_Log(LOG_LEVEL_INFO, LOG_CAT_OSDP, __FILE__, __LINE__, __func__,
                   "Packets Encrypted: %u", packets_encrypted);
    Diagnostic_Log(LOG_LEVEL_INFO, LOG_CAT_OSDP, __FILE__, __LINE__, __func__,
                   "Packets Decrypted: %u", packets_decrypted);
    Diagnostic_Log(LOG_LEVEL_INFO, LOG_CAT_OSDP, __FILE__, __LINE__, __func__,
                   "Errors: %u", errors);
    Diagnostic_Log(LOG_LEVEL_INFO, LOG_CAT_OSDP, __FILE__, __LINE__, __func__,
                   "CP Sequence: %u, PD Sequence: %u",
                   ctx->cp_seq, ctx->pd_seq);
}

void OSDP_SC_LogReset(void) {
    Diagnostic_Log(LOG_LEVEL_WARN, LOG_CAT_OSDP, __FILE__, __LINE__, __func__,
                   "=== SECURE CHANNEL RESET ===");
    Diagnostic_Log(LOG_LEVEL_WARN, LOG_CAT_OSDP, __FILE__, __LINE__, __func__,
                   "All cryptographic material cleared");
    Diagnostic_Log(LOG_LEVEL_WARN, LOG_CAT_OSDP, __FILE__, __LINE__, __func__,
                   "Secure channel returning to INIT state");
}

// =============================================================================
// Troubleshooting Helpers
// =============================================================================

const char* OSDP_SC_DiagnoseError(ErrorCode_t error, SecureChannelState_t state) {
    static char diagnosis[512];

    switch (error) {
        case ErrorCode_AuthFailed:
            if (state == SC_STATE_CHALLENGE_RECV) {
                sprintf(diagnosis,
                        "Authentication failed during handshake. "
                        "SCBK mismatch between CP and PD. "
                        "Verify both devices have same 128-bit SCBK provisioned.");
            } else {
                sprintf(diagnosis,
                        "MAC verification failed on encrypted packet. "
                        "Possible packet tampering or corruption. "
                        "Check communication integrity.");
            }
            break;

        case ErrorCode_CryptoError:
            sprintf(diagnosis,
                    "Cryptographic operation failed. "
                    "Check OpenSSL installation and system entropy. "
                    "Verify AES-128 support is available.");
            break;

        case ErrorCode_NotEnabled:
            sprintf(diagnosis,
                    "Secure channel not enabled in configuration. "
                    "Set secure_channel=true in OSDP_Config_t. "
                    "Provision SCBK before enabling.");
            break;

        case ErrorCode_InvalidState:
            sprintf(diagnosis,
                    "Operation invalid for current state (%s). "
                    "Follow handshake sequence: INIT → CHALLENGE_SENT → "
                    "CHALLENGE_RECV → ESTABLISHED.",
                    OSDP_SC_StateToString(state));
            break;

        default:
            sprintf(diagnosis, "Unknown error. Check logs for details.");
            break;
    }

    return diagnosis;
}
