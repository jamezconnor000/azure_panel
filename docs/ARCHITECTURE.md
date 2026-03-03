# HAL Architecture

## Overview

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

## Components

### Event Manager
- Manages event buffer (100K capacity)
- Handles subscriptions
- Guaranteed delivery with ACK
- Recovery on disconnect

### Card Database
- SQLite local storage
- Complex queries with AND/OR
- 1M+ card capacity
- Dynamic field updates

### Access Logic
- Permission checking
- Schedule validation
- APB tracking
- Multiple card format support

### SDK Wrapper
- Azure SDK integration
- Command serialization
- Event marshalling

## Event Flow

```
Card Presented at Reader
        ↓
Card Validated Against Local DB
        ↓
Access Decision Made (Grant/Deny)
        ↓
Physical Action (Strike, LED, Buzzer)
        ↓
Event Generated (AccessGrantEvent or AccessDenyEvent)
        ↓
Event Buffered in 100K Buffer
        ↓
Subscribers Notified (with Backpressure)
        ↓
Subscribers Acknowledge Receipt
        ↓
Event Can Be Pruned from Buffer
```

## Threading Model

- Single-threaded by default
- Event queue is thread-safe
- Card database uses SQLite locking
- Application responsible for multi-threaded usage

## Performance

- Access Decision: <250ms
- Event Generation: <1ms
- Event Buffer: 100,000 capacity
- Database: Up to 1,000,000 cards
- Query Performance: <100ms for complex logic

## Data Flow

```
HAL Application
    │
    ├─→ Add Cards to Database
    │
    ├─→ Subscribe to Events
    │
    └─→ Loop:
         ├─ Receive Event (Card Presented)
         ├─ Decide Access (Query DB + Rules)
         ├─ Execute Action (Energize Relay)
         ├─ Generate Event
         └─ Send Acknowledgement
```
