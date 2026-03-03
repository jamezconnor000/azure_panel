# HAL Event Export Daemon

## Overview

The **HAL Event Export Daemon** is a standalone application that automatically exports access control events from the HAL system to external platforms like Ambient.ai, SIEM systems, or other analytics platforms.

## Features

- **Automatic Event Export** - Monitors HAL for new events and forwards them in real-time
- **Batched Delivery** - Groups events into configurable batches for efficient transmission
- **Retry Logic** - Automatically retries failed transmissions with configurable attempts
- **HTTP/HTTPS Support** - Sends events via REST API using libcurl
- **API Key Authentication** - Secure authentication using API keys
- **Statistics Tracking** - Monitors events sent, failed, and retry counts
- **Graceful Shutdown** - Handles SIGINT/SIGTERM signals cleanly

## Building

The daemon is built automatically with the HAL project:

```bash
cmake --build . --target hal_event_export_daemon
```

## Configuration

Edit `config/hal_config.json` to configure the export destination:

```json
{
    "ambient_ai": {
        "enabled": true,
        "server_url": "https://ambient.local",
        "api_endpoint": "/api/v1/events",
        "api_key": "YOUR_API_KEY_HERE",
        "timeout_seconds": 5,
        "retry_attempts": 3,
        "batch_size": 100
    }
}
```

### Configuration Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `enabled` | boolean | `false` | Enable/disable event export |
| `server_url` | string | - | Base URL of the destination server |
| `api_endpoint` | string | - | API endpoint path for events |
| `api_key` | string | - | Authentication API key |
| `timeout_seconds` | integer | `5` | HTTP request timeout |
| `retry_attempts` | integer | `3` | Number of retry attempts on failure |
| `batch_size` | integer | `100` | Number of events per batch |

## Running

### Basic Usage

```bash
./hal_event_export_daemon
```

This will:
1. Load configuration from `config/hal_config.json`
2. Connect to HAL at `localhost:8080`
3. Start monitoring and exporting events

### Command Line Options

```bash
Usage: ./hal_event_export_daemon [options]

Options:
  -c <config>   Path to config file (default: config/hal_config.json)
  -h <host>     HAL controller host (default: localhost)
  -p <port>     HAL controller port (default: 8080)
  -i <seconds>  Poll interval in seconds (default: 1)
  -d            Daemon mode (run in background)
  --help        Show this help message
```

### Examples

**Connect to remote HAL controller:**
```bash
./hal_event_export_daemon -h 192.168.1.100 -p 8080
```

**Use custom config file:**
```bash
./hal_event_export_daemon -c /etc/hal/production_config.json
```

**Run with 5-second poll interval:**
```bash
./hal_event_export_daemon -i 5
```

**Run as background daemon:**
```bash
./hal_event_export_daemon -d
```

## Event Format

Events are sent as JSON arrays to the configured API endpoint:

```json
{
  "events": [
    {
      "serial_number": 12345,
      "timestamp": 1699488000,
      "node_id": 1,
      "event_type": 0,
      "event_subtype": 0,
      "source": {
        "type": 2,
        "id": 1,
        "node_id": 1
      },
      "destination": {
        "type": 3,
        "id": 1,
        "node_id": 1
      }
    }
  ],
  "count": 1,
  "source": 1
}
```

### Event Types

| Type | Value | Description |
|------|-------|-------------|
| `EventType_AccessGrant` | 0 | Access granted event |
| `EventType_AccessDeny` | 1 | Access denied event |
| `EventType_Input` | 4 | Input alarm/tamper event |
| `EventType_Reader` | 5 | Reader status event |
| `EventType_Relay` | 6 | Relay state change |

### LPA (Logical Physical Address) Types

| Type | Value | Description |
|------|-------|-------------|
| `LPAType_Reader` | 2 | Card reader |
| `LPAType_AccessPoint` | 3 | Access point (door) |
| `LPAType_Area` | 4 | APB area |
| `LPAType_Relay` | 6 | Door strike relay |

## API Endpoint Requirements

Your destination API endpoint should:

