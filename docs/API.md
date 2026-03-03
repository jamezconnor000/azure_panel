# HAL API Reference

## Core Functions

### HAL_Create
Create HAL instance.

```c
HAL_t* HAL_Create(const HALConfig_t* config);
```

### HAL_Destroy
Destroy HAL instance.

```c
void HAL_Destroy(HAL_t* hal);
```

### HAL_Connect
Connect to controller.

```c
ErrorCode_t HAL_Connect(HAL_t* hal, const char* addr, uint16_t port);
```

## Card Operations

### HAL_AddCard
Add card to database.

```c
ErrorCode_t HAL_AddCard(HAL_t* hal, const Card_t* card);
```

### HAL_GetCard
Get card from database.

```c
ErrorCode_t HAL_GetCard(HAL_t* hal, CardId_t card_id, Card_t* out_card);
```

### HAL_UpdateCard
Update existing card.

```c
ErrorCode_t HAL_UpdateCard(HAL_t* hal, const Card_t* card);
```

### HAL_DeleteCard
Delete card from database.

```c
ErrorCode_t HAL_DeleteCard(HAL_t* hal, CardId_t card_id);
```

## Access Control

### HAL_DecideAccess
Make access control decision.

```c
ErrorCode_t HAL_DecideAccess(HAL_t* hal, CardId_t card_id, LPA_t reader_lpa, AccessResult_t* result);
```

Returns:
- `result->decision`: GRANT or DENY
- `result->strike_time_ms`: Door strike duration
- `result->deny_reason`: If denied

### HAL_EnergizeRelay
Energize door strike relay.

```c
ErrorCode_t HAL_EnergizeRelay(HAL_t* hal, uint32_t relay_id, uint32_t duration_ms);
```

## Event Management

### HAL_SubscribeToEvents
Subscribe to event stream.

```c
ErrorCode_t HAL_SubscribeToEvents(HAL_t* hal, const EventSubscription_t* subscription);
```

### HAL_SendEventAck
Acknowledge received events.

```c
ErrorCode_t HAL_SendEventAck(HAL_t* hal, const EventAck_t* ack);
```

### HAL_GetEventBufferStatus
Query event buffer status.

```c
ErrorCode_t HAL_GetEventBufferStatus(HAL_t* hal, EventBufferStatus_t* status);
```

## Error Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 11 | Node offline |
| 21 | Bad parameters |
| 22 | Object not found |
| 24 | Database error |

## Types

### Card_t
```c
typedef struct {
    CardId_t card_id;
    FacilityCode_t facility_code;
    uint32_t card_number;
    uint8_t card_format_id;
    time_t activation_time;
    time_t deactivation_time;
    uint16_t use_limit;
    uint8_t is_blocked;
} Card_t;
```

### AccessResult_t
```c
typedef struct {
    AccessDecision_t decision;      // GRANT or DENY
    DenyReason_t deny_reason;       // If denied
    uint32_t strike_time_ms;        // Strike duration
    uint32_t relay_id;              // Which relay
} AccessResult_t;
```

See `include/hal_types.h` for complete type definitions.
