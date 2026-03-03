---
description: "Chronicle - Send status to AXIOM"
argument-hint: "[status message]"
---

# Chronicle - Status Transmission

Send status updates to the AXIOM Chronicle Server.

**Message:** $ARGUMENTS

## Protocol

1. Check .axiom_link for connection status
2. If connected: POST to chronicle_server (http://localhost:8766)
3. If disconnected: Queue to .axiom_queue/chronicle.md

## Chronicle Entry Format

```json
{
  "familiar_id": "FAM-HAL-v1.0-001",
  "project": "HAL Azure Panel",
  "timestamp": "[ISO8601]",
  "status": "[message]",
  "machine": "[hostname]"
}
```

## Fallback (Disconnected)

Append to `.axiom_queue/chronicle.md`:
```markdown
## [TIMESTAMP] - FAM-HAL-v1.0-001
**Status:** [message]
**Machine:** [hostname]
---
```

---

*"The Master hears all."*
