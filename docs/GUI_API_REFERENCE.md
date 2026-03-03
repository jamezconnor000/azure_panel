# HAL GUI API Reference v2 - Complete Edition

**Surpasses Lenel OnGuard, Mercury, and Other Enterprise Systems**

---

## 🎯 Overview

The HAL GUI API provides comprehensive REST endpoints for:
- Azure Panel I/O Monitoring
- Reader Health Monitoring
- I/O Control (Doors, Outputs, Relays)
- Mass Control Operations (Lockdown, Evacuation)
- Control Macros
- Real-time WebSocket Updates

**Base URL:** `http://localhost:8080`
**API Docs:** `http://localhost:8080/docs` (Automatic Swagger UI)
**WebSocket:** `ws://localhost:8080/ws/live`

---

## 📊 Azure Panel I/O Monitoring

### Get Panel I/O Status
```http
GET /api/v1/panels/{panel_id}/io
```

**Response:**
```json
{
  "panel_id": 1,
  "panel_name": "Panel 1",
  "inputs": [
    {
      "id": 1,
      "panel_id": 1,
      "name": "Main Door Contact",
      "type": "DOOR_CONTACT",
      "state": "INACTIVE",
      "last_change": "2025-11-08T14:30:00",
      "trigger_count_today": 156,
      "supervised": true,
      "resistance_ohms": 2200.0
    }
  ],
  "outputs": [
    {
      "id": 1,
      "panel_id": 1,
      "name": "Door Strike",
      "type": "STRIKE",
      "state": "INACTIVE",
      "last_activated": "2025-11-08T14:32:15",
      "activation_count_today": 156,
      "mode": "MOMENTARY",
      "duration_ms": 3000,
      "controlled_by": "Access Grant"
    }
  ],
  "relays": [
    {
      "id": 1,
      "panel_id": 1,
      "name": "Elevator Relay",
      "state": "INACTIVE",
      "last_change": "2025-11-08T14:00:00",
      "activation_count_today": 23,
      "mode": "PULSE",
      "pulse_duration_ms": 2000,
      "linked_to": "Floor 2 Access"
    }
  ],
  "last_update": "2025-11-08T14:35:00",
  "total_events_today": 378
}
```

### Get Panel Health
```http
GET /api/v1/panels/{panel_id}/health
```

**Response:**
```json
{
  "panel_id": 1,
  "panel_name": "Azure Panel 1",
  "overall_health": "excellent",
  "health_score": 96,
  "online": true,
  "uptime_hours": 168.5,
  "firmware_version": "2.4.1",
  "main_power": true,
  "battery_voltage": 13.2,
  "battery_charge_percent": 95.0,
  "battery_health": "excellent",
  "network_health": "excellent",
  "ip_address": "192.168.1.100",
  "network_uptime_percent": 99.9,
  "inputs_ok": 3,
  "inputs_fault": 0,
  "outputs_ok": 2,
  "outputs_fault": 0,
  "database_size_mb": 45.2,
  "errors_last_24h": 0
}
```

---

## 🏥 Reader Health Monitoring

### Get Reader Health
```http
GET /api/v1/readers/{reader_id}/health
```

**Response:**
```json
{
  "reader_id": 1,
  "reader_name": "Reader 1",
  "overall_health": "excellent",
  "health_score": 95,

  "comm_health": "excellent",
  "comm_uptime_percent": 99.8,
  "last_successful_comm": "2025-11-08T14:35:00",
  "failed_polls_last_hour": 0,
  "avg_response_time_ms": 45.2,
  "packet_loss_percent": 0.1,

  "sc_health": "excellent",
  "sc_handshake_success_rate": 100.0,
  "sc_mac_failure_rate": 0.0,
  "sc_cryptogram_failure_rate": 0.0,
  "sc_avg_handshake_time_ms": 285.3,

  "hardware_health": "good",
  "tamper_status": "OK",
  "power_voltage": 12.3,
  "power_status": "NORMAL",
  "temperature_celsius": 32.5,
  "led_status": "FUNCTIONAL",

  "card_reader_health": "excellent",
  "successful_reads_today": 156,
  "failed_reads_today": 2,
  "read_success_rate": 98.7,

  "firmware_version": "4.5.0",
  "firmware_up_to_date": true,

  "warnings": ["Temperature slightly elevated (32.5°C)"],
  "recommendations": ["Monitor temperature trend"]
}
```

### Get All Readers Health Summary
```http
GET /api/v1/readers/health/summary
```

---

## 🚪 Door Control (Lenel-style)

### Unlock Door
```http
POST /api/v1/doors/{door_id}/unlock
```

**Query Parameters:**
- `duration_seconds` (optional): Momentary unlock duration
- `reason` (optional): Reason for audit log

**Examples:**
```bash
# Unlock indefinitely
curl -X POST http://localhost:8080/api/v1/doors/1/unlock

# Momentary unlock (5 seconds)
curl -X POST "http://localhost:8080/api/v1/doors/1/unlock?duration_seconds=5"

# With reason
curl -X POST "http://localhost:8080/api/v1/doors/1/unlock?reason=VIP+visitor"
```

