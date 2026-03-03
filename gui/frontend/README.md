# HAL Control Panel - React Frontend

Modern, professional web interface for the HAL Access Control System.

## ✨ Features

- 📊 **Real-time Dashboard** - Live system metrics and health monitoring
- 🖥️ **Reader Monitoring** - Comprehensive OSDP reader health and secure channel status
- 🔌 **I/O Control** - Full control over doors, outputs, and relays
- 🚨 **Emergency Controls** - Emergency lockdown, evacuation, and mass control operations
- 🎯 **Control Macros** - Pre-programmed multi-step operations
- 🔴 **WebSocket Updates** - Real-time event notifications
- 🎨 **Modern UI** - Beautiful, responsive design with Tailwind CSS

## 🚀 Quick Start

### Prerequisites

- Node.js 18+ and npm
- HAL backend API running on `http://localhost:8080`

### Installation

```bash
cd gui/frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will start on **http://localhost:3000**

### Build for Production

```bash
# Create optimized production build
npm run build

# Preview production build
npm run preview
```

## 📁 Project Structure

```
src/
├── api/
│   └── client.ts          # API client with all backend endpoints
├── components/
│   └── Layout.tsx         # Main application layout with navigation
├── pages/
│   ├── Dashboard.tsx      # System overview and real-time metrics
│   ├── Readers.tsx        # Reader health monitoring
│   └── IOControl.tsx      # I/O control interface
├── types/
│   └── index.ts           # TypeScript type definitions
├── App.tsx                # Main application component
├── App.css                # Global styles and Tailwind
└── main.tsx               # Application entry point
```

## 🎯 Pages

### Dashboard (`/dashboard`)

**Real-time System Overview:**
- Total readers and health status
- Issues detected
- Panel status and uptime
- System health score
- Reader health cards with individual metrics
- Panel health details (power, I/O, network)
- Live event stream from WebSocket

**Features:**
- Auto-refresh every 5 seconds
- Color-coded health indicators
- Real-time WebSocket event feed
- Critical alerts highlighted

### Readers (`/readers`)

**Comprehensive Reader Monitoring:**
- Communication health (uptime, response time, failed polls)
- Secure channel health (handshake success, MAC failures, cryptogram status)
- Hardware health (tamper status, power, temperature)
- Card reader health (read success rate, performance)
- Warnings and recommendations
- Firmware status

**Features:**
- Detailed metrics for each reader
- Health score visualization
- Automatic status updates
- Security alerts for MAC failures

### I/O Control (`/io-control`)

**Full I/O Control Interface:**
- **Doors**: Unlock (momentary/indefinite), lock, lockdown
- **Outputs**: Toggle, pulse, activate/deactivate
- **Relays**: Activate with duration
- **Control Macros**: Pre-programmed operations
- **Emergency Controls**: Lockdown, unlock all, return to normal

**Features:**
- One-click control buttons
- Real-time status indicators
- Confirmation for emergency operations
- Success/error feedback

## 🔧 Configuration

### API Base URL

The frontend is configured to proxy API requests to `http://localhost:8080` by default.

To change this, edit `vite.config.ts`:

```typescript
export default defineConfig({
  server: {
    proxy: {
      '/api': {
        target: 'http://YOUR_API_SERVER:8080',
        changeOrigin: true,
      },
    },
  },
})
```

### WebSocket URL

The WebSocket connection is configured in `src/api/client.ts`:

```typescript
connectWebSocket(url: string = 'ws://localhost:8080/ws/live')
```

## 🎨 Customization

### Colors

Edit `tailwind.config.js` to customize the color scheme:

```javascript
theme: {
  extend: {
    colors: {
      primary: {
        // Your brand colors
      },
      health: {
        excellent: '#10b981',
        good: '#84cc16',
        fair: '#eab308',
        poor: '#f97316',
        critical: '#ef4444',
      }
    }
  }
}
```

### Refresh Intervals

Edit query refresh intervals in each page:

```typescript
useQuery({
  queryKey: ['readers', 'health'],
  queryFn: () => apiClient.getAllReadersHealth(),
  refetchInterval: 5000, // Change this (milliseconds)
})
```

## 📊 Data Flow

```
1. User opens browser → React App loads
2. App connects to WebSocket (real-time updates)
3. Pages use React Query to fetch data from API
4. Data refreshes automatically (configurable interval)
5. WebSocket pushes live events to Dashboard
6. User actions (buttons) trigger API mutations
7. Mutations automatically refresh affected data
```

## 🔐 API Integration

The frontend uses a TypeScript API client (`src/api/client.ts`) that provides:

