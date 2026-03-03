# HAL GUI - Architecture & Design Document

**Version**: 1.0
**Date**: November 8, 2025
**Status**: Design Phase

---

## Overview

The HAL GUI provides a modern web-based interface for monitoring, managing, and troubleshooting the Hardware Abstraction Layer system with integrated OSDP Secure Channel visualization.

---

## Technology Stack

### Recommended: Modern Web Stack

**Backend:**
- **FastAPI** (Python 3.9+) - Already in use for REST API
- **WebSockets** - Real-time updates
- **SQLite** - Existing database integration
- **Server-Sent Events (SSE)** - Live log streaming

**Frontend:**
- **React 18** - Modern UI framework
- **TypeScript** - Type safety
- **Tailwind CSS** - Utility-first styling
- **Chart.js / Recharts** - Data visualization
- **React Query** - API state management

**Alternative: Lightweight Stack**
- **Flask** + **Jinja2** - Server-side rendering (simpler)
- **Bootstrap 5** - CSS framework
- **jQuery** - Basic interactivity
- **Socket.IO** - Real-time updates

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Web Browser (Client)                    │
│  ┌────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │ Dashboard  │  │ Secure       │  │  Troubleshooting │   │
│  │ View       │  │ Channel      │  │  Console         │   │
│  └────────────┘  └──────────────┘  └──────────────────┘   │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTPS / WSS
                       ↓
┌─────────────────────────────────────────────────────────────┐
│                  HAL GUI Server (FastAPI)                   │
│  ┌────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │ REST API   │  │ WebSocket    │  │  Authentication  │   │
│  │ Endpoints  │  │ Handler      │  │  & Authorization │   │
│  └────────────┘  └──────────────┘  └──────────────────┘   │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────────┐
│                    HAL Core System                          │
│  ┌────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │ Event      │  │ OSDP Secure  │  │  Diagnostic      │   │
│  │ Manager    │  │ Channel      │  │  Logger          │   │
│  └────────────┘  └──────────────┘  └──────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## GUI Features

### 1. **Dashboard View** 📊

**Real-time Metrics:**
- System health status
- Active readers count
- Secure channel status
- Events per minute
- Access grants/denies ratio

**Recent Activity:**
- Last 20 access events
- Recent errors
- Secure channel handshakes
- System alerts

**Visual Indicators:**
- 🟢 Green: All systems operational
- 🟡 Yellow: Warnings present
- 🔴 Red: Critical errors
- 🔒 Lock: Secure channel active

### 2. **Secure Channel Monitor** 🔐

**Handshake Visualization:**
```
┌─────────────────────────────────────────────────────┐
│  Reader #1 - Secure Channel Status                  │
├─────────────────────────────────────────────────────┤
│                                                      │
│  CP ──[CHLNG]──→ PD                                │
│     ←─[CCRYPT]── (CP_Random, PD_Random)            │
│  CP ──[SCRYPT]──→ PD                                │
│     ✓ ESTABLISHED                                   │
│                                                      │
│  Session Keys: ✓ Derived                            │
│  Packets Encrypted: 1,523                           │
│  Packets Decrypted: 1,489                           │
│  MAC Failures: 0                                    │
│  Last Handshake: 2 hours ago                        │
└─────────────────────────────────────────────────────┘
```

**Security Alerts:**
- Cryptogram failures (highlighted in red)
- MAC verification failures
- SCBK mismatch warnings
- Replay attack attempts

**Encryption Metrics:**
- Handshake success rate
- Average encryption time
- Packet throughput
- Error rates over time

### 3. **Reader Management** 📡

**Reader List:**
```
┌────────────────────────────────────────────────────────┐
│ ID  │ Address │ Status     │ Secure │ Last Seen      │
├────────────────────────────────────────────────────────┤
│ 1   │ 0x01    │ Online 🟢  │ ✓ AES  │ 2 seconds ago  │
│ 2   │ 0x02    │ Online 🟢  │ ✓ AES  │ 5 seconds ago  │
│ 3   │ 0x03    │ Offline 🔴 │ ✗      │ 2 hours ago    │
└────────────────────────────────────────────────────────┘
```

**Reader Details (click to expand):**
- Firmware version
- Capabilities
- LED status
- Tamper status
- Power status
- Poll interval
- Configuration

**Actions:**
- Reinitialize secure channel
- Reset reader
- Update configuration
- View logs

### 4. **Event Viewer** 📋

