# Aether_Access Build 2.0 - Installation & User Guide

**Version**: 2.0.0
**Release Date**: November 8, 2025

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [What's New in 2.0](#whats-new-in-20)
3. [System Requirements](#system-requirements)
4. [Installation](#installation)
5. [Quick Start](#quick-start)
6. [Configuration](#configuration)
7. [Using the GUI](#using-the-gui)
8. [API Integration](#api-integration)
9. [Troubleshooting](#troubleshooting)
10. [Upgrade from 1.x](#upgrade-from-1x)

---

## 🎯 Overview

Aether_Access Build 2.0 is a **complete, enterprise-grade access control system** that includes:

- **C Core**: High-performance OSDP secure channel implementation
- **REST API**: Modern FastAPI backend with automatic documentation
- **Web GUI**: Professional React frontend with real-time updates
- **Integration Examples**: Python, JavaScript, and Bash clients
- **Monitoring Tools**: Production-ready monitoring dashboard

### Key Features

✅ OSDP Secure Channel with AES-128 encryption
✅ Azure BLU-IC2 panel I/O monitoring
✅ Comprehensive reader health monitoring
✅ Full I/O control (doors, outputs, relays)
✅ Real-time WebSocket updates
✅ Control macros and emergency operations
✅ Event export system
✅ Diagnostic logging with feedback loop
✅ REST API with Swagger documentation
✅ Modern web interface

### Comparison

| Feature | Aether_Access 2.0 | Lenel OnGuard | Mercury Partners |
|---------|---------|---------------|------------------|
| Modern REST API | ✅ | ⚠️ Limited | ⚠️ Varies |
| WebSocket Real-time | ✅ | ❌ | ❌ |
| Secure Channel Deep Visibility | ✅ | ❌ | ⚠️ Basic |
| I/O Control via API | ✅ | ⚠️ GUI only | ⚠️ Varies |
| Open Architecture | ✅ | ❌ | ⚠️ Varies |
| Cost | ✅ Free | ❌ $$$$ | ⚠️ Varies |

---

## 🆕 What's New in 2.0

### Major Features

1. **Complete Web GUI**
   - Modern React interface with TypeScript
   - Real-time dashboard with WebSocket updates
   - Comprehensive reader health monitoring
   - Full I/O control interface
   - Emergency operations panel

2. **Enhanced API**
   - REST API with automatic Swagger documentation
   - WebSocket support for real-time events
   - Panel I/O monitoring endpoints
   - Reader health APIs with deep metrics
   - Control macros and mass operations

3. **Integration Examples**
   - Complete Python client library
   - JavaScript/Node.js client with WebSocket
   - Bash/curl examples for all endpoints
   - Production monitoring dashboard

4. **Improved Documentation**
   - Complete API reference (600+ lines)
   - Architecture documentation (800+ lines)
   - Quick start guides
   - Integration examples

### Enhancements from 1.x

- **Performance**: Async Python backend, optimized React frontend
- **Security**: Enhanced secure channel logging and diagnostics
- **Usability**: Intuitive web interface, no client software required
- **Monitoring**: Real-time health metrics for all components
- **Extensibility**: RESTful API for easy integration

---

## 💻 System Requirements

### Hardware

**Minimum:**
- CPU: 2 cores, 2.0 GHz
- RAM: 2 GB
- Storage: 500 MB available space

**Recommended:**
- CPU: 4 cores, 2.5 GHz or higher
- RAM: 4 GB or more
- Storage: 1 GB available space
- Network: 100 Mbps or higher

### Software

**Operating System:**
- Linux (Ubuntu 20.04+, CentOS 8+, Debian 11+)
- macOS 11+ (Big Sur or later)
- Windows 10/11 (with WSL2)

**Required Dependencies:**
- Python 3.8 or higher
- Node.js 18 or higher (with npm)
- SQLite 3
- OpenSSL 1.1 or higher
- libcurl 7.x or higher
- CMake 3.10 or higher
- GCC 7+ or Clang 10+

**Optional:**
- nginx or Apache (for production frontend hosting)
- Docker (for containerized deployment)
- systemd (for service management)

---

## 📦 Installation

### Option 1: Using the Deployment Script (Recommended)

The deployment script automatically builds and packages everything:

```bash
# Clone or extract Aether_Access Build 2.0
cd aetheraccess_project

# Run deployment script
./deploy_hal_2.0.sh
```

This will:
1. Check prerequisites
2. Build C core
3. Install Python dependencies
4. Install Node.js dependencies
5. Build React frontend for production
6. Create deployment package
7. Generate startup scripts
8. Create archive for distribution

The deployment package will be in `aetheraccess_build_2.0_deployment/`

### Option 2: Manual Installation

#### Step 1: Install System Dependencies

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install -y build-essential cmake git \
    libsqlite3-dev libssl-dev libcurl4-openssl-dev \
    python3 python3-pip nodejs npm
```

**macOS:**
```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install cmake sqlite openssl curl python3 node
```

**CentOS/RHEL:**
```bash
sudo yum groupinstall "Development Tools"
sudo yum install -y cmake sqlite-devel openssl-devel libcurl-devel \
    python3 python3-pip nodejs npm
```

#### Step 2: Build C Core

```bash
cd aetheraccess_project

# Create build directory
mkdir build
cd build

# Configure with CMake
cmake ..

# Build
make -j$(nproc)

cd ..
```

#### Step 3: Install Backend Dependencies

```bash
cd gui/backend
pip3 install -r requirements.txt
cd ../..
```

#### Step 4: Install and Build Frontend

```bash
cd gui/frontend

# Install dependencies
npm install

# Build for production
npm run build

cd ../..
```

### Option 3: Docker Deployment

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  backend:
    build: ./gui/backend
    ports:
      - "8080:8080"
    volumes:
      - ./data:/app/data
    environment:
      - DATABASE_PATH=/app/data/hal.db

  frontend:
    build: ./gui/frontend
    ports:
      - "80:80"
    depends_on:
      - backend
```

Then run:
```bash
docker-compose up -d
```

---

## 🚀 Quick Start

### Starting the System

#### Using Deployment Package

```bash
cd aetheraccess_build_2.0_deployment

# Start complete system (backend + logs)
./start_hal_system.sh
```

#### Manual Start

**Terminal 1 - Backend:**
```bash
cd gui/backend
python3 hal_gui_server_v2.py
```

**Terminal 2 - Frontend (Development):**
```bash
cd gui/frontend
npm run dev
```

**Terminal 3 - Frontend (Production):**
```bash
cd gui/frontend/dist
python3 -m http.server 3000
```

### Accessing the System

Once running:

- **Web Interface**: http://localhost:3000
- **Backend API**: http://localhost:8080
- **API Documentation**: http://localhost:8080/docs
- **WebSocket**: ws://localhost:8080/ws/live

### First Login

The default installation has no authentication. In production, you should:

1. Add authentication (see Configuration section)
2. Configure HTTPS/TLS
3. Set up firewall rules
4. Configure user roles

---

## ⚙️ Configuration

### Backend Configuration

Edit `gui/backend/hal_gui_server_v2.py`:

```python
# Server configuration
HOST = "0.0.0.0"  # Listen on all interfaces
PORT = 8080       # API port

# CORS configuration (adjust for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://your-domain.com"],  # Specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Frontend Configuration

Edit `gui/frontend/vite.config.ts`:

```typescript
export default defineConfig({
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://YOUR_BACKEND_SERVER:8080',
        changeOrigin: true,
      },
    },
  },
})
```

### Database Configuration

The system uses SQLite by default. Location: `/path/to/hal.db`

For production, consider migrating to PostgreSQL:

1. Update `hal_core` to use PostgreSQL
2. Configure connection string
3. Run migrations

### Panel Configuration

Configure Azure panels in `panel_config.json`:

```json
{
  "panels": [
    {
      "panel_id": 1,
      "panel_name": "Main Building",
      "ip_address": "192.168.1.100",
      "readers": [
        {
          "reader_id": 1,
          "name": "Main Entrance",
          "address": 0
        }
      ]
    }
  ]
}
```

---

## 🖥️ Using the GUI

### Dashboard Page

**Access**: http://localhost:3000/dashboard

**Features:**
- System overview with 4 metric cards
- Reader health summary
- Panel status and health
- Real-time event feed

**Actions:**
- View system health at a glance
- Monitor real-time events
- Check for issues across all components

### Readers Page

**Access**: http://localhost:3000/readers

**Features:**
- Detailed health metrics for each reader
- Communication health (uptime, latency, failures)
- Secure channel health (handshakes, MAC failures)
- Hardware health (power, temperature, tamper)
- Card reader performance

**Actions:**
- Monitor reader health
- Identify communication issues
- Detect security alerts (MAC failures)
- Review firmware status

### I/O Control Page

**Access**: http://localhost:3000/io-control

**Features:**
- Door control (unlock, lock, lockdown)
- Output control (activate, deactivate, pulse)
- Relay control
- Control macros
- Emergency operations

**Actions:**
- Unlock doors (momentary or indefinite)
- Activate outputs and relays
- Execute control macros
- Emergency lockdown
- Emergency unlock all
- Return to normal operation

---

## 🔌 API Integration

### Using Python

```python
from gui.examples.python_client_example import HALClient

# Create client
client = HALClient(base_url="http://localhost:8080")

# Get reader health
health = client.get_reader_health(reader_id=1)
print(f"Health Score: {health['health_score']}/100")

# Unlock door
result = client.unlock_door(door_id=1, duration_seconds=5)
print(result['message'])

# Emergency lockdown
result = client.emergency_lockdown(
    reason="Active threat",
    initiated_by="Security System"
)
```

### Using JavaScript

```javascript
const { HALClient } = require('./gui/examples/javascript_client_example');

const client = new HALClient('http://localhost:8080');

// Get panel I/O
const ioStatus = await client.getPanelIO(1);
console.log(`Total events today: ${ioStatus.total_events_today}`);

// Unlock door
const result = await client.unlockDoor(1, 5, 'Admin access');
console.log(result.message);
```

### Using curl

```bash
# Get reader health
curl http://localhost:8080/api/v1/readers/1/health | python3 -m json.tool

# Unlock door
curl -X POST "http://localhost:8080/api/v1/doors/1/unlock?duration_seconds=5"

# Emergency lockdown
curl -X POST http://localhost:8080/api/v1/control/lockdown \
  -H "Content-Type: application/json" \
  -d '{"reason": "Emergency", "initiated_by": "Admin"}'
```

---

## 🔧 Troubleshooting

### Backend Won't Start

**Error: "ModuleNotFoundError: No module named 'fastapi'"**

Solution:
```bash
cd gui/backend
pip3 install -r requirements.txt
```

**Error: "Address already in use (port 8080)"**

Solution:
```bash
# Find and kill process using port 8080
lsof -ti:8080 | xargs kill -9
```

### Frontend Won't Start

**Error: "Cannot find module..."**

Solution:
```bash
cd gui/frontend
rm -rf node_modules package-lock.json
npm install
```

**Error: "Failed to compile"**

Solution:
```bash
# Check Node.js version
node --version  # Should be 18+

# Update npm
npm install -g npm@latest
```

### API Requests Failing

**Symptoms**: Frontend shows errors, API calls fail

Solutions:
1. Check that backend is running: `curl http://localhost:8080`
2. Check browser console (F12) for errors
3. Verify CORS settings in backend
4. Check firewall rules

### WebSocket Not Connecting

**Symptoms**: No real-time updates in dashboard

Solutions:
1. Verify WebSocket URL in frontend
2. Check that backend WebSocket endpoint is accessible
3. Check for proxy/firewall blocking WebSocket upgrade
4. Review browser console for connection errors

### Database Errors

**Error: "database is locked"**

Solutions:
1. Close other connections to database
2. Increase timeout in database configuration
3. Consider migrating to PostgreSQL for production

---

## 📈 Upgrade from 1.x

### Backup Current Installation

```bash
# Backup database
cp /path/to/hal.db /path/to/hal.db.backup

# Backup configurations
tar -czf hal_1.x_backup.tar.gz /path/to/hal_installation/
```

### Migration Steps

1. **Install Aether_Access 2.0** following installation instructions above

2. **Migrate Database**
   ```bash
   # Copy existing database
   cp /path/to/old/hal.db /path/to/new/hal.db

   # Run migration script (if needed)
   python3 scripts/migrate_1x_to_2x.py
   ```

3. **Update Configurations**
   - Review and update panel configurations
   - Update reader addresses if changed
   - Configure new GUI settings

4. **Test System**
   - Start backend and frontend
   - Verify all readers are online
   - Test door control operations
   - Check event logging

5. **Cutover**
   - Stop HAL 1.x services
   - Start Aether_Access 2.0 services
   - Monitor for issues

### Breaking Changes from 1.x

- API endpoints now use `/api/v1/` prefix
- WebSocket protocol updated
- Configuration file format changed
- Some API responses include additional fields

---

## 📊 Performance Tuning

### Backend Optimization

For high-traffic installations:

```bash
# Use gunicorn with multiple workers
gunicorn -w 4 -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8080 \
  gui.backend.hal_gui_server_v2:app
```

### Database Optimization

For PostgreSQL in production:

```python
# Connection pooling
DATABASE_URL = "postgresql://user:pass@localhost/hal"
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=0
)
```

### Frontend Optimization

Serve built frontend with nginx:

```nginx
server {
    listen 80;
    server_name hal.yourdomain.com;

    # Frontend
    root /path/to/aetheraccess_build_2.0_deployment/gui/frontend/dist;
    index index.html;

    # API proxy
    location /api/ {
        proxy_pass http://localhost:8080/api/;
        proxy_set_header Host $host;
    }

    # WebSocket proxy
    location /ws/ {
        proxy_pass http://localhost:8080/ws/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Caching
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

---

## 🔒 Security Considerations

### Production Checklist

- [ ] Enable HTTPS/TLS
- [ ] Add authentication (JWT recommended)
- [ ] Implement role-based access control
- [ ] Configure rate limiting
- [ ] Update CORS settings
- [ ] Enable audit logging
- [ ] Set up firewall rules
- [ ] Regular security updates
- [ ] Database backups
- [ ] Monitor for security alerts

### Recommended Security Settings

```python
# Backend: Add JWT authentication
from fastapi_jwt_auth import AuthJWT

# Frontend: Store tokens securely
localStorage.setItem('access_token', token);

# Use HTTPS in production
if (window.location.protocol !== 'https:') {
    window.location.protocol = 'https:';
}
```

---

## 📞 Support & Resources

### Documentation

- **API Reference**: `docs/GUI_API_REFERENCE.md`
- **Architecture**: `docs/GUI_ARCHITECTURE.md`
- **Frontend Guide**: `gui/frontend/README.md`
- **Examples**: `gui/examples/README.md`

### Example Scripts

- Python: `gui/examples/python_client_example.py`
- JavaScript: `gui/examples/javascript_client_example.js`
- Bash: `gui/examples/bash_examples.sh`
- Monitoring: `gui/examples/monitoring_dashboard.py`

### Online Resources

- API Documentation: http://localhost:8080/docs (when running)
- Quick Start: `QUICK_START.md`
- Deployment Guide: `DEPLOY_README.md`

---

## 🎉 Conclusion

Aether_Access Build 2.0 is a **complete, production-ready access control system** that surpasses enterprise solutions like Lenel OnGuard and Mercury partners in features, usability, and modern architecture.

**Key Advantages:**
- Modern REST API with automatic documentation
- Real-time WebSocket updates
- Professional web interface
- Comprehensive health monitoring
- Deep secure channel visibility
- Free and open source

**Get Started:**
```bash
cd aetheraccess_build_2.0_deployment
./start_hal_system.sh
```

Visit http://localhost:3000 and start managing your access control system!

---

**Aether_Access Build 2.0** - Enterprise Access Control, Modernized

**Version**: 2.0.0
**Release Date**: November 8, 2025
