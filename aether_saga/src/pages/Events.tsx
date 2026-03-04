/**
 * Events - Situ8-style Event Log
 */

import { useEffect, useState } from 'react';
import { Activity, AlertTriangle, CheckCircle, Search, RefreshCw } from 'lucide-react';
import { eventsApi } from '../api/bifrost';
import { EVENT_TYPE_NAMES } from '../types';
import type { Event } from '../types';

// DEMO MODE
const DEMO_MODE = true;
const MOCK_EVENTS: Event[] = [
  { event_id: 1001, event_type: 0, card_number: 'A1B2C3D4', door_id: 1, timestamp: new Date(Date.now() - 60000).toISOString(), details: 'Main Entrance - John Smith' },
  { event_id: 1002, event_type: 1, card_number: 'X9Y8Z7W6', door_id: 3, timestamp: new Date(Date.now() - 120000).toISOString(), details: 'Server Room - Unknown Card' },
  { event_id: 1003, event_type: 0, card_number: 'E5F6G7H8', door_id: 2, timestamp: new Date(Date.now() - 180000).toISOString(), details: 'Side Entrance - Sarah Johnson' },
  { event_id: 1004, event_type: 0, card_number: 'I9J0K1L2', door_id: 1, timestamp: new Date(Date.now() - 240000).toISOString(), details: 'Main Entrance - Mike Rodriguez' },
  { event_id: 1005, event_type: 3, card_number: '', door_id: 5, timestamp: new Date(Date.now() - 300000).toISOString(), details: 'Emergency Exit - Door Forced' },
  { event_id: 1006, event_type: 0, card_number: 'M3N4O5P6', door_id: 4, timestamp: new Date(Date.now() - 360000).toISOString(), details: 'Parking Garage - Lisa Kim' },
  { event_id: 1007, event_type: 0, card_number: 'Q7R8S9T0', door_id: 1, timestamp: new Date(Date.now() - 420000).toISOString(), details: 'Main Entrance - David Chen' },
  { event_id: 1008, event_type: 1, card_number: 'EXPIRED01', door_id: 2, timestamp: new Date(Date.now() - 480000).toISOString(), details: 'Side Entrance - Expired Card' },
  { event_id: 1009, event_type: 0, card_number: 'U1V2W3X4', door_id: 1, timestamp: new Date(Date.now() - 540000).toISOString(), details: 'Main Entrance - Amanda Foster' },
  { event_id: 1010, event_type: 4, card_number: '', door_id: 6, timestamp: new Date(Date.now() - 600000).toISOString(), details: 'Loading Dock - Door Held Open' },
  { event_id: 1011, event_type: 0, card_number: 'Y5Z6A7B8', door_id: 3, timestamp: new Date(Date.now() - 660000).toISOString(), details: 'Server Room - Robert Johnson' },
  { event_id: 1012, event_type: 5, card_number: '', door_id: 2, timestamp: new Date(Date.now() - 720000).toISOString(), details: 'Side Entrance - Tamper Detected' },
];

function EventIcon({ eventType }: { eventType: number }) {
  switch (eventType) {
    case 0:
      return <CheckCircle size={16} style={{ color: '#22c55e' }} />;
    case 1:
    case 3:
    case 4:
    case 5:
      return <AlertTriangle size={16} style={{ color: '#ef4444' }} />;
    default:
      return <Activity size={16} style={{ color: '#8b5cf6' }} />;
  }
}

function EventBadge({ eventType }: { eventType: number }) {
  const isGood = eventType === 0 || eventType === 2;
  const isBad = [1, 3, 4, 5, 8].includes(eventType);

  return (
    <span
      className="px-2.5 py-1 rounded text-xs font-medium"
      style={{
        background: isGood
          ? 'rgba(34, 197, 94, 0.15)'
          : isBad
          ? 'rgba(239, 68, 68, 0.15)'
          : 'rgba(139, 92, 246, 0.15)',
        color: isGood ? '#22c55e' : isBad ? '#ef4444' : '#8b5cf6'
      }}
    >
      {EVENT_TYPE_NAMES[eventType] || `Type ${eventType}`}
    </span>
  );
}