**Response:**
```json
{
  "success": true,
  "action": "activate",
  "target_id": 1,
  "target_type": "door",
  "message": "Door 1 unlocked for 5 seconds",
  "timestamp": "2025-11-08T14:35:00.123",
  "executed_by": "API"
}
```

### Lock Door
```http
POST /api/v1/doors/{door_id}/lock
```

### Door Lockdown
```http
POST /api/v1/doors/{door_id}/lockdown
```

**Body:**
```json
{
  "reason": "Emergency lockdown"
}
```

### Release Door
```http
POST /api/v1/doors/{door_id}/release
```

Returns door to normal operation.

---

## 🔌 Output Control

### Activate Output
```http
POST /api/v1/outputs/{output_id}/activate
```

**Query Parameters:**
- `duration_ms` (optional): Pulse duration

**Examples:**
```bash
# Activate indefinitely
curl -X POST http://localhost:8080/api/v1/outputs/1/activate

# Pulse for 2 seconds
curl -X POST "http://localhost:8080/api/v1/outputs/1/activate?duration_ms=2000"
```

### Deactivate Output
```http
POST /api/v1/outputs/{output_id}/deactivate
```

### Pulse Output
```http
POST /api/v1/outputs/{output_id}/pulse?duration_ms=1000
```

### Toggle Output
```http
POST /api/v1/outputs/{output_id}/toggle
```

---

## 🔄 Relay Control

### Activate Relay
```http
POST /api/v1/relays/{relay_id}/activate
```

**Query Parameters:**
- `duration_ms` (optional): Pulse duration

### Deactivate Relay
```http
POST /api/v1/relays/{relay_id}/deactivate
```

---

## 🚨 Mass Control (Emergency Operations)

### Emergency Lockdown
```http
POST /api/v1/control/lockdown
```

**Body:**
```json
{
  "reason": "Active shooter situation",
  "initiated_by": "Security Director"
}
```

**Response:**
```json
{
  "success": true,
  "action": "activate",
  "target_type": "ALL_DOORS",
  "message": "LOCKDOWN activated - all doors locked and secured",
  "timestamp": "2025-11-08T14:35:00"
}
```

### Emergency Unlock All
```http
POST /api/v1/control/unlock-all
```

**Body:**
```json
{
  "reason": "Fire evacuation",
  "initiated_by": "Fire Marshal"
}
```

### Return to Normal
```http
POST /api/v1/control/normal
```

---

## 🎭 Control Macros

### List Macros
```http
GET /api/v1/macros
```

**Response:**
```json
{
  "macros": [
    {
      "macro_id": 1,
      "name": "Emergency Lockdown",
      "description": "Lock all doors and disable all outputs"
    },
    {
      "macro_id": 2,
      "name": "Fire Evacuation",
      "description": "Unlock all doors for evacuation"
    },
    {
      "macro_id": 3,
      "name": "After Hours Mode",
      "description": "Secure building for night"
    },
    {
      "macro_id": 4,
      "name": "Morning Unlock",
      "description": "Unlock main entrances for business hours"
    }
  ]
}
```

### Execute Macro
```http
POST /api/v1/macros/{macro_id}/execute
```

**Examples:**
```bash
# Execute Emergency Lockdown
curl -X POST http://localhost:8080/api/v1/macros/1/execute

# Execute Fire Evacuation
curl -X POST http://localhost:8080/api/v1/macros/2/execute
```

---

## 🔓 Override Management

### Get Active Overrides
```http
GET /api/v1/overrides
```

**Response:**
```json
[
  {
    "override_id": 1,
    "target_type": "door",
    "target_id": 5,
    "target_name": "Server Room",
    "override_state": "LOCKED",
    "override_since": "2025-11-08T10:30:00",
    "override_by": "admin",
    "reason": "Maintenance in progress",
    "auto_release": "2025-11-08T17:00:00"
  }
]
```

### Clear Override
```http
DELETE /api/v1/overrides/{override_id}
```

---

## 🔴 WebSocket - Real-time Updates

### Connect
```javascript
const ws = new WebSocket('ws://localhost:8080/ws/live');

ws.onopen = () => {
  console.log('Connected to HAL Control Panel');

  // Subscribe to topics
  ws.send(JSON.stringify({
    action: 'subscribe',
    topics: ['io_changes', 'door_control', 'health_alerts']
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);

  switch(data.type) {
    case 'io_change':
      updateIODisplay(data.event);
      break;
    case 'door_control':
      updateDoorStatus(data);
      break;
    case 'mass_control':
      showAlert(data);
      break;
  }
};
```

### Message Types

**I/O Change:**
```json
{
  "type": "io_change",
  "event": {
    "panel_id": 1,
    "input_id": 1,
    "name": "Main Door Contact",
    "new_state": "ACTIVE",
    "timestamp": "2025-11-08T14:35:00"
  }
}
```

