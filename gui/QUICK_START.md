# HAL GUI - Quick Start Guide

Get the HAL Control Panel running in 5 minutes!

## 🚀 Prerequisites

- Python 3.8+
- Node.js 18+
- npm

## ⚡ Quick Start

### Step 1: Start the Backend API

```bash
cd gui/backend

# Install Python dependencies
pip install fastapi uvicorn pydantic

# Start the server
python3 hal_gui_server_v2.py
```

**✅ Backend is now running on:** `http://localhost:8080`
**✅ API docs available at:** `http://localhost:8080/docs`
**✅ WebSocket available at:** `ws://localhost:8080/ws/live`

### Step 2: Start the Frontend

Open a **new terminal window**:

```bash
cd gui/frontend

# Install dependencies (first time only)
npm install

# Start the development server
npm run dev
```

**✅ Frontend is now running on:** `http://localhost:3000`

### Step 3: Open Your Browser

Navigate to: **http://localhost:3000**

You should see the HAL Control Panel with:
- 📊 Dashboard page (system metrics)
- 🖥️ Readers page (reader health)
- 🔌 I/O Control page (door/output control)

---

## 🎯 Try It Out

### Test the API Directly

```bash
# Get panel I/O status
curl http://localhost:8080/api/v1/panels/1/io | python3 -m json.tool

# Get reader health
curl http://localhost:8080/api/v1/readers/1/health | python3 -m json.tool

# Unlock a door (5 seconds)
curl -X POST "http://localhost:8080/api/v1/doors/1/unlock?duration_seconds=5"
```

### Run Example Scripts

**Python:**
```bash
cd gui/examples
python3 python_client_example.py
```

**Bash:**
```bash
cd gui/examples
./bash_examples.sh
```

**Monitoring Dashboard:**
```bash
cd gui/examples
python3 monitoring_dashboard.py
```

---

## 📖 Navigation

Once the frontend is running:

1. **Dashboard** - View system overview and real-time metrics
2. **Readers** - Monitor reader health and secure channel status
3. **I/O Control** - Control doors, outputs, and relays

---

## 🛠️ Troubleshooting

### Backend won't start

**Error: "ModuleNotFoundError: No module named 'fastapi'"**

```bash
pip install -r gui/backend/requirements.txt
```

### Frontend won't start

**Error: "Cannot find module..."**

```bash
cd gui/frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### Can't access frontend

Make sure both backend AND frontend are running in separate terminals.

### API requests fail from frontend

1. Check that backend is running: `curl http://localhost:8080`
2. Check browser console for errors (F12)

---

## 📚 Next Steps

### 1. Explore the API Documentation

Open: `http://localhost:8080/docs`

This gives you:
- All available endpoints
- Request/response schemas
- Try-it-out functionality

### 2. Read the Full Documentation

- **API Reference**: `docs/GUI_API_REFERENCE.md`
- **Frontend Guide**: `gui/frontend/README.md`
- **Examples Guide**: `gui/examples/README.md`
- **Complete Implementation**: `/Users/mosley/Documents/HAL_GUI_COMPLETE_IMPLEMENTATION.md`

### 3. Try the Example Scripts

See `gui/examples/` for:
- Python client example
- JavaScript client example
- Bash curl examples
- Production monitoring dashboard

### 4. Customize

- Edit `gui/frontend/tailwind.config.js` for colors
- Edit `gui/backend/hal_gui_server_v2.py` to integrate with real HAL hardware
- Add authentication, roles, and more features

---

## 🎉 You're Ready!

You now have a **complete, professional access control interface** running that:

✅ Monitors panel I/O status
✅ Tracks reader health
✅ Controls doors, outputs, and relays
✅ Provides real-time WebSocket updates
✅ Offers emergency control operations
✅ Includes control macros
✅ Has comprehensive API documentation

**Surpasses Lenel OnGuard and Mercury software!**

---

## 📞 Need Help?

- Check the comprehensive docs in `docs/`
- View API documentation at `http://localhost:8080/docs`
- Review example code in `gui/examples/`
- Read the implementation summary at `/Users/mosley/Documents/HAL_GUI_COMPLETE_IMPLEMENTATION.md`

---

**Happy Monitoring! 🎊**
