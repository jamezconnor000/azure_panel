# HAL GUI API - Integration Examples

This directory contains comprehensive examples for integrating with the HAL Control Panel API.

## 📁 Files

| File | Description |
|------|-------------|
| `python_client_example.py` | Complete Python client library with usage examples |
| `javascript_client_example.js` | Node.js/JavaScript client with WebSocket support |
| `bash_examples.sh` | Command-line curl examples for all API endpoints |
| `monitoring_dashboard.py` | Real-time monitoring dashboard (production-ready) |

---

## 🚀 Quick Start

### Prerequisites

**For Python examples:**
```bash
pip install requests
```

**For JavaScript examples:**
```bash
npm install axios ws
```

**For Bash examples:**
```bash
# Requires: curl, python3 (for JSON formatting)
# Already available on macOS and most Linux distributions
```

---

## 📖 Usage Examples

### 1. Python Client Library

**Basic Usage:**

```python
from python_client_example import HALClient

# Create client
client = HALClient(base_url="http://localhost:8080")

# Get panel I/O status
io_status = client.get_panel_io(panel_id=1)
print(f"Inputs: {len(io_status['inputs'])}")
print(f"Outputs: {len(io_status['outputs'])}")

# Get reader health
health = client.get_reader_health(reader_id=1)
print(f"Health Score: {health['health_score']}/100")
print(f"Overall: {health['overall_health']}")

# Unlock door (momentary - 5 seconds)
result = client.unlock_door(door_id=1, duration_seconds=5, reason="Admin access")
print(result['message'])

# Pulse output
result = client.pulse_output(output_id=1, duration_ms=2000)
print(result['message'])

# Emergency lockdown
result = client.emergency_lockdown(
    reason="Active shooter drill",
    initiated_by="Security Director"
)
print(result['message'])

# Execute macro
result = client.execute_macro(macro_id=1, initiated_by="Admin")
print(f"Macro executed: {len(result['results'])} actions")
```

**Run example:**
```bash
cd gui/examples
python3 python_client_example.py
```

---

### 2. JavaScript/Node.js Client

**Basic Usage:**

```javascript
const { HALClient, HALWebSocketClient } = require('./javascript_client_example');

async function main() {
    // Create client
    const client = new HALClient('http://localhost:8080');

    // Get panel I/O
    const ioStatus = await client.getPanelIO(1);
    console.log(`Inputs: ${ioStatus.inputs.length}`);

    // Get reader health
    const health = await client.getReaderHealth(1);
    console.log(`Health Score: ${health.health_score}/100`);

    // Unlock door
    const result = await client.unlockDoor(1, 5, 'Admin access');
    console.log(result.message);

    // WebSocket for real-time updates
    const wsClient = new HALWebSocketClient();
    await wsClient.connect();
    // Automatically handles real-time events
}

main();
```

**Run example:**
```bash
cd gui/examples
npm install axios ws  # First time only
node javascript_client_example.js
```

---

### 3. Bash/curl Examples

**Run all examples:**
```bash
cd gui/examples
./bash_examples.sh
```

**Individual commands:**

```bash
# Get panel I/O status
curl http://localhost:8080/api/v1/panels/1/io | python3 -m json.tool

# Get reader health
curl http://localhost:8080/api/v1/readers/1/health | python3 -m json.tool

# Unlock door (5 seconds)
curl -X POST "http://localhost:8080/api/v1/doors/1/unlock?duration_seconds=5"

# Pulse output (2 seconds)
curl -X POST "http://localhost:8080/api/v1/outputs/1/pulse?duration_ms=2000"

# Emergency lockdown
curl -X POST http://localhost:8080/api/v1/control/lockdown \
  -H "Content-Type: application/json" \
  -d '{"reason": "Emergency", "initiated_by": "Admin"}'

# Execute macro
curl -X POST http://localhost:8080/api/v1/macros/1/execute \
  -H "Content-Type: application/json" \
  -d '{"initiated_by": "Admin"}'
```

---

### 4. Monitoring Dashboard (Production-Ready)

Real-time monitoring dashboard that continuously monitors:
- Reader health and status
- Panel health and power
- I/O states and faults
- Active overrides
- System alerts

**Run dashboard:**
```bash
cd gui/examples
python3 monitoring_dashboard.py
```

**Options:**
```bash
# Custom API URL
python3 monitoring_dashboard.py --url http://192.168.1.100:8080

# Custom refresh interval (10 seconds)
python3 monitoring_dashboard.py --interval 10
```

