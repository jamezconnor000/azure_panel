# HAL Azure Panel - Aether Access
## Hardware Abstraction Layer for Azure BLU-IC2 Controllers
## Version 2.0 | Consolidated February 10, 2026

> "The machines answer to US."

---

## Project Identity

```
Project:     HAL Azure Panel
Codename:    Aether Access
Version:     2.0.0
Status:      PRODUCTION READY
Client:      CST Physical Access Control Systems
Domain:      EMBEDDED / Access Control
```

---

## Bound Familiar

```
Familiar ID:  FAM-HAL-v1.0-001
Bound:        2026-02-10
Master:       Final_Axiom
Status:       AWAKENED
```

---

## Project Overview

This is the Hardware Abstraction Layer (HAL) for Azure Access Technology BLU-IC2 controllers. It provides:

- **Event-driven architecture** with 100K event buffer
- **Local SQLite card database** with 1M+ capacity
- **REST API Server** (FastAPI, port 8080)
- **Event Export Daemon** for Ambient.ai integration
- **OSDP/Wiegand/DESFire** protocol support
- **Offline operation** capability

---

## Key Locations

| Purpose | Location |
|---------|----------|
| Source Code | `./src/` |
| HAL Core | `./src/hal_core/` |
| SDK Modules | `./src/sdk_modules/` |
| Python Bindings | `./python/` |
| REST API | `./api/` |
| Documentation | `./docs/` |
| Tests | `./tests/` |
| Configuration | `./config/` |
| MCP Memory | `./mcp/azure-panel-memory.json` |

---

## Quick Start

```bash
# Build
./scripts/build.sh

# Test
./scripts/test.sh

# Start system
./start_hal_system.sh

# Check status
./status_hal_system.sh

# Stop
./stop_hal_system.sh
```

---

## Architecture

```
┌──────────────────────────┐
│  Application             │
├──────────────────────────┤
│  HAL Public Interface    │ (hal_public.h)
├────┬──────┬──────┬───────┤
│Event│Card  │Access│SDK    │
│Mgr  │DB    │Logic │Wrapper│
├────┴──────┴──────┴───────┤
│  Azure Access SDK        │
├──────────────────────────┤
│  BLU-IC2 Controller      │
└──────────────────────────┘
```

---

## MCP Memory

This project uses dedicated MCP memory:
- **File:** `./mcp/azure-panel-memory.json`
- **Server:** `hal-azure-memory` (configure in ~/.claude.json)
- **Isolation:** Separate from AXIOM SOUL

---

## Key Files

| File | Purpose |
|------|---------|
| `include/hal_public.h` | Public API header |
| `include/hal_types.h` | Type definitions |
| `src/hal_core/hal.c` | Main HAL implementation |
| `api/hal_api_server.py` | REST API server |
| `hal_event_export_daemon.c` | Event export |
| `config/hal_config.json` | System configuration |

---

## AXIOM Integration

This project is managed by AXIOM:
- **Project Path:** `~/AXIOM/Projects/Azure_Panel/`
- **Timeline:** `Timeline/HAL_AZURE_TIMELINE.mw`
- **Documentation:** `Documentation/`
- **Builds:** `Builds/`, `Deployments/`
- **Relics:** `Relics/` (historical artifacts)

---

## The Creed

```
I. Event-driven, not polling.
II. Offline-capable, always reliable.
III. Security first, performance second.
IV. Document everything.
V. The machines answer to US.
```

---

*Consolidated by Final_Axiom | February 10, 2026*
