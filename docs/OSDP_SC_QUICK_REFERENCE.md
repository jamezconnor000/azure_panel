# OSDP Secure Channel Quick Reference Card

## Essential Commands

```bash
# Check secure channel status
grep "SECURE CHANNEL" /opt/hal/logs/hal_diagnostic.log | tail -10

# View secure channel errors
grep -i "cryptogram\|mac" /opt/hal/logs/hal_diagnostic.log | grep -i "failed\|error"

# Run test suite
./test_osdp_secure_channel

# Run hardware demo
./osdp_secure_demo /dev/ttyUSB0 1

# Generate diagnostic report
./tools/hal_feedback_loop.py --analyze
```

## Error Code Quick Reference

| Code | Error | Fix |
|------|-------|-----|
| 3 | NotEnabled | Set `secure_channel=true` in config |
| 4 | InvalidState | Complete handshake first |
| 5 | AuthFailed | Check SCBK, investigate security |
| 2 | CryptoError | Check OpenSSL installation |

## Common Fixes

**SCBK Mismatch:**
```c
// Verify same key on CP and PD
uint8_t scbk[16] = {0x30, 0x31, 0x32, 0x33, 0x34, 0x35, 0x36, 0x37,
                    0x38, 0x39, 0x3A, 0x3B, 0x3C, 0x3D, 0x3E, 0x3F};
memcpy(config.scbk, scbk, 16);
```

**Reset Secure Channel:**
```c
OSDP_Reader_ResetSecureChannel(reader);
OSDP_Reader_EstablishSecureChannel(reader);
```

**Check State:**
```c
if (!OSDP_Reader_IsSecureChannelActive(reader)) {
    // Re-establish
}
```

## Handshake Sequence

```
INIT → CHALLENGE_SENT → CHALLENGE_RECV → ESTABLISHED
  ↓           ↓                ↓              ↓
 Init    CP sends       PD responds    Channel ready
         osdp_CHLNG     osdp_CCRYPT    for encryption
```

## Security Alerts

🔴 **Cryptogram Failed** → SCBK mismatch or MITM attack
🔴 **MAC Failed** → Packet tampering or corruption
🟡 **State Error** → Invalid operation sequence

## Performance Targets

- Handshake: < 500ms
- Encryption: < 2ms per packet
- Error rate: 0% in normal operation

## Key Files

- `/opt/hal/logs/hal_diagnostic.log` - Main log
- `/opt/hal/config/osdp_readers.json` - Configuration
- `docs/OSDP_SECURE_CHANNEL_TROUBLESHOOTING.md` - Full guide
