/**
 * Dashboard - The Great Hall
 * "From here, all of Midgard is watched"
 */

import { useEffect, useState } from 'react';
import { Activity, Users, DoorOpen, Shield, AlertTriangle, CheckCircle, Swords } from 'lucide-react';
import { systemApi, eventsApi } from '../api/bifrost';
import { EVENT_TYPE_NAMES } from '../types';
import type { DashboardData, Event } from '../types';
import { NorseStatCard } from '../components/NorseStatCard';

// DEMO MODE - Mock data for demonstration
const DEMO_MODE = true;

const MOCK_DASHBOARD: DashboardData = {
  system_status: 'healthy',
  hal_version: '4.0.0',
  cards: { total: 1247, active: 1189 },
  doors: { total: 24 },
  events: { total: 48293, today: 847 },
  recent_events: [],
  timestamp: new Date().toISOString(),
};

const MOCK_EVENTS: Event[] = [
  { event_id: 1001, event_type: 0, card_number: 'A1B2C3D4', door_id: 1, timestamp: new Date(Date.now() - 60000).toISOString(), details: 'Main Entrance' },
  { event_id: 1002, event_type: 1, card_number: 'X9Y8Z7W6', door_id: 3, timestamp: new Date(Date.now() - 120000).toISOString(), details: 'Server Room - Invalid Card' },
  { event_id: 1003, event_type: 0, card_number: 'E5F6G7H8', door_id: 2, timestamp: new Date(Date.now() - 180000).toISOString(), details: 'Side Entrance' },
  { event_id: 1004, event_type: 0, card_number: 'I9J0K1L2', door_id: 1, timestamp: new Date(Date.now() - 240000).toISOString(), details: 'Main Entrance' },
  { event_id: 1005, event_type: 3, card_number: '', door_id: 5, timestamp: new Date(Date.now() - 300000).toISOString(), details: 'Emergency Exit - Door Forced' },
  { event_id: 1006, event_type: 0, card_number: 'M3N4O5P6', door_id: 4, timestamp: new Date(Date.now() - 360000).toISOString(), details: 'Parking Garage' },
  { event_id: 1007, event_type: 0, card_number: 'Q7R8S9T0', door_id: 1, timestamp: new Date(Date.now() - 420000).toISOString(), details: 'Main Entrance' },
  { event_id: 1008, event_type: 1, card_number: 'EXPIRED01', door_id: 2, timestamp: new Date(Date.now() - 480000).toISOString(), details: 'Side Entrance - Expired Card' },
];

// Norse-style runes for stat cards
const STAT_RUNES = {
  cards: 'ᚠ',      // Fehu - wealth/abundance
  active: 'ᛉ',     // Algiz - protection
  doors: 'ᚨ',      // Ansuz - doorway/portal
  events: 'ᚱ',     // Raido - journey/activity
};

function EventRow({ event }: { event: Event }) {
  const isGranted = event.event_type === 0;

  return (
    <tr className="border-b border-frost-blue/10 hover:bg-frost-blue/5 transition-colors duration-200">
      <td className="py-3 px-4">
        <span className={`inline-flex items-center gap-2 ${isGranted ? 'text-aether-success' : 'text-blood-red'}`}>
          {isGranted ? <CheckCircle size={16} /> : <AlertTriangle size={16} />}
          <span className="font-rajdhani">{EVENT_TYPE_NAMES[event.event_type] || `Type ${event.event_type}`}</span>
        </span>
      </td>
      <td className="py-3 px-4 text-ice-white/70 font-rajdhani font-mono">{event.card_number || '-'}</td>
      <td className="py-3 px-4 text-ice-white/70 font-rajdhani">Door {event.door_id || '-'}</td>
      <td className="py-3 px-4 text-frost-light/50 font-rajdhani text-sm">{new Date(event.timestamp).toLocaleString()}</td>
    </tr>
  );
}