1. **Accept POST requests** with JSON body
2. **Validate API key** in `X-API-Key` header
3. **Return HTTP 200-299** on success
4. **Handle batches** of up to `batch_size` events

### Example Express.js Endpoint

```javascript
app.post('/api/v1/events', (req, res) => {
  const apiKey = req.headers['x-api-key'];

  if (apiKey !== process.env.API_KEY) {
    return res.status(401).json({ error: 'Unauthorized' });
  }

  const { events, count } = req.body;

  // Process events
  events.forEach(event => {
    console.log(`Event ${event.serial_number}: Type ${event.event_type}`);
    // Store in database, forward to analytics, etc.
  });

  res.json({ received: count, status: 'success' });
});
```

## Statistics

The daemon prints statistics every 60 seconds:

```
═══════════════════════════════════════════════════════════════
  EXPORT STATISTICS
═══════════════════════════════════════════════════════════════
  Events Received:     1250
  Events Sent:         1250
  Events Failed:       0
  Batches Sent:        13
  Retries Attempted:   2
═══════════════════════════════════════════════════════════════
```

## Integration with Ambient.ai

To integrate with Ambient.ai:

1. **Get your API credentials** from Ambient.ai dashboard
2. **Update config/hal_config.json:**
   ```json
   {
     "ambient_ai": {
       "enabled": true,
       "server_url": "https://api.ambient.ai",
       "api_endpoint": "/v2/events/access-control",
       "api_key": "amb_live_xxxxxxxxxxxxx"
     }
   }
   ```
3. **Start the daemon:**
   ```bash
   ./hal_event_export_daemon
   ```

Events will automatically flow to Ambient.ai for video verification and analytics.

## Systemd Service (Linux)

Create `/etc/systemd/system/hal-event-export.service`:

```ini
[Unit]
Description=HAL Event Export Daemon
After=network.target

[Service]
Type=simple
User=hal
WorkingDirectory=/opt/hal
ExecStart=/opt/hal/hal_event_export_daemon -c /etc/hal/config.json
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable hal-event-export
sudo systemctl start hal-event-export
sudo systemctl status hal-event-export
```

## Troubleshooting

### Daemon Won't Start

**Problem:** `ERROR: Failed to load configuration`

**Solution:** Check that `config/hal_config.json` exists and is valid JSON

---

**Problem:** `ERROR: Failed to connect to HAL`

**Solution:**
- Verify HAL controller is running
- Check host/port are correct
- Ensure firewall allows connection

### Events Not Sending

**Problem:** `ERROR: Failed to send batch`

**Solution:**
- Verify `server_url` and `api_endpoint` are correct
- Check API key is valid
- Test endpoint manually with curl:
  ```bash
  curl -X POST https://ambient.local/api/v1/events \
    -H "X-API-Key: YOUR_KEY" \
    -H "Content-Type: application/json" \
    -d '{"events":[],"count":0}'
  ```

**Problem:** Events sending but API returns errors

**Solution:** Check API endpoint logs for detailed error messages

### High Memory Usage

**Problem:** Daemon using too much memory

**Solution:** Reduce `batch_size` in configuration to process smaller batches

## Security Considerations

1. **API Keys** - Store API keys securely, never commit to version control
2. **TLS/HTTPS** - Always use HTTPS for production deployments
3. **Network Security** - Use firewall rules to restrict daemon network access
4. **File Permissions** - Protect config files with appropriate permissions:
   ```bash
   chmod 600 config/hal_config.json
   ```

## Performance

- **Throughput:** Up to 10,000 events/second with batch_size=100
- **Latency:** Typical batch delivery within 1-5 seconds
- **Memory:** ~5-10MB baseline + (batch_size × 500 bytes)
- **CPU:** <1% on modern hardware during normal operation

## Related Documentation

- [API.md](API.md) - HAL C API Reference
- [ARCHITECTURE.md](ARCHITECTURE.md) - System Architecture
- [BUILD.md](BUILD.md) - Build Instructions

## License

Part of the HAL (Hardware Abstraction Layer) project for Azure Access Technology BLU-IC2 panels.
