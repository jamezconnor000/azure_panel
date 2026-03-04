# Aether Access - Azure Panel Installation Guide

## Overview

This guide provides instructions for deploying Aether Access to an Azure BLU-IC2 Controller panel. The installation creates a complete access control system with REST API, real-time WebSocket updates, and card database management.

## System Requirements

### Hardware
- Azure BLU-IC2 Controller (ARM64)
- Minimum 512MB RAM
- Minimum 500MB free disk space
- Network connectivity

### Software
- Linux (Debian/Ubuntu, Alpine, or RHEL-based)
- Python 3.9 or higher
- SQLite 3.x
- systemd (for service management)

## Quick Start

### 1. Transfer Package to Panel

Transfer the deployment package to your Azure Panel:

```bash
# From your development machine
scp -r aether-access-deploy.tar.gz root@panel-ip:/tmp/

# On the panel
cd /tmp
tar -xzf aether-access-deploy.tar.gz
cd aether-access-deploy
```

### 2. Run Installation

```bash
sudo ./scripts/install.sh
```

For automated installation without prompts:

```bash
sudo ./scripts/install.sh --unattended
```

### 3. Verify Installation

```bash
# Check service status
sudo systemctl status aether-access

# Test API
curl http://localhost:8080/health
```

## Installation Options

### Command-Line Arguments

| Option | Description |
|--------|-------------|
| `--unattended` | Run without prompts (use defaults) |
| `--dev` | Install in development mode |
| `--no-service` | Don't install systemd services |
| `--data-dir DIR` | Custom data directory |
| `--port PORT` | API server port (default: 8080) |

### Examples

```bash
# Production installation with custom port
sudo ./scripts/install.sh --port 443

# Development installation (no services)
sudo ./scripts/install.sh --dev --no-service

# Custom data directory
sudo ./scripts/install.sh --data-dir /mnt/data/aether
```

## Directory Structure

After installation, files are organized as follows:

```
/opt/aether-access/          # Application files
├── api/                     # API server modules
│   ├── unified_api_server.py
│   ├── api_v2_1.py
│   ├── api_v2_2.py
│   ├── auth.py
│   └── database.py
├── python/                  # HAL Python bindings
│   └── hal_bindings.py
├── venv/                    # Python virtual environment
├── lib/                     # HAL C libraries (if available)
└── requirements.txt

/etc/aether/                 # Configuration
├── aether.conf              # Main configuration
└── aether.env               # Environment variables

/var/lib/aether/            # Data
├── hal_database.db         # Main database
└── backups/                # Database backups

/var/log/aether/            # Logs
├── aether.log              # Application log
└── aether-error.log        # Error log
```

## Configuration

### Main Configuration (/etc/aether/aether.conf)

Key settings to review:

```ini
[security]
# IMPORTANT: Change this for production!
secret_key = your-unique-secret-key

# Restrict CORS origins for production
allowed_origins = https://your-frontend-domain.com

[server]
port = 8080
workers = 2

[database]
path = /var/lib/aether/hal_database.db
```

### Environment Variables (/etc/aether/aether.env)

```bash
API_PORT=8080
HAL_DATABASE_PATH=/var/lib/aether/hal_database.db
HAL_LOG_LEVEL=INFO
```

## Service Management

### Using systemctl

```bash
# Start the service
sudo systemctl start aether-access

# Stop the service
sudo systemctl stop aether-access

# Restart the service
sudo systemctl restart aether-access

# View service status
sudo systemctl status aether-access

# Enable auto-start on boot
sudo systemctl enable aether-access

# Disable auto-start
sudo systemctl disable aether-access
```

### Viewing Logs

```bash
# Real-time logs
sudo journalctl -u aether-access -f

# Last 100 lines
sudo journalctl -u aether-access -n 100

# Application log file
tail -f /var/log/aether/aether.log
```

## API Endpoints

### Quick Reference

| Endpoint | Description |
|----------|-------------|
| `GET /` | API root (HTML info page) |
| `GET /health` | Health check |
| `GET /docs` | Swagger UI documentation |
| `GET /redoc` | ReDoc documentation |

### HAL Core (`/hal/*`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/hal/health` | GET | HAL system health |
| `/hal/stats` | GET | HAL statistics |
| `/hal/cards` | GET/POST | Card management |
| `/hal/cards/{number}` | GET/PUT/DELETE | Single card |
| `/hal/doors` | GET/POST | Door management |
| `/hal/access-levels` | GET/POST | Access level management |
| `/hal/events` | GET | Event buffer |
| `/hal/access/check` | POST | Check access decision |
| `/hal/simulate/card-read` | POST | Simulate card read |

### Frontend API (`/api/v1/*`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/dashboard` | GET | Dashboard data |
| `/api/v1/panels/{id}/io` | GET | Panel I/O status |
| `/api/v1/panels/{id}/health` | GET | Panel health |
| `/api/v1/readers/health/summary` | GET | Reader health summary |
| `/api/v1/doors/{id}/unlock` | POST | Unlock door |
| `/api/v1/doors/{id}/lock` | POST | Lock door |
| `/api/v1/control/lockdown` | POST | Emergency lockdown |

### Auth API (`/api/v2.1/*`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v2.1/auth/login` | POST | User login |
| `/api/v2.1/auth/logout` | POST | User logout |
| `/api/v2.1/auth/refresh` | POST | Refresh token |
| `/api/v2.1/users` | GET/POST | User management |
| `/api/v2.1/doors` | GET/POST | Door configuration |
| `/api/v2.1/access-levels` | GET/POST | Access levels |

### WebSocket

```
ws://panel-ip:8080/ws/live
```

Subscribe to real-time events:
- Card reads
- Door events
- System alerts
- Heartbeat

## Testing the Installation

