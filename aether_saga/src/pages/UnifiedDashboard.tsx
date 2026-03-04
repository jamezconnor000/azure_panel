/**
 * UnifiedDashboard - Situ8-style Command Center
 * Exact match to Situ8 UI design
 */

import { useState, useEffect } from 'react';
import { RefreshCw, ChevronRight, DoorOpen, UserCheck, AlertTriangle, FileText } from 'lucide-react';

// ============================================================================
// DEMO DATA
// ============================================================================

const DEMO_STATS = {
  activeDoors: 12,
  pendingApprovals: 3,
  todaysEvents: 847,
  todaysAlerts: 2,
  resolvedToday: 15,
  avgResponse: '0ms',
};

const DEMO_DOORS = [
  { id: 1, name: 'Main Entrance', status: 'online', lastEvent: '2 min ago' },
  { id: 2, name: 'Server Room', status: 'online', lastEvent: '5 min ago' },
  { id: 3, name: 'Loading Dock', status: 'offline', lastEvent: '1 hour ago' },
  { id: 4, name: 'Executive Suite', status: 'online', lastEvent: '12 min ago' },
];

const DEMO_EVENTS = [
  { id: 1, type: 'access_granted', user: 'John Smith', door: 'Main Entrance', time: '8:45 AM' },
  { id: 2, type: 'access_granted', user: 'Sarah Johnson', door: 'Server Room', time: '8:42 AM' },
  { id: 3, type: 'access_denied', user: 'Unknown Card', door: 'Loading Dock', time: '8:30 AM' },
  { id: 4, type: 'access_granted', user: 'Mike Rodriguez', door: 'Executive Suite', time: '8:15 AM' },
];

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export function UnifiedDashboard() {
  const [currentTime, setCurrentTime] = useState(new Date());
  const [lastUpdated, setLastUpdated] = useState('Just now');

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const timeString = currentTime.toLocaleTimeString('en-US', {
    hour: 'numeric',
    minute: '2-digit',
    second: '2-digit',
    hour12: true
  });

  return (
    <div className="space-y-6">
      {/* Page Header - Situ8 exact style */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span
              className="w-2 h-2 rounded-full animate-pulse"
              style={{ background: '#22c55e' }}
            />
            <h1 className="text-xl font-semibold" style={{ color: '#e6edf3' }}>
              Command Center
            </h1>
          </div>
          <p className="text-sm" style={{ color: '#7d8590' }}>
            Real-time operations overview • {timeString} • Last updated: {lastUpdated}
          </p>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-sm font-medium" style={{ color: '#22c55e' }}>
            All Systems Operational
          </span>
          <button
            onClick={() => setLastUpdated('Just now')}
            className="p-2 rounded-md transition-colors hover:bg-opacity-80"
            style={{ background: '#21262d', border: '1px solid #30363d', color: '#7d8590' }}
          >
            <RefreshCw size={16} />
          </button>
        </div>
      </div>

      {/* Stat Cards - Situ8 exact layout (6 cards in a row) */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <StatCard
          label="Active Doors"
          value={DEMO_STATS.activeDoors}
          subtitle="Online now"
          indicatorColor="#22c55e"
        />
        <StatCard
          label="Pending Approvals"
          value={DEMO_STATS.pendingApprovals}
          subtitle="Awaiting action"
          indicatorColor="#f97316"
        />
        <StatCard
          label="Today's Events"
          value={DEMO_STATS.todaysEvents}
          subtitle="Total received"
        />
        <StatCard
          label="Today's Alerts"
          value={DEMO_STATS.todaysAlerts}
          subtitle="Created"
          indicatorColor="#ef4444"
        />
        <StatCard
          label="Resolved Today"
          value={DEMO_STATS.resolvedToday}
          subtitle="Completed"
        />
        <StatCard
          label="Avg Response"
          value={DEMO_STATS.avgResponse}
          subtitle="Today"
        />
      </div>

      {/* Two Panel Row - Situ8 style */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Active Doors Panel */}
        <Panel
          title="Active Doors"
          count={`${DEMO_DOORS.length} doors`}
          indicatorColor="#22c55e"
        >
          {DEMO_DOORS.length > 0 ? (
            <div className="space-y-2">
              {DEMO_DOORS.map((door) => (
                <ListItem
                  key={door.id}
                  icon={<DoorOpen size={16} />}
                  title={door.name}
                  subtitle={door.lastEvent}
                  status={door.status}
                  statusColor={door.status === 'online' ? '#22c55e' : '#ef4444'}
                />
              ))}
            </div>
          ) : (
            <EmptyState emoji="🚪" text="No active doors" subtext="All doors are currently offline" />
          )}
          <PanelLink href="/doors" text="View all doors" />
        </Panel>

        {/* Recent Events Panel */}
        <Panel
          title="Recent Events"
          count={DEMO_EVENTS.length.toString()}
          indicatorColor="#8b5cf6"
        >
          {DEMO_EVENTS.length > 0 ? (
            <div className="space-y-2">
              {DEMO_EVENTS.map((event) => (
                <EventItem key={event.id} event={event} />
              ))}
            </div>
          ) : (
            <EmptyState emoji="📋" text="No recent events" subtext="All events have been processed" />
          )}
          <PanelLink href="/events" text="View all events" />
        </Panel>
      </div>

      {/* Active Cardholders Panel - Full width */}
      <Panel
        title="Active Cardholders"
        count="156 total"
        indicatorColor="#f59e0b"
      >
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
          <MiniStatCard label="Active" value="142" color="#22c55e" />
          <MiniStatCard label="Inactive" value="14" color="#7d8590" />
          <MiniStatCard label="Pending" value="8" color="#f59e0b" />
          <MiniStatCard label="Expired" value="3" color="#ef4444" />
        </div>
        <PanelLink href="/people" text="View all cardholders" />
      </Panel>
    </div>
  );
}

// ============================================================================
// STAT CARD COMPONENT - Situ8 exact style
// ============================================================================

function StatCard({
  label,
  value,
  subtitle,
  indicatorColor
}: {
  label: string;
  value: number | string;
  subtitle: string;
  indicatorColor?: string;
}) {
  return (
    <div
      className="rounded-md p-4"
      style={{
        background: '#161b22',
        border: '1px solid #30363d'
      }}
    >
      <div className="flex items-center gap-2 mb-2">
        {indicatorColor && (
          <span
            className="w-2 h-2 rounded-full"
            style={{ background: indicatorColor }}
          />
        )}
        <span className="text-sm" style={{ color: '#7d8590' }}>{label}</span>
      </div>
      <p
        className="text-3xl font-semibold mb-1"
        style={{ color: '#e6edf3' }}
      >
        {value}
      </p>
      <p className="text-xs" style={{ color: '#484f58' }}>{subtitle}</p>
    </div>
  );
}

// ============================================================================
// PANEL COMPONENT - Situ8 exact style
// ============================================================================

function Panel({
  title,
  count,
  indicatorColor,
  children
}: {
  title: string;
  count: string;
  indicatorColor: string;
  children: React.ReactNode;
}) {
  return (
    <div
      className="rounded-md overflow-hidden"
      style={{ background: '#161b22', border: '1px solid #30363d' }}
    >
      {/* Panel Header */}
      <div
        className="flex items-center justify-between px-4 py-3"
        style={{ borderBottom: '1px solid #30363d' }}
      >
        <div className="flex items-center gap-2">
          <span
            className="w-2 h-2 rounded-full"
            style={{ background: indicatorColor }}
          />
          <span className="font-medium" style={{ color: '#e6edf3' }}>{title}</span>
        </div>
        <span className="text-sm" style={{ color: '#7d8590' }}>{count}</span>
      </div>
      {/* Panel Content */}
      <div className="p-4">
        {children}
      </div>
    </div>
  );
}

// ============================================================================
// LIST ITEM COMPONENT
// ============================================================================

function ListItem({
  icon,
  title,
  subtitle,
  status,
  statusColor
}: {
  icon: React.ReactNode;
  title: string;
  subtitle: string;
  status: string;
  statusColor: string;
}) {
  return (
    <div
      className="flex items-center justify-between p-3 rounded-md cursor-pointer transition-colors"
      style={{ background: '#21262d' }}
      onMouseEnter={(e) => e.currentTarget.style.background = '#30363d'}
      onMouseLeave={(e) => e.currentTarget.style.background = '#21262d'}
    >
      <div className="flex items-center gap-3">
        <span style={{ color: '#7d8590' }}>{icon}</span>
        <div>
          <p className="text-sm font-medium" style={{ color: '#e6edf3' }}>{title}</p>
          <p className="text-xs" style={{ color: '#7d8590' }}>{subtitle}</p>
        </div>
      </div>
      <div className="flex items-center gap-2">
        <span className="w-2 h-2 rounded-full" style={{ background: statusColor }} />
        <span className="text-xs capitalize" style={{ color: statusColor }}>{status}</span>
      </div>
    </div>
  );
}

// ============================================================================
// EVENT ITEM COMPONENT
// ============================================================================

function EventItem({ event }: { event: typeof DEMO_EVENTS[0] }) {
  const isGranted = event.type === 'access_granted';

  return (
    <div
      className="flex items-center justify-between p-3 rounded-md"
      style={{ background: '#21262d' }}
    >
      <div className="flex items-center gap-3">
        {isGranted ? (
          <UserCheck size={16} style={{ color: '#22c55e' }} />
        ) : (
          <AlertTriangle size={16} style={{ color: '#ef4444' }} />
        )}
        <div>
          <p className="text-sm font-medium" style={{ color: '#e6edf3' }}>{event.user}</p>
          <p className="text-xs" style={{ color: '#7d8590' }}>{event.door}</p>
        </div>
      </div>
      <div className="text-right">
        <span
          className="text-xs px-2 py-1 rounded"
          style={{
            background: isGranted ? 'rgba(34, 197, 94, 0.15)' : 'rgba(239, 68, 68, 0.15)',
            color: isGranted ? '#22c55e' : '#ef4444'
          }}
        >
          {isGranted ? 'Granted' : 'Denied'}
        </span>
        <p className="text-xs mt-1" style={{ color: '#7d8590' }}>{event.time}</p>
      </div>
    </div>
  );
}

// ============================================================================
// MINI STAT CARD COMPONENT
// ============================================================================

function MiniStatCard({
  label,
  value,
  color
}: {
  label: string;
  value: string;
  color: string;
}) {
  return (
    <div
      className="text-center p-4 rounded-md"
      style={{ background: '#21262d' }}
    >
      <p className="text-2xl font-semibold" style={{ color }}>{value}</p>
      <p className="text-xs mt-1" style={{ color: '#7d8590' }}>{label}</p>
    </div>
  );
}

// ============================================================================
// EMPTY STATE COMPONENT - Situ8 style
// ============================================================================

function EmptyState({
  emoji,
  text,
  subtext
}: {
  emoji: string;
  text: string;
  subtext?: string;
}) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <span className="text-4xl mb-3 opacity-40">{emoji}</span>
      <p className="text-sm font-medium" style={{ color: '#7d8590' }}>{text}</p>
      {subtext && (
        <p className="text-xs mt-1" style={{ color: '#484f58' }}>{subtext}</p>
      )}
    </div>
  );
}

// ============================================================================
// PANEL LINK COMPONENT
// ============================================================================

function PanelLink({ href, text }: { href: string; text: string }) {
  return (
    <a
      href={href}
      className="flex items-center gap-1 mt-4 text-sm transition-colors hover:underline"
      style={{ color: '#58a6ff' }}
    >
      {text} <ChevronRight size={14} />
    </a>
  );
}

export default UnifiedDashboard;