**Door Control:**
```json
{
  "type": "door_control",
  "action": "unlock",
  "door_id": 1,
  "result": {
    "success": true,
    "message": "Door unlocked"
  },
  "timestamp": "2025-11-08T14:35:00"
}
```

**Mass Control:**
```json
{
  "type": "mass_control",
  "action": "EMERGENCY_LOCKDOWN",
  "priority": "CRITICAL",
  "result": {
    "success": true,
    "message": "All doors locked"
  },
  "timestamp": "2025-11-08T14:35:00"
}
```

---

## 🔥 Usage Examples

### Python Client
```python
import requests

API_BASE = "http://localhost:8080/api/v1"

# Check panel I/O
response = requests.get(f"{API_BASE}/panels/1/io")
io_status = response.json()
print(f"Inputs: {len(io_status['inputs'])}")
print(f"Outputs: {len(io_status['outputs'])}")

# Unlock door
response = requests.post(f"{API_BASE}/doors/1/unlock?duration_seconds=5")
result = response.json()
print(result['message'])

# Get reader health
response = requests.get(f"{API_BASE}/readers/1/health")
health = response.json()
print(f"Health Score: {health['health_score']}/100")
print(f"Comm Health: {health['comm_health']}")

# Emergency lockdown
response = requests.post(
    f"{API_BASE}/control/lockdown",
    json={"reason": "Emergency", "initiated_by": "Admin"}
)
print(response.json())
```

### JavaScript/TypeScript
```typescript
// Unlock door
async function unlockDoor(doorId: number, duration?: number) {
  const url = `/api/v1/doors/${doorId}/unlock${duration ? `?duration_seconds=${duration}` : ''}`;
  const response = await fetch(url, { method: 'POST' });
  return await response.json();
}

// Get panel I/O
async function getPanelIO(panelId: number) {
  const response = await fetch(`/api/v1/panels/${panelId}/io`);
  return await response.json();
}

// Execute macro
async function executeMacro(macroId: number) {
  const response = await fetch(`/api/v1/macros/${macroId}/execute`, {
    method: 'POST'
  });
  return await response.json();
}
```

### curl Commands
```bash
# Panel I/O
curl http://localhost:8080/api/v1/panels/1/io

# Reader Health
curl http://localhost:8080/api/v1/readers/1/health

# Unlock door
curl -X POST http://localhost:8080/api/v1/doors/1/unlock

# Pulse output
curl -X POST "http://localhost:8080/api/v1/outputs/1/pulse?duration_ms=2000"

# Emergency lockdown
curl -X POST http://localhost:8080/api/v1/control/lockdown \
  -H "Content-Type: application/json" \
  -d '{"reason": "Emergency", "initiated_by": "Admin"}'

# Execute macro
curl -X POST http://localhost:8080/api/v1/macros/1/execute
```

---

## 🏆 Comparison with Competition

Feature | HAL GUI | Lenel OnGuard | Mercury Partners
--------|---------|---------------|------------------
REST API | ✅ Yes | ⚠️ Limited | ⚠️ Varies
WebSocket | ✅ Yes | ❌ No | ❌ Rare
I/O Monitoring | ✅ Comprehensive | ✅ Yes | ⚠️ Basic
I/O Control | ✅ Full API | ⚠️ GUI only | ⚠️ Varies
Reader Health | ✅ Deep metrics | ⚠️ Basic | ⚠️ Limited
Panel Health | ✅ Comprehensive | ⚠️ Basic | ⚠️ Limited
Secure Channel | ✅ Deep visibility | ❌ No | ⚠️ Basic
Mass Control | ✅ API + Macros | ✅ GUI | ⚠️ Limited
Auto Docs | ✅ Swagger | ❌ No | ❌ Rare
Open API | ✅ Yes | ❌ Proprietary | ⚠️ Varies
Cost | ✅ Free/Open | ❌ Expensive | ⚠️ Varies

---

## 🚀 Getting Started

1. **Install Dependencies:**
```bash
cd gui/backend
pip install -r requirements.txt
```

2. **Start Server:**
```bash
python hal_gui_server_v2.py
```

3. **Access API Docs:**
```
http://localhost:8080/docs
```

4. **Test API:**
```bash
curl http://localhost:8080/api/v1/panels/1/io
```

---

## 📖 API Documentation

**Interactive Swagger UI:** http://localhost:8080/docs
**ReDoc:** http://localhost:8080/redoc (Alternative documentation)

All endpoints are automatically documented with:
- Request/response schemas
- Example payloads
- Try-it-out functionality
- Type validation

---

**This API provides everything Lenel OnGuard does, but with:**
- ✅ Modern REST architecture
- ✅ Real-time WebSocket support
- ✅ Comprehensive health monitoring
- ✅ Better I/O control
- ✅ Deeper secure channel visibility
- ✅ Open, documented API
- ✅ No licensing fees

**Ready to use NOW!**