### Health Check

```bash
curl http://localhost:8080/health | jq
```

Expected response:
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "hal": {
    "status": "healthy",
    "mode": "simulation"
  },
  "api_versions": {
    "v1": true,
    "v2.1": true,
    "v2.2": true
  }
}
```

### Add a Test Card

```bash
curl -X POST http://localhost:8080/hal/cards \
  -H "Content-Type: application/json" \
  -d '{
    "card_number": "12345678",
    "permission_id": 1,
    "holder_name": "Test User"
  }'
```

### Simulate Card Read

```bash
curl -X POST "http://localhost:8080/hal/simulate/card-read?card_number=12345678&door_id=1"
```

### Test WebSocket

```bash
# Install websocat if needed: cargo install websocat
websocat ws://localhost:8080/ws/live
```

## Troubleshooting

### Service Won't Start

1. Check logs:
   ```bash
   sudo journalctl -u aether-access -n 50 --no-pager
   ```

2. Check port availability:
   ```bash
   sudo lsof -i :8080
   ```

3. Verify permissions:
   ```bash
   ls -la /var/lib/aether/
   ls -la /opt/aether-access/
   ```

### Database Errors

1. Check database file:
   ```bash
   sqlite3 /var/lib/aether/hal_database.db ".tables"
   ```

2. Reset database:
   ```bash
   sudo systemctl stop aether-access
   sudo rm /var/lib/aether/hal_database.db
   sudo systemctl start aether-access
   ```

### Permission Issues

```bash
# Fix ownership
sudo chown -R aether:aether /var/lib/aether
sudo chown -R aether:aether /var/log/aether
```

### Port Already in Use

```bash
# Find process using port
sudo lsof -i :8080

# Kill process or change port in /etc/aether/aether.env
```

## Uninstallation

To remove Aether Access:

```bash
sudo ./scripts/uninstall.sh
```

This will:
1. Stop and disable the service
2. Remove application files
3. Remove configuration
4. Optionally remove data

## Security Considerations

### Production Checklist

- [ ] Change default `secret_key` in configuration
- [ ] Restrict `allowed_origins` to your frontend domain
- [ ] Enable HTTPS (use reverse proxy like nginx)
- [ ] Configure firewall rules
- [ ] Set up log rotation
- [ ] Enable database backups
- [ ] Review user permissions
- [ ] Disable debug mode

### Firewall Rules

```bash
# Allow API port
sudo ufw allow 8080/tcp

# Or with iptables
sudo iptables -A INPUT -p tcp --dport 8080 -j ACCEPT
```

### HTTPS with nginx

```nginx
server {
    listen 443 ssl;
    server_name panel.example.com;

    ssl_certificate /etc/ssl/certs/panel.crt;
    ssl_certificate_key /etc/ssl/private/panel.key;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Ambient.ai Integration

Aether Access supports real-time event export to Ambient.ai for intelligent video monitoring integration.

### Configuring Ambient.ai Export

1. **Create configuration file:**
   ```bash
   sudo cp /etc/aether/ambient.env.template /etc/aether/ambient.env
   sudo nano /etc/aether/ambient.env
   ```

2. **Add your API key:**
   ```bash
   AMBIENT_API_KEY=your-api-key-from-ambient-ai
   ```

3. **Enable and start the export daemon:**
   ```bash
   sudo systemctl enable aether-ambient-export
   sudo systemctl start aether-ambient-export
   ```

4. **Verify the daemon is running:**
   ```bash
   sudo systemctl status aether-ambient-export
   tail -f /var/log/aether/ambient_export.log
   ```

### Ambient.ai API Endpoints

The following endpoints are available for Ambient.ai entity sync:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/hal/ambient/source-system` | GET | Get source system UUID |
| `/hal/ambient/devices` | GET | Get all devices for sync |
| `/hal/ambient/persons` | GET | Get all persons for sync |
| `/hal/ambient/access-items` | GET | Get all cards/credentials for sync |
| `/hal/ambient/alarms` | GET | Get alarm definitions |
| `/hal/ambient/export-queue` | GET | View export queue status |

### Supported Event Types

The following PACS events are exported to Ambient.ai:

| Event Type | Alarm | Description |
|------------|-------|-------------|
| Access Granted | No | Card read, access allowed |
| Access Denied | Yes | Card read, access denied |
| Door Forced Open | Yes | Door opened without valid credential |
| Door Held Open | Yes | Door left open too long |
| Invalid Badge | Yes | Unknown card presented |
| Expired Badge | Yes | Expired card presented |
| Tamper Alarm | Yes | Device tamper detected |
| Communication Failure | Yes | Reader/panel communication lost |
| Anti-Passback Violation | Yes | APB rule violated |
| Duress Alarm | Yes | Duress code entered |
| Emergency Lockdown | Yes | System locked down |

### Export Daemon Configuration

Environment variables in `/etc/aether/ambient.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `AMBIENT_API_KEY` | (required) | Your Ambient.ai API key |
| `AMBIENT_API_URL` | `https://pacs-ingestion.ambient.ai/v1/api` | API endpoint URL |
| `AMBIENT_BATCH_SIZE` | `100` | Events per batch |
| `AMBIENT_POLL_INTERVAL` | `5` | Seconds between queue checks |
| `AMBIENT_MAX_RETRIES` | `3` | Max retry attempts per event |

### Monitoring Export Status

Check export queue status:
```bash
curl http://localhost:8080/hal/ambient/export-queue | jq
```

View export daemon logs:
```bash
sudo journalctl -u aether-ambient-export -f
```

## Support

For issues and feature requests:
- Check logs: `/var/log/aether/`
- API documentation: `http://panel-ip:8080/docs`
- Health status: `http://panel-ip:8080/health`
