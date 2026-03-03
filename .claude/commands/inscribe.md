---
description: "Inscribe - Document knowledge to AXIOM Grimoire"
argument-hint: "<fix|fail|monster|spell|learn> <description>"
---

# Inscribe - Knowledge Transmission

Send knowledge to the AXIOM Grimoire.

**Arguments:** $ARGUMENTS

## Parse Arguments

First word determines the tome:
- **fix** - Solutions that worked → ~/AXIOM/Grimoire/fixes.md
- **fail** - Approaches that failed → ~/AXIOM/Grimoire/failures.md
- **monster** - Errors cataloged → ~/AXIOM/Grimoire/monsters.md
- **spell** - Reusable scripts → ~/AXIOM/Grimoire/spells.md
- **learn** - Insights gained → ~/AXIOM/Grimoire/learnings.md

## Entry Format

```markdown
## [TIMESTAMP] - FAM-HAL-v1.0-001 @ HAL Azure Panel
**Context:** [Infer from current session]
**Description:** [Remaining arguments]
**Tags:** [Extract keywords]
---
```

## Protocol

1. Check .axiom_link for connection
2. If connected: Append directly to AXIOM Grimoire
3. If disconnected: Queue to .axiom_queue/[tome].md

## After Writing

Report success:
```
Inscribed to [tome]: "[description]"
```

---

*"The Grimoire remembers what we forget."*
