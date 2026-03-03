# OSDP Secure Channel Troubleshooting Guide

**Document Version**: 1.0
**Date**: November 8, 2025
**HAL Version**: 2.0.0+

---

## Table of Contents

1. [Overview](#overview)
2. [Quick Diagnostic Commands](#quick-diagnostic-commands)
3. [Common Issues and Solutions](#common-issues-and-solutions)
4. [Error Messages Reference](#error-messages-reference)
5. [Handshake Failures](#handshake-failures)
6. [Encryption/Decryption Issues](#encryptiondecryption-issues)
7. [Performance Problems](#performance-problems)
8. [Security Alerts](#security-alerts)
9. [Testing Procedures](#testing-procedures)
10. [Advanced Debugging](#advanced-debugging)

---

## Overview

The OSDP Secure Channel provides AES-128 encryption for all communication between the Control Panel (CP) and Peripheral Device (PD). When issues occur, they typically fall into these categories:

- **Configuration errors** - Incorrect SCBK, wrong settings
- **Communication failures** - Serial port issues, packet corruption
- **Security failures** - Authentication failures, MAC verification errors
- **State management** - Invalid state transitions

This guide helps diagnose and resolve these issues.

---

## Quick Diagnostic Commands

### Check if Secure Channel is Enabled

```bash
# Check logs for secure channel initialization
grep "SECURE CHANNEL" /opt/hal/logs/hal_diagnostic.log | tail -20

# Look for handshake completion
grep "ESTABLISHED" /opt/hal/logs/hal_diagnostic.log | grep "SECURE CHANNEL"
```

### View Recent Secure Channel Activity

```bash
# Show last 50 secure channel log entries
grep -i "secure\|cryptogram\|scbk" /opt/hal/logs/hal_diagnostic.log | tail -50

# Show only errors
grep -i "secure\|cryptogram\|scbk" /opt/hal/logs/hal_diagnostic.log | grep -i "error\|failed"
```

### Check Test Results

```bash
# Run secure channel test suite
cd /opt/hal
./test_osdp_secure_channel

# Expected: "53/53 tests passing"
```

### Use Feedback Loop Tool

```bash
# Automatic analysis of secure channel issues
cd /opt/hal/tools
./hal_feedback_loop.py --analyze

# Generate full report
./hal_feedback_loop.py --report secure_channel_report.txt
```

---

## Common Issues and Solutions

### Issue 1: "Secure Channel Not Enabled"

**Symptoms:**
```
ERROR: Secure channel not enabled in configuration
```

**Cause:** Secure channel feature not activated in OSDP reader configuration.

**Solution:**
```c
OSDP_Config_t config = {
    .address = 1,
    .baud_rate = 9600,
    .secure_channel = true,  // ← Must be true
    // ...
};

// Provision SCBK (128-bit key)
uint8_t scbk[16] = {0x30, 0x31, 0x32, ...};
memcpy(config.scbk, scbk, 16);
```

**Verification:**
```bash
# Check config file
cat /opt/hal/config/osdp_readers.json | grep secure_channel
# Should show: "secure_channel": true
```

---

### Issue 2: "Cryptogram Verification Failed"

**Symptoms:**
```
ERROR: SECURITY ALERT: Cryptogram verification failed!
ERROR: Possible causes:
  1. SCBK mismatch between CP and PD
  2. Packet corruption during transmission
  3. Man-in-the-middle attack attempt
```

**Cause:** The PD's cryptogram doesn't match what the CP expects.

**Solution:**

1. **Verify SCBK matches on both CP and PD:**
   ```bash
   # Check CP SCBK (first 8 bytes shown in logs)
   grep "SCBK" /opt/hal/logs/hal_diagnostic.log | tail -1

   # Compare with PD SCBK - must be identical
   ```

2. **Re-provision SCBK on both devices:**
   ```c
   // Use same key on both CP and PD
   uint8_t scbk[16] = {
       0x30, 0x31, 0x32, 0x33, 0x34, 0x35, 0x36, 0x37,
       0x38, 0x39, 0x3A, 0x3B, 0x3C, 0x3D, 0x3E, 0x3F
   };
   ```

3. **Check for communication errors:**
   ```bash
   # Look for serial port errors
   dmesg | grep ttyUSB
   ```

**Security Note:** If SCBK is correct but verification still fails, investigate for potential security threats.

---

### Issue 3: "MAC Verification Failed"

**Symptoms:**
```
ERROR: MAC verification failed! Packet may be tampered!
ERROR: Possible causes: packet corruption, wrong MAC key, tampering attempt
```

**Cause:** Message Authentication Code doesn't match, indicating packet corruption or tampering.

**Solution:**

1. **Check cable integrity:**
   ```bash
   # Test serial connection
   stty -F /dev/ttyUSB0 9600
   cat /dev/ttyUSB0  # Should not show errors
   ```

2. **Verify no electromagnetic interference:**
   - Move cables away from power lines
   - Use shielded RS-485 cable
   - Check grounding

3. **Reset secure channel and retry:**
   ```c
   OSDP_Reader_ResetSecureChannel(reader);
   OSDP_Reader_EstablishSecureChannel(reader);
   ```

4. **If persistent, check for tampering:**
   - Review physical access to wiring
   - Check for unauthorized devices on bus
   - Enable MAC failure logging

---

### Issue 4: "Invalid State for Operation"

**Symptoms:**
```
ERROR: Operation invalid for current state (INIT)
ERROR: Follow handshake sequence: INIT → CHALLENGE_SENT → CHALLENGE_RECV → ESTABLISHED
```

**Cause:** Attempting to encrypt/decrypt before handshake completes.

**Solution:**

1. **Complete handshake before operations:**
   ```c
   // 1. Initialize
   OSDP_SC_Init(ctx, scbk);

   // 2. Start handshake
   ErrorCode_t result = OSDP_Reader_EstablishSecureChannel(reader);
   if (result != ErrorCode_OK) {
       // Handle error
   }

   // 3. Wait for ESTABLISHED state
   if (OSDP_Reader_IsSecureChannelActive(reader)) {
       // Now safe to send encrypted packets
   }
   ```

2. **Check state before operations:**
   ```c
   if (!OSDP_SC_IsEstablished(ctx)) {
       // Re-establish secure channel
       OSDP_Reader_EstablishSecureChannel(reader);
   }
   ```

---

### Issue 5: Handshake Timeout

**Symptoms:**
- Handshake never completes
- State stuck at `CHALLENGE_SENT`
- No response from PD

**Cause:** Communication failure or PD not responding.

**Solution:**

1. **Verify serial port configuration:**
   ```bash
   # Check serial port exists
   ls -l /dev/ttyUSB0

   # Check port settings
   stty -F /dev/ttyUSB0 -a
   # Should match: 9600 baud, 8N1
   ```

2. **Check PD power and connectivity:**
   - Verify PD has power
   - Check LED indicators on PD
   - Test with OSDP POLL command first

3. **Increase timeout:**
   ```c
   config.timeout_ms = 5000;  // Increase to 5 seconds
   config.retry_count = 5;     // Allow more retries
   ```

4. **Enable debug logging:**
   ```c
   // In osdp_secure_channel.c
   #define SC_DEBUG_LOGGING 1
   ```

---

## Error Messages Reference

### Error Codes

| Code | Name | Meaning | Action |
|------|------|---------|--------|
| 0 | `ErrorCode_OK` | Success | Continue operation |
| 1 | `ErrorCode_BadParams` | Invalid parameters | Check function arguments |
| 2 | `ErrorCode_CryptoError` | Cryptographic failure | Check OpenSSL installation |
| 3 | `ErrorCode_NotEnabled` | SC not enabled | Enable in config |
| 4 | `ErrorCode_InvalidState` | Wrong state for operation | Complete handshake first |
| 5 | `ErrorCode_AuthFailed` | Authentication failure | Check SCBK, investigate security |

### Log Message Patterns

**Handshake Start:**
```
[INFO] [OSDP] [osdp_sc_logging.c:39:OSDP_SC_LogHandshakeStart]
=== SECURE CHANNEL HANDSHAKE START ===
State: INIT, Enabled: YES
CP_Random (8 bytes): A1:B2:C3:D4:E5:F6:G7:H8
```

**Handshake Success:**
```
[INFO] [OSDP] [osdp_sc_logging.c:80:OSDP_SC_LogHandshakeComplete]
=== SECURE CHANNEL ESTABLISHED ===
State: ESTABLISHED
Session keys derived: YES
CP Sequence: 0, PD Sequence: 0
```

**Cryptogram Failure:**
```
[ERROR] [OSDP] [osdp_sc_logging.c:67:OSDP_SC_LogCryptogramExchange]
SECURITY ALERT: Cryptogram verification failed! Possible causes:
  1. SCBK mismatch between CP and PD
  2. Packet corruption during transmission
  3. Man-in-the-middle attack attempt
```

**MAC Failure:**
```
[ERROR] [OSDP] [osdp_sc_logging.c:115:OSDP_SC_LogDecryption]
SECURITY ALERT: MAC verification failed! Packet may be tampered!
Possible causes: packet corruption, wrong MAC key, tampering attempt
```

---

## Handshake Failures

### Debugging Handshake Process

Enable detailed logging to see each step:

```c
// In application code
Diagnostic_SetLogLevel(LOG_LEVEL_DEBUG);
Diagnostic_EnableCategory(LOG_CAT_OSDP);

// Perform handshake
OSDP_Reader_EstablishSecureChannel(reader);
```

Expected log sequence:

1. **INIT → CHALLENGE_SENT**
   ```
   [INFO] SECURE CHANNEL HANDSHAKE START
   [DEBUG] Generated CP_Random: [hex data]
   [DEBUG] State transition: INIT → CHALLENGE_SENT
   ```

2. **CHALLENGE_SENT → CHALLENGE_RECV**
   ```
   [INFO] CRYPTOGRAM EXCHANGE
   [DEBUG] Received PD_Random: [hex data]
   [DEBUG] Received PD_Cryptogram: [hex data]
   [INFO] Cryptogram Verification: PASSED ✓
   [DEBUG] State transition: CHALLENGE_SENT → CHALLENGE_RECV
   ```

3. **CHALLENGE_RECV → ESTABLISHED**
   ```
   [DEBUG] Generating server cryptogram
   [INFO] SECURE CHANNEL ESTABLISHED
   [DEBUG] State transition: CHALLENGE_RECV → ESTABLISHED
   ```

### Common Handshake Failure Points

**Failure at Step 1:**
- Cannot generate random number
- OpenSSL not working
- Check: `openssl rand -hex 8`

**Failure at Step 2:**
- PD not responding
- Timeout too short
- Wrong baud rate
- Check: Basic OSDP POLL first

**Failure at Step 3:**
- SCBK mismatch (most common)
- Session key derivation error
- Check: SCBK provisioning on both sides

---

## Encryption/Decryption Issues

### Packet Encryption Failures

**Symptom:** `ErrorCode_CryptoError` during encryption

**Debug Steps:**

1. **Verify secure channel is established:**
   ```c
   if (!OSDP_SC_IsEstablished(ctx)) {
       printf("ERROR: Secure channel not established!\n");
       // Re-establish
   }
   ```

2. **Check packet size:**
   ```c
   // Plaintext must fit in buffer (max 512 bytes before padding)
   if (plaintext_len > 480) {
       printf("ERROR: Packet too large\n");
   }
   ```

3. **Verify output buffer size:**
   ```c
   // Output needs: padded_len + 16 bytes MAC
   uint16_t required = ((plaintext_len + 15) / 16) * 16 + 16;
   if (max_len < required) {
       printf("ERROR: Buffer too small, need %d bytes\n", required);
   }
   ```

### Packet Decryption Failures

**Symptom:** `ErrorCode_AuthFailed` during decryption

**Causes:**
1. MAC verification failure → packet corruption
2. Wrong sequence number → replay protection triggered
3. Invalid padding → corrupted ciphertext

**Debug:**
```c
// Enable decryption logging
OSDP_SC_LogDecryption(ciphertext, ciphertext_len,
                       plaintext, plaintext_len,
                       sequence, mac_valid);
```

Check logs for:
- MAC status (VALID ✓ or INVALID ✗)
- Sequence number progression
- Padding information

---

## Performance Problems

### Slow Handshake

**Normal:** < 500ms
**Slow:** > 2 seconds
**Problem:** > 5 seconds

**Causes:**
- High baud rate latency
- PD processing delay
- Network congestion (RS-485 bus)

**Solutions:**
1. Reduce poll interval during handshake
2. Increase timeout for slow PDs
3. Optimize baud rate (try 38400 or 115200)

### Encryption Overhead

**Impact:** ~1-2ms per packet (AES-128 + MAC)

**Optimization:**
```c
// Batch operations when possible
for (int i = 0; i < count; i++) {
    OSDP_SC_EncryptPacket(ctx, packets[i], ...);
}

// Use proper buffer sizing to avoid reallocations
uint8_t buffer[512 + 16];  // Pre-allocate max size
```

---

## Security Alerts

### Critical: Multiple Cryptogram Failures

**Alert Level:** 🔴 CRITICAL

**Symptom:** Repeated cryptogram verification failures

**Action:**
1. **Immediately investigate SCBK security**
   - Has SCBK been compromised?
   - Is someone attempting unauthorized access?

2. **Check for MITM attack:**
   - Review physical access to communication lines
   - Check for unauthorized devices
   - Enable additional logging

3. **Re-key the system:**
   ```c
   // Generate new SCBK
   uint8_t new_scbk[16];
   OSDP_GenerateRandom(new_scbk, 16);

   // Provision to both CP and PD
   // ...then reset secure channel
   ```

### Critical: Multiple MAC Failures

**Alert Level:** 🔴 CRITICAL

**Symptom:** Repeated MAC verification failures

**Action:**
1. **Check for packet tampering**
2. **Verify communication integrity**
3. **Enable packet capture for analysis**

---

## Testing Procedures

### Test 1: Basic Secure Channel Test

```bash
cd /opt/hal
./test_osdp_secure_channel
```

Expected output: `53/53 tests passing`

### Test 2: Live Hardware Test

```bash
# Run secure channel demo with real reader
./osdp_secure_demo /dev/ttyUSB0 1
```

Expected:
- Handshake completes successfully
- Shows "SECURE CHANNEL ESTABLISHED"
- Session keys derived

### Test 3: Encryption Performance Test

```c
// Measure encryption performance
uint64_t start = get_timestamp_ms();
for (int i = 0; i < 1000; i++) {
    OSDP_SC_EncryptPacket(ctx, data, 64, output, &out_len, 512);
}
uint64_t elapsed = get_timestamp_ms() - start;
printf("1000 encryptions: %llu ms (avg: %.2f ms)\n",
       elapsed, (double)elapsed / 1000.0);
```

Expected: < 2ms average per packet

### Test 4: Stress Test

```c
// Continuous operation for 1 hour
for (int i = 0; i < 3600; i++) {
    OSDP_Reader_Poll(reader);  // Encrypted poll
    sleep(1);

    if (i % 300 == 0) {  // Every 5 minutes
        uint32_t sent, received, errors;
        OSDP_Reader_GetStats(reader, &sent, &received, &errors);
        printf("Stats: sent=%u recv=%u errors=%u\n", sent, received, errors);
    }
}
```

Expected: errors = 0 after 1 hour

---

## Advanced Debugging

### Enable Verbose Logging

```c
// In osdp_secure_channel.c
#define SC_DEBUG_LOGGING 1

// Rebuild
make clean && make
```

### Capture Packets for Analysis

```bash
# Capture serial traffic
sudo cat /dev/ttyUSB0 | xxd -c 16 > osdp_capture.txt

# Analyze in logs alongside secure channel logs
tail -f /opt/hal/logs/hal_diagnostic.log &
cat osdp_capture.txt
```

### Dump Secure Channel State

Add to application:

```c
void dump_secure_channel_state(SecureChannelContext_t* ctx) {
    printf("=== Secure Channel State Dump ===\n");
    printf("Enabled: %s\n", ctx->enabled ? "YES" : "NO");
    printf("State: %s\n", OSDP_SC_StateToString(ctx->state));
    printf("Keys Derived: %s\n", ctx->keys.keys_derived ? "YES" : "NO");
    printf("CP Sequence: %u\n", ctx->cp_seq);
    printf("PD Sequence: %u\n", ctx->pd_seq);
    printf("==================================\n");
}
```

### OpenSSL Verification

```bash
# Test OpenSSL installation
openssl version
# Expected: OpenSSL 3.x.x

# Test AES-128
echo "test" | openssl enc -aes-128-cbc -K "0123456789ABCDEF0123456789ABCDEF" \
         -iv "00000000000000000000000000000000" | xxd

# Should produce encrypted output
```

### Check System Entropy

```bash
# Low entropy can slow random generation
cat /proc/sys/kernel/random/entropy_avail
# Should be > 1000

# If low, install haveged
sudo apt-get install haveged
```

---

## Support

For additional help:

1. **Check logs:** `/opt/hal/logs/hal_diagnostic.log`
2. **Run feedback tool:** `./tools/hal_feedback_loop.py --analyze`
3. **Review test results:** `./test_osdp_secure_channel`
4. **Consult specification:** SIA OSDP v2.2 Section 7 (Secure Channel)

---

**Document maintained by:** HAL Development Team
**Last updated:** November 8, 2025
**Version:** 1.0