**Live Event Stream:**
```
┌────────────────────────────────────────────────────────┐
│ Time       │ Type        │ Reader │ Details           │
├────────────────────────────────────────────────────────┤
│ 14:32:15   │ AccessGrant │ 1      │ Card: *****4567   │
│ 14:31:58   │ AccessDeny  │ 2      │ Invalid card      │
│ 14:31:45   │ SecureInit  │ 1      │ Handshake OK      │
│ 14:31:23   │ AccessGrant │ 1      │ Card: *****8901   │
└────────────────────────────────────────────────────────┘
```

**Filters:**
- Event type (Access, System, Security)
- Reader ID
- Time range
- Severity level

**Export:**
- CSV download
- JSON export
- Print report

### 5. **Diagnostics Console** 🔧

**Log Viewer:**
- Real-time log streaming
- Syntax highlighting
- Search/filter
- Level filtering (DEBUG, INFO, WARN, ERROR)
- Category filtering (OSDP, SECURE, SYSTEM)

**Troubleshooting Wizard:**
```
┌────────────────────────────────────────────────────────┐
│  Issue: Secure Channel Handshake Failed               │
├────────────────────────────────────────────────────────┤
│  Step 1/3: Checking SCBK Configuration                │
│  [████████████████████████░░░░░] 75%                  │
│                                                         │
│  ✓ SCBK is provisioned                                │
│  ✓ Secure channel enabled                             │
│  ✗ Cryptogram verification failed                     │
│                                                         │
│  Recommendation:                                       │
│  → Verify SCBK matches between CP and PD              │
│  → Check serial communication integrity                │
│  → Review logs for corruption errors                   │
│                                                         │
│  [View Detailed Logs] [Retry Handshake] [Reset]       │
└────────────────────────────────────────────────────────┘
```

**Quick Actions:**
- Run feedback loop analysis
- Export diagnostic report
- Clear error logs
- Restart services

### 6. **Configuration Panel** ⚙️

**System Settings:**
- Event buffer size
- Poll intervals
- Timeout values
- Retry counts
- Log levels

**Secure Channel Settings:**
- Enable/disable secure channel
- SCBK management (encrypted display)
- Key rotation scheduler
- Security policy

**Reader Configuration:**
- Add/remove readers
- Update addresses
- Set capabilities
- Configure LEDs/buzzers

### 7. **Analytics & Reports** 📈

**Charts:**
1. **Access Patterns:**
   - Hourly access attempts (line chart)
   - Grant/Deny ratio (pie chart)
   - Peak usage times (bar chart)

2. **Secure Channel Health:**
   - Handshake success rate over time
   - Encryption overhead (ms)
   - MAC failure trend
   - Packet throughput

3. **System Performance:**
   - API response times
   - Database query times
   - Event processing latency
   - Memory usage

**Reports:**
- Daily summary (auto-generated)
- Security audit log
- Compliance report
- Performance report

---

## API Endpoints (Backend)

### Dashboard
```python
GET  /api/v1/dashboard/status      # System overview
GET  /api/v1/dashboard/metrics     # Real-time metrics
GET  /api/v1/dashboard/alerts      # Active alerts
```

### Readers
```python
GET    /api/v1/readers              # List all readers
GET    /api/v1/readers/{id}         # Reader details
POST   /api/v1/readers/{id}/reset   # Reset reader
POST   /api/v1/readers/{id}/secure  # Reinit secure channel
PATCH  /api/v1/readers/{id}/config  # Update configuration
```

### Secure Channel
```python
GET  /api/v1/secure/status          # All readers SC status
GET  /api/v1/secure/{reader_id}     # Specific reader SC
POST /api/v1/secure/{reader_id}/handshake  # Force handshake
GET  /api/v1/secure/{reader_id}/stats      # Encryption stats
```

### Events
```python
GET  /api/v1/events                 # List events (paginated)
GET  /api/v1/events/stream          # SSE stream
GET  /api/v1/events/export          # Export events
```

### Diagnostics
```python
GET  /api/v1/logs                   # Get logs (filtered)
GET  /api/v1/logs/stream            # SSE log stream
POST /api/v1/diagnostics/analyze    # Run feedback loop
GET  /api/v1/diagnostics/report     # Generate report
```

### WebSocket
```python
WS   /ws/live                       # Live updates
     - Events
     - Status changes
     - Alerts
     - Log entries
```

---

## UI Mockups