export function Events() {
  const [events, setEvents] = useState<Event[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState<'all' | 'access' | 'alarms'>('all');

  const fetchData = async () => {
    if (DEMO_MODE) {
      setEvents(MOCK_EVENTS);
      setLoading(false);
      return;
    }
    try {
      setLoading(true);
      const data = await eventsApi.list(500, 0);
      setEvents(data.events || []);
      setError(null);
    } catch (err) {
      setError('Failed to load events');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);

  const filteredEvents = events.filter((event) => {
    if (filter === 'access' && ![0, 1].includes(event.event_type)) return false;
    if (filter === 'alarms' && ![1, 3, 4, 5, 8].includes(event.event_type)) return false;

    if (search) {
      const searchLower = search.toLowerCase();
      const matchesCard = event.card_number?.toLowerCase().includes(searchLower);
      const matchesDoor = `door ${event.door_id}`.includes(searchLower);
      const matchesType = EVENT_TYPE_NAMES[event.event_type]?.toLowerCase().includes(searchLower);
      const matchesDetails = event.details?.toLowerCase().includes(searchLower);
      return matchesCard || matchesDoor || matchesType || matchesDetails;
    }

    return true;
  });

  const grantedCount = events.filter((e) => e.event_type === 0).length;
  const deniedCount = events.filter((e) => e.event_type === 1).length;
  const alarmCount = events.filter((e) => [3, 4, 5, 8].includes(e.event_type)).length;

  if (loading && events.length === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-2 border-t-transparent" style={{ borderColor: '#8b5cf6', borderTopColor: 'transparent' }} />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span
              className="w-2 h-2 rounded-full"
              style={{ background: '#8b5cf6' }}
            />
            <h1 className="text-xl font-semibold" style={{ color: '#e6edf3' }}>
              Events
            </h1>
          </div>
          <p className="text-sm" style={{ color: '#7d8590' }}>
            {events.length} total events
            {alarmCount > 0 && (
              <span style={{ color: '#ef4444' }}> ({alarmCount} alarms)</span>
            )}
          </p>
        </div>
        <button
          onClick={fetchData}
          className="flex items-center gap-2 px-4 py-2 rounded-md transition-colors"
          style={{ background: '#21262d', border: '1px solid #30363d', color: '#7d8590' }}
        >
          <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
          Refresh
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-4">
        <div className="p-4 rounded-md" style={{ background: '#161b22', border: '1px solid #30363d' }}>
          <p className="text-xs" style={{ color: '#7d8590' }}>Total Events</p>
          <p className="text-2xl font-semibold mt-1" style={{ color: '#e6edf3' }}>{events.length}</p>
        </div>
        <div className="p-4 rounded-md" style={{ background: '#161b22', border: '1px solid #30363d' }}>
          <div className="flex items-center gap-2 mb-1">
            <span className="w-2 h-2 rounded-full" style={{ background: '#22c55e' }} />
            <p className="text-xs" style={{ color: '#7d8590' }}>Access Granted</p>
          </div>
          <p className="text-2xl font-semibold" style={{ color: '#22c55e' }}>{grantedCount}</p>
        </div>
        <div className="p-4 rounded-md" style={{ background: '#161b22', border: '1px solid #30363d' }}>
          <div className="flex items-center gap-2 mb-1">
            <span className="w-2 h-2 rounded-full" style={{ background: '#ef4444' }} />
            <p className="text-xs" style={{ color: '#7d8590' }}>Access Denied</p>
          </div>
          <p className="text-2xl font-semibold" style={{ color: '#ef4444' }}>{deniedCount}</p>
        </div>
        <div className="p-4 rounded-md" style={{ background: '#161b22', border: '1px solid #30363d' }}>
          <div className="flex items-center gap-2 mb-1">
            <span className="w-2 h-2 rounded-full" style={{ background: '#f97316' }} />
            <p className="text-xs" style={{ color: '#7d8590' }}>Other Alarms</p>
          </div>
          <p className="text-2xl font-semibold" style={{ color: '#f97316' }}>{alarmCount}</p>
        </div>
      </div>

      {/* Search & Filters */}
      <div className="flex items-center gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2" size={18} style={{ color: '#7d8590' }} />
          <input
            type="text"
            placeholder="Search events..."
            className="w-full rounded-md pl-11 pr-4 py-2.5 focus:outline-none"
            style={{ background: '#0d1117', border: '1px solid #30363d', color: '#e6edf3' }}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <div className="flex rounded-md p-1" style={{ background: '#21262d' }}>
          <button
            onClick={() => setFilter('all')}
            className="px-4 py-1.5 rounded text-sm font-medium transition-colors"
            style={{
              background: filter === 'all' ? '#30363d' : 'transparent',
              color: filter === 'all' ? '#e6edf3' : '#7d8590'
            }}
          >
            All
          </button>
          <button
            onClick={() => setFilter('access')}
            className="px-4 py-1.5 rounded text-sm font-medium transition-colors"
            style={{
              background: filter === 'access' ? 'rgba(34, 197, 94, 0.15)' : 'transparent',
              color: filter === 'access' ? '#22c55e' : '#7d8590'
            }}
          >
            Access
          </button>
          <button
            onClick={() => setFilter('alarms')}
            className="px-4 py-1.5 rounded text-sm font-medium transition-colors"
            style={{
              background: filter === 'alarms' ? 'rgba(239, 68, 68, 0.15)' : 'transparent',
              color: filter === 'alarms' ? '#ef4444' : '#7d8590'
            }}
          >
            Alarms
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-md" style={{ background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)' }}>
          <p style={{ color: '#ef4444' }}>{error}</p>
        </div>
      )}

      {/* Events Table */}
      <div className="rounded-md overflow-hidden" style={{ background: '#161b22', border: '1px solid #30363d' }}>
        <table className="w-full">
          <thead>
            <tr style={{ borderBottom: '1px solid #30363d', background: '#0d1117' }}>
              <th className="text-left py-3 px-4 text-sm font-medium" style={{ color: '#7d8590' }}>EVENT</th>
              <th className="text-left py-3 px-4 text-sm font-medium" style={{ color: '#7d8590' }}>TYPE</th>
              <th className="text-left py-3 px-4 text-sm font-medium" style={{ color: '#7d8590' }}>CARD</th>
              <th className="text-left py-3 px-4 text-sm font-medium" style={{ color: '#7d8590' }}>DOOR</th>
              <th className="text-left py-3 px-4 text-sm font-medium" style={{ color: '#7d8590' }}>DETAILS</th>
              <th className="text-left py-3 px-4 text-sm font-medium" style={{ color: '#7d8590' }}>TIME</th>
            </tr>
          </thead>
          <tbody>
            {filteredEvents.length === 0 ? (
              <tr>
                <td colSpan={6} className="py-12 text-center" style={{ color: '#7d8590' }}>
                  No events found
                </td>
              </tr>
            ) : (
              filteredEvents.map((event) => (
                <tr
                  key={event.event_id}
                  className="transition-colors"
                  style={{ borderBottom: '1px solid #21262d' }}
                  onMouseEnter={(e) => e.currentTarget.style.background = '#21262d'}
                  onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
                >
                  <td className="py-3 px-4">
                    <div className="flex items-center gap-2">
                      <EventIcon eventType={event.event_type} />
                      <span className="text-sm" style={{ color: '#7d8590' }}>#{event.event_id}</span>
                    </div>
                  </td>
                  <td className="py-3 px-4">
                    <EventBadge eventType={event.event_type} />
                  </td>
                  <td className="py-3 px-4 font-mono text-sm" style={{ color: '#7d8590' }}>
                    {event.card_number || '-'}
                  </td>
                  <td className="py-3 px-4" style={{ color: '#7d8590' }}>
                    {event.door_id ? `Door ${event.door_id}` : '-'}
                  </td>
                  <td className="py-3 px-4 text-sm max-w-xs truncate" style={{ color: '#7d8590' }}>
                    {event.details || '-'}
                  </td>
                  <td className="py-3 px-4 text-sm whitespace-nowrap" style={{ color: '#7d8590' }}>
                    {new Date(event.timestamp).toLocaleString()}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