**Dashboard Features:**
- 📡 Real-time reader monitoring
- 🖥️ Panel status and health
- 🔌 I/O status tracking
- ⚙️ Override detection
- 🚨 Automated alerting
- Color-coded health indicators
- Auto-refresh with configurable interval

**Alert Levels:**
- 🔴 **CRITICAL**: MAC failures, tamper alerts, power failures
- 🟡 **WARNING**: Low health scores, slow response times, I/O faults
- 🔵 **INFO**: Active overrides, status changes

---

## 🎯 Use Cases

### Use Case 1: Automated Access Control

```python
from python_client_example import HALClient
import schedule
import time

client = HALClient()

# Unlock main entrance every weekday at 8 AM
def morning_unlock():
    client.execute_macro(macro_id=4, initiated_by="Scheduler")  # Morning Unlock
    print("Main entrance unlocked for business hours")

# Lock everything at 6 PM
def evening_lockdown():
    client.execute_macro(macro_id=3, initiated_by="Scheduler")  # After Hours Mode
    print("Building secured for night")

schedule.every().monday.at("08:00").do(morning_unlock)
schedule.every().monday.at("18:00").do(evening_lockdown)
# ... repeat for other weekdays

while True:
    schedule.run_pending()
    time.sleep(60)
```

---

### Use Case 2: Security Monitoring Integration

```python
from python_client_example import HALClient

client = HALClient()

def check_security_status():
    """Monitor for security issues"""
    alerts = []

    # Check all readers
    readers = client.get_all_readers_health()

    for reader in readers['readers']:
        # Get detailed health
        health = client.get_reader_health(reader['reader_id'])

        # Check for MAC failures (security issue!)
        if health['sc_mac_failure_rate'] > 0:
            alerts.append(f"SECURITY ALERT: Reader {reader['reader_id']} MAC failures!")

        # Check for tamper
        if health['tamper_status'] != "OK":
            alerts.append(f"TAMPER ALERT: Reader {reader['reader_id']}")

        # Check for cryptogram failures
        if health['sc_cryptogram_failure_rate'] > 0:
            alerts.append(f"SECURITY: Reader {reader['reader_id']} cryptogram failures")

    return alerts

# Run every minute
import time
while True:
    alerts = check_security_status()
    for alert in alerts:
        print(f"🚨 {alert}")
        # Send to SIEM, email, SMS, etc.
    time.sleep(60)
```

---

### Use Case 3: Emergency Response Integration

```python
from python_client_example import HALClient

client = HALClient()

def handle_fire_alarm():
    """Fire alarm activated - unlock all doors"""
    result = client.emergency_unlock_all(
        reason="Fire alarm activated",
        initiated_by="Fire System"
    )
    print(f"Fire evacuation mode: {result['message']}")
    # Log to emergency systems, notify fire department, etc.

def handle_security_threat():
    """Security threat - lockdown building"""
    result = client.emergency_lockdown(
        reason="Security threat detected",
        initiated_by="Security System"
    )
    print(f"Emergency lockdown: {result['message']}")
    # Alert security team, police, etc.

def handle_all_clear():
    """Threat resolved - return to normal"""
    result = client.return_to_normal(initiated_by="Security Director")
    print(f"System status: {result['message']}")
```

---

### Use Case 4: Building Management Integration

```python
from python_client_example import HALClient

client = HALClient()

# Integrate with building management system
def sync_with_bms():
    """Synchronize HAL with Building Management System"""

    # Get all panel health
    panel_health = client.get_panel_health(panel_id=1)

    # Send to BMS
    bms_data = {
        "hal_panel_1_online": panel_health['online'],
        "hal_panel_1_health": panel_health['health_score'],
        "hal_battery_voltage": panel_health['battery_voltage'],
        "hal_main_power": panel_health['main_power']
    }

    # Send to BMS API (example)
    # requests.post("http://bms.local/api/systems/hal", json=bms_data)

    return bms_data
```

---

### Use Case 5: Custom Web Dashboard

```javascript
// Express.js server that uses HAL API
const express = require('express');
const { HALClient } = require('./javascript_client_example');

const app = express();
const halClient = new HALClient('http://localhost:8080');

// Endpoint for your custom dashboard
app.get('/api/dashboard', async (req, res) => {
    try {
        const [readers, panel1IO, panel1Health] = await Promise.all([
            halClient.getAllReadersHealth(),
            halClient.getPanelIO(1),
            halClient.getPanelHealth(1)
        ]);

        res.json({
            readers: readers.readers,
            panel: {
                io: panel1IO,
                health: panel1Health
            },
            timestamp: new Date()
        });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Door control endpoint
app.post('/api/door/:doorId/unlock', async (req, res) => {
    try {
        const result = await halClient.unlockDoor(
            parseInt(req.params.doorId),
            req.body.duration,
            req.body.reason
        );
        res.json(result);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

app.listen(3000, () => {
    console.log('Custom dashboard running on http://localhost:3000');
});
```

