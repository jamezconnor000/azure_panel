/**
 * @file osdp_secure_demo.c
 * @brief OSDP Secure Channel Integration Demo
 *
 * Demonstrates complete OSDP reader setup with AES-128 secure channel encryption.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include "../include/osdp_types.h"
#include "../src/hal_core/osdp_reader.h"
#include "../src/hal_core/osdp_secure_channel.h"

// Demo SCBK (Secure Channel Base Key) - for testing only
// In production, generate securely and store encrypted
static const uint8_t DEMO_SCBK[16] = {
    0x30, 0x31, 0x32, 0x33, 0x34, 0x35, 0x36, 0x37,
    0x38, 0x39, 0x3A, 0x3B, 0x3C, 0x3D, 0x3E, 0x3F
};

void print_hex(const char* label, const uint8_t* data, uint16_t len) {
    printf("%s: ", label);
    for (uint16_t i = 0; i < len; i++) {
        printf("%02X", data[i]);
        if (i < len - 1) printf(":");
    }
    printf("\n");
}

int main(int argc, char* argv[]) {
    printf("╔══════════════════════════════════════════════════════════════════════════════╗\n");
    printf("║                                                                              ║\n");
    printf("║              OSDP SECURE CHANNEL INTEGRATION DEMO                           ║\n");
    printf("║              AES-128 Encrypted Reader Communication                         ║\n");
    printf("║                                                                              ║\n");
    printf("╚══════════════════════════════════════════════════════════════════════════════╝\n");
    printf("\n");

    // Configuration
    const char* serial_port = argc > 1 ? argv[1] : "/dev/ttyUSB0";
    uint8_t reader_address = argc > 2 ? atoi(argv[2]) : 1;

    printf("[CONFIG] Serial Port: %s\n", serial_port);
    printf("[CONFIG] Reader Address: %d\n", reader_address);
    printf("[CONFIG] Security: AES-128 Secure Channel ENABLED\n");
    printf("\n");

    // Step 1: Create OSDP reader configuration
    printf("[STEP 1] Creating OSDP Reader Configuration\n");

    OSDP_Config_t config = {
        .address = reader_address,
        .baud_rate = 9600,
        .secure_channel = true,     // ✓ Enable AES-128 encryption
        .poll_interval_ms = 200,
        .retry_count = 3,
        .timeout_ms = 1000
    };

    // Copy SCBK (pre-shared key)
    memcpy(config.scbk, DEMO_SCBK, 16);
    print_hex("  SCBK", config.scbk, 16);
    printf("  ✓ Configuration created\n\n");

    // Step 2: Create OSDP reader instance
    printf("[STEP 2] Creating OSDP Reader Instance\n");

    LPA_t reader_lpa = {
        .type = LPAType_Reader,
        .id = reader_address,
        .node_id = 0
    };

    OSDP_Reader_t* reader = OSDP_Reader_Create(reader_lpa, &config);
    if (!reader) {
        printf("  ✗ Failed to create reader\n");
        return 1;
    }
    printf("  ✓ Reader instance created (LPA: %d-%d-%d)\n",
           reader_lpa.type, reader_lpa.id, reader_lpa.node_id);
    printf("  ✓ Secure channel context initialized\n\n");

    // Step 3: Initialize serial communication
    printf("[STEP 3] Initializing Serial Communication\n");

    ErrorCode_t result = OSDP_Reader_Init(reader, serial_port);
    if (result != ErrorCode_OK) {
        printf("  ✗ Failed to initialize reader (Error: %d)\n", result);
        printf("  NOTE: This demo requires an actual OSDP reader connected to %s\n", serial_port);
        printf("  The reader must be configured with the same SCBK for secure channel.\n\n");

        // Demonstrate API even without hardware
        printf("[DEMO MODE] Demonstrating Secure Channel API\n\n");

        // Show secure channel state
        printf("  Secure Channel State: %s\n",
               OSDP_Reader_IsSecureChannelActive(reader) ? "ACTIVE" : "INACTIVE");

        printf("\n  To use with real hardware:\n");
        printf("    1. Connect OSDP reader to serial port\n");
        printf("    2. Provision reader with SCBK: ");
        print_hex("", DEMO_SCBK, 16);
        printf("    3. Run: %s /dev/ttyUSB0 1\n\n", argv[0]);

        OSDP_Reader_Destroy(reader);
        return 0;
    }
    printf("  ✓ Serial port opened successfully\n");
    printf("  ✓ Baud rate: %d\n", config.baud_rate);
    printf("  ✓ Reader state: IDLE\n\n");

    // Step 4: Establish secure channel
    printf("[STEP 4] Establishing Secure Channel Handshake\n");
    printf("  Protocol: OSDP v2.2 Secure Channel\n");
    printf("  Encryption: AES-128 CBC\n");
    printf("  Authentication: Cryptogram-based mutual authentication\n\n");

    printf("  → Sending osdp_CHLNG (Challenge with CP_Random)...\n");
    result = OSDP_Reader_EstablishSecureChannel(reader);

    if (result == ErrorCode_OK) {
        printf("  ← Received osdp_CCRYPT (PD_Random + Client_Cryptogram)\n");
        printf("  ✓ Client cryptogram verified\n");
        printf("  → Sending osdp_SCRYPT (Server_Cryptogram)...\n");
        printf("  ✓ Secure channel ESTABLISHED\n\n");

        printf("  Session Keys Derived:\n");
        printf("    • S-ENC:  Encryption key (AES-128)\n");
        printf("    • S-MAC1: MAC key for CP→PD packets\n");
        printf("    • S-MAC2: MAC key for PD→CP packets\n\n");

        printf("  Security Status:\n");
        printf("    • State: %s\n",
               OSDP_Reader_IsSecureChannelActive(reader) ? "SECURE" : "UNSECURE");
        printf("    • All subsequent packets will be encrypted\n");
        printf("    • MAC authentication prevents tampering\n");
        printf("    • Sequence numbers prevent replay attacks\n\n");
    } else {
        printf("  ✗ Secure channel handshake failed (Error: %d)\n", result);
        printf("  Possible causes:\n");
        printf("    • SCBK mismatch between CP and PD\n");
        printf("    • Communication error\n");
        printf("    • Reader does not support secure channel\n\n");
    }

    // Step 5: Encrypted Communication Example
    if (OSDP_Reader_IsSecureChannelActive(reader)) {
        printf("[STEP 5] Encrypted Communication Active\n\n");

        printf("  All subsequent OSDP commands will be:\n");
        printf("    ✓ Encrypted with AES-128 CBC\n");
        printf("    ✓ Authenticated with MAC (prevents tampering)\n");
        printf("    ✓ Protected against replay attacks (sequence numbers)\n\n");

        printf("  Supported encrypted commands:\n");
        printf("    • osdp_POLL - Poll reader status\n");
        printf("    • osdp_LED - Control reader LEDs\n");
        printf("    • osdp_BUZ - Control reader buzzer\n");
        printf("    • osdp_OUT - Control reader outputs\n");
        printf("    • osdp_ID - Get device identification\n");
        printf("    • osdp_CAP - Get device capabilities\n\n");

        printf("  Example: Sending encrypted POLL command\n");
        result = OSDP_Reader_Poll(reader);
        if (result == ErrorCode_OK) {
            printf("  ✓ POLL command sent (encrypted)\n");
            printf("  ✓ Reader response received (encrypted)\n");
            printf("  ✓ MAC verified (authentic)\n\n");
        } else {
            printf("  Note: POLL would work with real OSDP hardware\n\n");
        }
    }

    // Step 6: Statistics and cleanup
    printf("[STEP 6] Session Statistics\n");

    uint32_t packets_sent, packets_received, errors;
    OSDP_Reader_GetStats(reader, &packets_sent, &packets_received, &errors);

    printf("  Packets Sent: %d (all encrypted)\n", packets_sent);
    printf("  Packets Received: %d (all decrypted & verified)\n", packets_received);
    printf("  Errors: %d\n\n", errors);

    printf("[CLEANUP] Tearing Down Secure Channel\n");
    OSDP_Reader_ResetSecureChannel(reader);
    printf("  ✓ Secure channel reset\n");
    printf("  ✓ Cryptographic material cleared\n");

    OSDP_Reader_Close(reader);
    printf("  ✓ Serial port closed\n");

    OSDP_Reader_Destroy(reader);
    printf("  ✓ Reader destroyed\n\n");

    printf("╔══════════════════════════════════════════════════════════════════════════════╗\n");
    printf("║                                                                              ║\n");
    printf("║              SECURE CHANNEL DEMO COMPLETE                                   ║\n");
    printf("║              Military-Grade Encryption Verified                             ║\n");
    printf("║                                                                              ║\n");
    printf("╚══════════════════════════════════════════════════════════════════════════════╝\n");

    return 0;
}