export function Dashboard() {
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [events, setEvents] = useState<Event[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchData() {
      if (DEMO_MODE) {
        // Use mock data in demo mode
        setDashboard(MOCK_DASHBOARD);
        setEvents(MOCK_EVENTS);
        setLoading(false);
        return;
      }

      try {
        const [dashData, eventsData] = await Promise.all([
          systemApi.dashboard(),
          eventsApi.list(20, 0),
        ]);
        setDashboard(dashData);
        setEvents(eventsData.events || []);
        setError(null);
      } catch (err) {
        setError('Failed to load dashboard data');
        console.error(err);
      } finally {
        setLoading(false);
      }
    }

    fetchData();
    const interval = setInterval(fetchData, 10000); // Refresh every 10s
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-2 border-aether-primary border-t-transparent"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="glass rounded-xl p-6 border border-aether-danger/30">
        <p className="text-aether-danger">{error}</p>
      </div>
    );
  }

  const systemOnline = dashboard?.system_status === 'healthy';

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-cinzel font-bold text-ice-white tracking-wide flex items-center gap-3">
            <span className="text-frost-blue/50">ᚺ</span>
            DASHBOARD
          </h1>
          <p className="text-frost-light/50 font-rajdhani tracking-wider">System overview and recent activity</p>
        </div>
        <div className={`flex items-center gap-2 px-5 py-2.5 rounded-lg border ${systemOnline ? 'bg-aether-success/10 text-aether-success border-aether-success/30' : 'bg-blood-red/10 text-blood-red border-blood-red/30'}`}>
          <span className={`w-2.5 h-2.5 rounded-full ${systemOnline ? 'bg-aether-success' : 'bg-blood-red'} animate-pulse`}></span>
          <span className="font-rajdhani font-medium tracking-wide">{systemOnline ? 'System Online' : 'System Offline'}</span>
        </div>
      </div>

      {/* Stats Grid - The Rune Stones */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <NorseStatCard
          title="Total Cards"
          value={dashboard?.cards?.total || 0}
          icon={<Users size={32} />}
          color="frost"
          rune={STAT_RUNES.cards}
        />
        <NorseStatCard
          title="Active Cards"
          value={dashboard?.cards?.active || 0}
          icon={<Shield size={32} />}
          color="gold"
          rune={STAT_RUNES.active}
        />
        <NorseStatCard
          title="Doors"
          value={dashboard?.doors?.total || 0}
          icon={<DoorOpen size={32} />}
          color="frost"
          rune={STAT_RUNES.doors}
        />
        <NorseStatCard
          title="Events Today"
          value={dashboard?.events?.today || 0}
          icon={<Activity size={32} />}
          color="ember"
          rune={STAT_RUNES.events}
        />
      </div>

      {/* Recent Events */}
      <div className="card-norse rounded-xl overflow-hidden">
        <div className="px-6 py-4 border-b border-frost-blue/20 bg-gradient-to-r from-stone-dark to-transparent">
          <h2 className="text-lg font-cinzel font-semibold text-frost-light tracking-wider flex items-center gap-2">
            <span className="text-frost-blue/40">ᚱ</span>
            RECENT EVENTS
          </h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="text-left text-frost-blue text-sm border-b border-frost-blue/20 bg-stone-darker/50">
                <th className="py-3 px-4 font-cinzel font-medium tracking-wider">EVENT</th>
                <th className="py-3 px-4 font-cinzel font-medium tracking-wider">CARD</th>
                <th className="py-3 px-4 font-cinzel font-medium tracking-wider">DOOR</th>
                <th className="py-3 px-4 font-cinzel font-medium tracking-wider">TIME</th>
              </tr>
            </thead>
            <tbody>
              {events.length === 0 ? (
                <tr>
                  <td colSpan={4} className="py-8 text-center text-frost-light/40 font-rajdhani">
                    The chronicle is empty
                  </td>
                </tr>
              ) : (
                events.map((event) => (
                  <EventRow key={event.event_id} event={event} />
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* System Info */}
      <div className="card-norse rounded-xl p-6">
        <h2 className="text-lg font-cinzel font-semibold text-frost-light mb-4 tracking-wider flex items-center gap-2">
          <span className="text-frost-blue/40">ᛊ</span>
          SYSTEM INFORMATION
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6 text-sm">
          <div className="space-y-1">
            <p className="text-frost-light/40 font-rajdhani tracking-wider uppercase text-xs">HAL Version</p>
            <p className="text-frost-light font-mono text-lg">{dashboard?.hal_version || 'N/A'}</p>
          </div>
          <div className="space-y-1">
            <p className="text-frost-light/40 font-rajdhani tracking-wider uppercase text-xs">Status</p>
            <p className={`text-lg font-rajdhani font-medium ${systemOnline ? 'text-aether-success' : 'text-blood-red'}`}>
              {systemOnline ? 'ONLINE' : 'OFFLINE'}
            </p>
          </div>
          <div className="space-y-1">
            <p className="text-frost-light/40 font-rajdhani tracking-wider uppercase text-xs">Total Events</p>
            <p className="text-frost-light font-rajdhani text-lg">{(dashboard?.events?.total || 0).toLocaleString()}</p>
          </div>
          <div className="space-y-1">
            <p className="text-frost-light/40 font-rajdhani tracking-wider uppercase text-xs">Last Update</p>
            <p className="text-frost-light font-mono text-lg">
              {dashboard?.timestamp ? new Date(dashboard.timestamp).toLocaleTimeString() : 'N/A'}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