---

## 📊 API Endpoints Reference

### Panel I/O Monitoring
- `GET /api/v1/panels/{panel_id}/io` - Get panel I/O status
- `GET /api/v1/panels/{panel_id}/health` - Get panel health

### Reader Health
- `GET /api/v1/readers/{reader_id}/health` - Get reader health
- `GET /api/v1/readers/health/summary` - Get all readers summary

### Door Control
- `POST /api/v1/doors/{door_id}/unlock` - Unlock door
- `POST /api/v1/doors/{door_id}/lock` - Lock door
- `POST /api/v1/doors/{door_id}/lockdown` - Lockdown door
- `POST /api/v1/doors/{door_id}/release` - Release to normal

### Output Control
- `POST /api/v1/outputs/{output_id}/activate` - Activate output
- `POST /api/v1/outputs/{output_id}/deactivate` - Deactivate output
- `POST /api/v1/outputs/{output_id}/pulse` - Pulse output
- `POST /api/v1/outputs/{output_id}/toggle` - Toggle output

### Relay Control
- `POST /api/v1/relays/{relay_id}/activate` - Activate relay
- `POST /api/v1/relays/{relay_id}/deactivate` - Deactivate relay

### Mass Control
- `POST /api/v1/control/lockdown` - Emergency lockdown
- `POST /api/v1/control/unlock-all` - Emergency unlock all
- `POST /api/v1/control/normal` - Return to normal

### Macros
- `GET /api/v1/macros` - List all macros
- `POST /api/v1/macros/{macro_id}/execute` - Execute macro

### Overrides
- `GET /api/v1/overrides` - Get active overrides
- `DELETE /api/v1/overrides/{override_id}` - Clear override

### WebSocket
- `ws://localhost:8080/ws/live` - Real-time updates

---

## 🔧 Integration Tips

### Error Handling

Always wrap API calls in try/catch:

```python
try:
    result = client.unlock_door(door_id=1, duration_seconds=5)
    if result['success']:
        print("Door unlocked successfully")
    else:
        print(f"Failed: {result['message']}")
except requests.exceptions.ConnectionError:
    print("Cannot connect to HAL API server")
except requests.exceptions.Timeout:
    print("API request timed out")
except Exception as e:
    print(f"Unexpected error: {e}")
```

### Rate Limiting

For high-frequency monitoring:

```python
import time

def monitor_with_rate_limit():
    last_call = 0
    min_interval = 1.0  # Minimum 1 second between calls

    while True:
        now = time.time()
        if now - last_call >= min_interval:
            # Make API call
            health = client.get_reader_health(1)
            process_health(health)
            last_call = now
        time.sleep(0.1)
```

### Connection Pooling

For production applications:

```python
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

session = requests.Session()
retry = Retry(total=3, backoff_factor=0.3)
adapter = HTTPAdapter(max_retries=retry)
session.mount('http://', adapter)

# Use session instead of requests
response = session.get(f"{api_base}/readers/1/health")
```

---

## 📚 Additional Resources

- **Complete API Documentation**: See `docs/GUI_API_REFERENCE.md`
- **Architecture Overview**: See `docs/GUI_ARCHITECTURE.md`
- **Backend Code**: `gui/backend/hal_gui_server_v2.py`

---

## 🆘 Troubleshooting

**API server not responding:**
```bash
# Check if server is running
curl http://localhost:8080

# Start the server
cd gui/backend
python3 hal_gui_server_v2.py
```

**WebSocket connection fails:**
- Ensure no firewall blocking WebSocket connections
- Check that server supports WebSocket upgrade
- Verify WebSocket URL: `ws://` not `wss://` for local development

**Timeout errors:**
- Increase timeout in client initialization
- Check network connectivity
- Verify backend server is healthy

---

## 💡 Best Practices

1. **Always specify reasons** for control actions (audit trail)
2. **Use WebSocket** for real-time updates instead of polling
3. **Implement retry logic** for critical operations
4. **Log all API calls** in production applications
5. **Monitor health continuously** using the dashboard
6. **Handle errors gracefully** and alert operators
7. **Use macros** for complex multi-step operations
8. **Check overrides** before assuming normal operation

---

**Questions?** See the complete API reference at `http://localhost:8080/docs` when the server is running.
