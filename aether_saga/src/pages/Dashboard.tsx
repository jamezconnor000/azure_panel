import { useEffect, useState } from 'react';
import { Activity, Users, DoorOpen, Shield, AlertTriangle, CheckCircle } from 'lucide-react';
import { systemApi, eventsApi } from '../api/bifrost';
import { EVENT_TYPE_NAMES } from '../types';
import type { DashboardData, Event } from '../types';

function StatCard({
  title,
  value,
  icon,
  color = 'primary'
}: {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  color?: 'primary' | 'success' | 'warning' | 'danger';
}) {
  const colorClasses = {
    primary: 'text-aether-primary border-aether-primary/30',
    success: 'text-aether-success border-aether-success/30',
    warning: 'text-aether-warning border-aether-warning/30',
    danger: 'text-aether-danger border-aether-danger/30',
  };

  return (
    <div className={`glass rounded-xl p-6 border-l-4 ${colorClasses[color]}`}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-gray-400 text-sm">{title}</p>
          <p className="text-3xl font-bold text-white mt-1">{value}</p>
        </div>
        <div className={colorClasses[color]}>{icon}</div>
      </div>
    </div>
  );
}

function EventRow({ event }: { event: Event }) {
  const isGranted = event.event_type === 0;

  return (
    <tr className="border-b border-white/5 hover:bg-white/5">
      <td className="py-3 px-4">
        <span className={`inline-flex items-center gap-2 ${isGranted ? 'text-aether-success' : 'text-aether-danger'}`}>
          {isGranted ? <CheckCircle size={16} /> : <AlertTriangle size={16} />}
          {EVENT_TYPE_NAMES[event.event_type] || `Type ${event.event_type}`}
        </span>
      </td>
      <td className="py-3 px-4 text-gray-300">{event.card_number || '-'}</td>
      <td className="py-3 px-4 text-gray-300">Door {event.door_id || '-'}</td>
      <td className="py-3 px-4 text-gray-400">{new Date(event.timestamp).toLocaleString()}</td>
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
          <h1 className="text-2xl font-bold text-white">Dashboard</h1>
          <p className="text-gray-400">System overview and recent activity</p>
        </div>
        <div className={`flex items-center gap-2 px-4 py-2 rounded-full ${systemOnline ? 'bg-aether-success/20 text-aether-success' : 'bg-aether-danger/20 text-aether-danger'}`}>
          <span className={`w-2 h-2 rounded-full ${systemOnline ? 'bg-aether-success' : 'bg-aether-danger'} animate-pulse`}></span>
          {systemOnline ? 'System Online' : 'System Offline'}
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Total Cards"
          value={dashboard?.cards?.total || 0}
          icon={<Users size={32} />}
          color="primary"
        />
        <StatCard
          title="Active Cards"
          value={dashboard?.cards?.active || 0}
          icon={<Shield size={32} />}
          color="success"
        />
        <StatCard
          title="Doors"
          value={dashboard?.doors?.total || 0}
          icon={<DoorOpen size={32} />}
          color="primary"
        />
        <StatCard
          title="Events Today"
          value={dashboard?.events?.today || 0}
          icon={<Activity size={32} />}
          color="warning"
        />
      </div>

      {/* Recent Events */}
      <div className="glass rounded-xl overflow-hidden">
        <div className="px-6 py-4 border-b border-white/10">
          <h2 className="text-lg font-semibold text-white">Recent Events</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="text-left text-gray-400 text-sm border-b border-white/10">
                <th className="py-3 px-4 font-medium">Event</th>
                <th className="py-3 px-4 font-medium">Card</th>
                <th className="py-3 px-4 font-medium">Door</th>
                <th className="py-3 px-4 font-medium">Time</th>
              </tr>
            </thead>
            <tbody>
              {events.length === 0 ? (
                <tr>
                  <td colSpan={4} className="py-8 text-center text-gray-400">
                    No recent events
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
      <div className="glass rounded-xl p-6">
        <h2 className="text-lg font-semibold text-white mb-4">System Information</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div>
            <p className="text-gray-400">HAL Version</p>
            <p className="text-white font-mono">{dashboard?.hal_version || 'N/A'}</p>
          </div>
          <div>
            <p className="text-gray-400">Status</p>
            <p className={systemOnline ? 'text-aether-success' : 'text-aether-danger'}>
              {dashboard?.system_status || 'Unknown'}
            </p>
          </div>
          <div>
            <p className="text-gray-400">Total Events</p>
            <p className="text-white">{dashboard?.events?.total || 0}</p>
          </div>
          <div>
            <p className="text-gray-400">Last Update</p>
            <p className="text-white font-mono">
              {dashboard?.timestamp ? new Date(dashboard.timestamp).toLocaleTimeString() : 'N/A'}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