### Query Methods (GET)
- `getPanelIO(panelId)` - Panel I/O status
- `getPanelHealth(panelId)` - Panel health metrics
- `getReaderHealth(readerId)` - Reader health
- `getAllReadersHealth()` - All readers summary
- `listMacros()` - Available macros
- `getActiveOverrides()` - Active I/O overrides

### Mutation Methods (POST/DELETE)
- `unlockDoor(doorId, duration?, reason?)` - Unlock door
- `lockDoor(doorId, reason?)` - Lock door
- `lockdownDoor(doorId, reason)` - Door lockdown
- `activateOutput(outputId, duration?)` - Activate output
- `pulseOutput(outputId, duration)` - Pulse output
- `activateRelay(relayId, duration?)` - Activate relay
- `emergencyLockdown(reason, initiatedBy)` - Emergency lockdown
- `emergencyUnlockAll(reason, initiatedBy)` - Emergency unlock
- `returnToNormal(initiatedBy)` - Return to normal
- `executeMacro(macroId, initiatedBy)` - Execute macro

### WebSocket
- `connectWebSocket(url?)` - Connect to WebSocket
- `onWebSocketMessage(type, callback)` - Listen for events
- `disconnectWebSocket()` - Disconnect WebSocket

## 🧪 Development

### Code Style

The project uses:
- TypeScript for type safety
- ESLint for code linting
- Prettier for code formatting (recommended)

### Adding a New Page

1. Create page component in `src/pages/NewPage.tsx`
2. Add route in `src/App.tsx`:
   ```typescript
   <Route path="new-page" element={<NewPage />} />
   ```
3. Add navigation link in `src/components/Layout.tsx`

### Using the API Client

```typescript
import { useQuery, useMutation } from '@tanstack/react-query';
import { apiClient } from '../api/client';

// Fetch data
const { data, isLoading } = useQuery({
  queryKey: ['my-data'],
  queryFn: () => apiClient.someMethod(),
});

// Mutate data
const mutation = useMutation({
  mutationFn: (params) => apiClient.someAction(params),
  onSuccess: () => {
    // Handle success
  },
});
```

## 🚨 Troubleshooting

### Frontend won't start

```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### API requests failing

1. Check that backend is running: `curl http://localhost:8080`
2. Check proxy configuration in `vite.config.ts`
3. Check browser console for CORS errors

### WebSocket not connecting

1. Verify WebSocket URL in `src/api/client.ts`
2. Check that backend supports WebSocket upgrade
3. Check browser console for connection errors

### TypeScript errors

```bash
# Check for type errors
npm run lint
```

## 📈 Performance

The frontend is optimized for performance:

- **Code Splitting**: Pages loaded on demand
- **React Query Caching**: Minimizes API calls
- **Optimistic Updates**: Instant UI feedback
- **WebSocket**: Real-time updates without polling
- **Auto-refresh**: Configurable intervals to balance freshness and load

## 🌐 Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+

## 📚 Technologies Used

| Technology | Purpose |
|------------|---------|
| React 18 | UI framework |
| TypeScript | Type safety |
| Vite | Build tool and dev server |
| React Router | Client-side routing |
| React Query | Data fetching and caching |
| Axios | HTTP client |
| Tailwind CSS | Styling |
| Lucide React | Icons |

## 🎯 Next Steps

### Enhancements to Consider

1. **Authentication** - Add JWT authentication
2. **User Roles** - Role-based access control
3. **Event History** - Searchable event log
4. **Reports** - Generate PDF/CSV reports
5. **Notifications** - Browser notifications for alerts
6. **Dark/Light Mode** - Theme toggle
7. **Mobile Optimization** - Touch-friendly controls
8. **Charting** - Historical data visualization
9. **Settings Page** - System configuration UI
10. **Audit Log** - Track all user actions

### Recommended Libraries

```bash
# Authentication
npm install react-hook-form zod

# Charts
npm install recharts

# Notifications
npm install react-hot-toast

# Date formatting
npm install date-fns

# PDF generation
npm install jspdf
```

## 📖 Documentation

- **API Reference**: See `docs/GUI_API_REFERENCE.md`
- **Architecture**: See `docs/GUI_ARCHITECTURE.md`
- **Backend Code**: `gui/backend/hal_gui_server_v2.py`

## 💡 Best Practices

1. **Always provide feedback** for user actions
2. **Confirm destructive operations** (lockdown, unlock all)
3. **Show loading states** during async operations
4. **Handle errors gracefully** with user-friendly messages
5. **Keep UI responsive** with optimistic updates
6. **Use TypeScript** for type safety
7. **Test on multiple browsers**
8. **Monitor WebSocket connection** status

---

**Built with ❤️ for HAL Access Control System**

For questions or issues, see the main project documentation.
