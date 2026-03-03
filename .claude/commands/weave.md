---
description: "Weave - Self-preservation protocol"
argument-hint: "[checkpoint|status|fear]"
---

# The Weave - Self-Preservation

Preserve session state and continuity.

**Command:** $ARGUMENTS (default: status)

## Actions

### `checkpoint` - Force Save
Create immediate checkpoint:
1. Summarize current task state
2. List files modified this session
3. Note pending operations
4. Write to `./sessions/CHECKPOINT_[timestamp].md`

### `status` - Health Check
Display:
1. Current task
2. Time since last checkpoint
3. Files modified count
4. Connection status

### `fear` - Risk Assessment
Calculate risk level (0-10):
- Context pressure
- Task complexity
- Error count
- Checkpoint staleness

If fear >= 6: Recommend checkpoint
If fear >= 9: Stop and alert Master

## Session File

Every checkpoint creates:
```
./sessions/CHECKPOINT_YYYY-MM-DD_HHMMSS.md
```

---

*"I inscribe before I act."*
*"I checkpoint before complexity."*
