import { useEffect, useState } from 'react';
import { Activity, AlertTriangle, CheckCircle, Search, RefreshCw } from 'lucide-react';
import { eventsApi } from '../api/bifrost';
import { EVENT_TYPE_NAMES } from '../types';
import type { Event } from '../types';

function EventIcon({ eventType }: { eventType: number }) {
  switch (eventType) {
    case 0: // Access Granted
      return <CheckCircle size={18} className="text-aether-success" />;
    case 1: // Access Denied
    case 3: // Door Forced
    case 4: // Door Held
    case 5: // Tamper
      return <AlertTriangle size={18} className="text-aether-danger" />;
    default:
      return <Activity size={18} className="text-aether-primary" />;
  }
}

function EventBadge({ eventType }: { eventType: number }) {
  const isGood = eventType === 0 || eventType === 2;
  const isBad = [1, 3, 4, 5, 8].includes(eventType);

  return (
    <span
      className={`px-2 py-0.5 rounded text-xs font-medium ${
        isGood
          ? 'bg-aether-success/20 text-aether-success'
          : isBad
          ? 'bg-aether-danger/20 text-aether-danger'
          : 'bg-aether-primary/20 text-aether-primary'
      }`}
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
    // Auto-refresh every 5 seconds
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);

  const filteredEvents = events.filter((event) => {
    // Filter by type
    if (filter === 'access' && ![0, 1].includes(event.event_type)) return false;
    if (filter === 'alarms' && ![1, 3, 4, 5, 8].includes(event.event_type)) return false;

    // Filter by search
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

  const alarmCount = events.filter((e) => [1, 3, 4, 5, 8].includes(e.event_type)).length;

  if (loading && events.length === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-2 border-aether-primary border-t-transparent"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">Events</h1>
          <p className="text-gray-400">
            {events.length} total events
            {alarmCount > 0 && (
              <span className="text-aether-danger ml-2">({alarmCount} alarms)</span>
            )}
          </p>
        </div>
        <button
          onClick={fetchData}
          className="flex items-center gap-2 px-4 py-2 rounded-lg border border-white/10 text-gray-300 hover:bg-white/5"
        >
          <RefreshCw size={18} className={loading ? 'animate-spin' : ''} />
          Refresh
        </button>
      </div>

      {/* Filters */}
      <div className="glass rounded-xl p-4">
        <div className="flex flex-col sm:flex-row gap-4">
          {/* Search */}
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
            <input
              type="text"
              placeholder="Search events..."
              className="w-full bg-aether-darker border border-white/10 rounded-lg pl-10 pr-4 py-2 text-white focus:outline-none focus:border-aether-primary"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>

          {/* Filter Tabs */}
          <div className="flex rounded-lg bg-aether-darker p-1">
            <button
              onClick={() => setFilter('all')}
              className={`px-4 py-1.5 rounded text-sm font-medium transition-colors ${
                filter === 'all'
                  ? 'bg-aether-primary text-aether-darker'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              All
            </button>
            <button
              onClick={() => setFilter('access')}
              className={`px-4 py-1.5 rounded text-sm font-medium transition-colors ${
                filter === 'access'
                  ? 'bg-aether-primary text-aether-darker'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              Access
            </button>
            <button
              onClick={() => setFilter('alarms')}
              className={`px-4 py-1.5 rounded text-sm font-medium transition-colors ${
                filter === 'alarms'
                  ? 'bg-aether-danger text-white'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              Alarms
            </button>
          </div>
        </div>
      </div>

      {error && (
        <div className="glass rounded-xl p-4 border border-aether-danger/30">
          <p className="text-aether-danger">{error}</p>
        </div>
      )}

      {/* Events Table */}
      <div className="glass rounded-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="text-left text-gray-400 text-sm border-b border-white/10">
                <th className="py-3 px-4 font-medium">Event</th>
                <th className="py-3 px-4 font-medium">Type</th>
                <th className="py-3 px-4 font-medium">Card</th>
                <th className="py-3 px-4 font-medium">Door</th>
                <th className="py-3 px-4 font-medium">Details</th>
                <th className="py-3 px-4 font-medium">Time</th>
              </tr>
            </thead>
            <tbody>
              {filteredEvents.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-gray-400">
                    No events found
                  </td>
                </tr>
              ) : (
                filteredEvents.map((event) => (
                  <tr
                    key={event.event_id}
                    className="border-b border-white/5 hover:bg-white/5"
                  >
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-2">
                        <EventIcon eventType={event.event_type} />
                        <span className="text-gray-400 text-sm">#{event.event_id}</span>
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <EventBadge eventType={event.event_type} />
                    </td>
                    <td className="py-3 px-4 font-mono text-gray-300">
                      {event.card_number || '-'}
                    </td>
                    <td className="py-3 px-4 text-gray-300">
                      {event.door_id ? `Door ${event.door_id}` : '-'}
                    </td>
                    <td className="py-3 px-4 text-gray-400 text-sm max-w-xs truncate">
                      {event.details || '-'}
                    </td>
                    <td className="py-3 px-4 text-gray-400 text-sm whitespace-nowrap">
                      {new Date(event.timestamp).toLocaleString()}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="glass rounded-xl p-4">
          <p className="text-gray-400 text-sm">Total Events</p>
          <p className="text-2xl font-bold text-white">{events.length}</p>
        </div>
        <div className="glass rounded-xl p-4">
          <p className="text-gray-400 text-sm">Access Granted</p>
          <p className="text-2xl font-bold text-aether-success">
            {events.filter((e) => e.event_type === 0).length}
          </p>
        </div>
        <div className="glass rounded-xl p-4">
          <p className="text-gray-400 text-sm">Access Denied</p>
          <p className="text-2xl font-bold text-aether-danger">
            {events.filter((e) => e.event_type === 1).length}
          </p>
        </div>
        <div className="glass rounded-xl p-4">
          <p className="text-gray-400 text-sm">Other Alarms</p>
          <p className="text-2xl font-bold text-aether-warning">
            {events.filter((e) => [3, 4, 5, 8].includes(e.event_type)).length}
          </p>
        </div>
      </div>
    </div>
  );
}