### Main Dashboard
```
┌──────────────────────────────────────────────────────────────────┐
│ HAL Control Panel                          🔒 Admin   [Logout]   │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │  Readers    │  │  Events     │  │  Secure     │             │
│  │     3       │  │   1,234     │  │  Channel    │             │
│  │   🟢 🟢 🔴  │  │  Today      │  │    ✓ Active │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│                                                                   │
│  Recent Events                                                    │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ 14:32 │ AccessGrant │ Reader 1 │ Card *****4567        │    │
│  │ 14:31 │ AccessDeny  │ Reader 2 │ Unknown card          │    │
│  │ 14:30 │ SecureInit  │ Reader 1 │ Handshake complete    │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                   │
│  Secure Channel Status                                           │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ Reader 1: ESTABLISHED ✓ │ Pkts: 1523E/1489D │ Errors: 0│    │
│  │ Reader 2: ESTABLISHED ✓ │ Pkts: 891E/876D   │ Errors: 0│    │
│  │ Reader 3: OFFLINE ✗     │ Last seen: 2h ago            │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                   │
│  [Dashboard] [Readers] [Events] [Diagnostics] [Settings]        │
└──────────────────────────────────────────────────────────────────┘
```

---

## Implementation Options

### Option 1: Quick Start (Flask + Bootstrap)
**Pros:**
- Fast to implement (1-2 days)
- Simple deployment
- Minimal dependencies

**Cons:**
- Less interactive
- Limited real-time features

**Best for:** Quick deployment, internal use

### Option 2: Modern SPA (React + FastAPI)
**Pros:**
- Rich interactivity
- Real-time updates
- Professional appearance
- Scalable

**Cons:**
- Longer development (1-2 weeks)
- More complex deployment

**Best for:** Production system, customer-facing

### Option 3: Desktop App (Electron)
**Pros:**
- Native app experience
- Offline capable
- Direct serial port access

**Cons:**
- Larger download size
- Platform-specific builds

**Best for:** On-site technician tool

---

## Security Considerations

**Authentication:**
- Username/password (hashed with bcrypt)
- Session tokens (JWT)
- Role-based access control (Admin, Operator, Viewer)

**Authorization:**
- Admin: Full access
- Operator: Monitor + basic actions
- Viewer: Read-only

**Communication:**
- HTTPS only (TLS 1.3)
- WebSocket over TLS
- CSRF protection
- Rate limiting

**SCBK Protection:**
- Never display full SCBK in GUI
- Show only masked version (****...****)
- Audit all SCBK access
- Require 2FA for key operations

---

## Deployment

### Development
```bash
cd gui
npm install          # Install frontend deps
pip install -r requirements.txt  # Backend deps

# Run development servers
npm run dev          # Frontend (port 3000)
python server.py     # Backend (port 8080)
```

### Production
```bash
# Build frontend
npm run build

# Serve with Nginx + Gunicorn
gunicorn -w 4 -b 0.0.0.0:8080 server:app
nginx -c nginx.conf
```

### Docker
```dockerfile
FROM node:18 AS frontend
WORKDIR /app
COPY gui/package*.json ./
RUN npm install
COPY gui/ .
RUN npm run build

FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY --from=frontend /app/dist ./static
COPY server.py .
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8080", "server:app"]
```

---

## Next Steps

1. **Choose Implementation Option**
   - Option 1 (Flask): Quick & simple
   - Option 2 (React): Full-featured
   - Option 3 (Electron): Desktop app

2. **Create Prototype**
   - Build basic dashboard
   - Integrate with existing API
   - Test real-time updates

3. **Add Features Iteratively**
   - Week 1: Dashboard + Reader view
   - Week 2: Secure channel monitor
   - Week 3: Diagnostics console
   - Week 4: Configuration & reports

---

## Estimated Timeline

**Option 1 (Flask + Bootstrap):**
- Day 1-2: Backend API integration
- Day 3-4: Basic UI templates
- Day 5: Real-time features
- Total: 5 days

**Option 2 (React + FastAPI):**
- Week 1: Backend API + WebSockets
- Week 2: Frontend components + routing
- Week 3: Charts + advanced features
- Week 4: Polish + testing
- Total: 4 weeks

**Option 3 (Electron):**
- Similar to Option 2 + packaging
- Total: 5 weeks

---

## Recommendation

**Start with Option 1 (Flask + Bootstrap) for MVP**, then migrate to Option 2 (React) if needed.

This gets you a working GUI quickly while you validate requirements with users.

---

**Ready to build? Which option would you like me to implement?**
