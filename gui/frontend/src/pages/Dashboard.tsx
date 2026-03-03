import { useQuery } from '@tanstack/react-query';
import { useEffect, useState } from 'react';
import { apiClient } from '../api/client';
import { Server, Cpu, Activity, AlertCircle, CheckCircle2, Clock } from 'lucide-react';
import type { ReaderHealthSummary, PanelHealth } from '../types';

export default function Dashboard() {
  const [realtimeEvents, setRealtimeEvents] = useState<any[]>([]);

  // Fetch readers health
  const { data: readersData, isLoading: readersLoading } = useQuery({
    queryKey: ['readers', 'health'],
    queryFn: () => apiClient.getAllReadersHealth(),
    refetchInterval: 5000, // Refresh every 5 seconds
  });

  // Fetch panel health
  const { data: panelData, isLoading: panelLoading } = useQuery({
    queryKey: ['panel', 1, 'health'],
    queryFn: () => apiClient.getPanelHealth(1),
    refetchInterval: 5000,
  });

  // Listen for WebSocket events
  useEffect(() => {
    const unsubscribe = apiClient.onWebSocketMessage('*', (message) => {
      setRealtimeEvents((prev) => [
        { ...message, timestamp: new Date().toISOString() },
        ...prev.slice(0, 9), // Keep last 10 events
      ]);
    });

    return unsubscribe;
  }, []);

  const getHealthColor = (health: string) => {
    switch (health) {
      case 'excellent':
        return 'text-green-500';
      case 'good':
        return 'text-lime-500';
      case 'fair':
        return 'text-yellow-500';
      case 'poor':
        return 'text-orange-500';
      case 'critical':
        return 'text-red-500';
      default:
        return 'text-slate-500';
    }
  };

  const getHealthBadge = (health: string) => {
    switch (health) {
      case 'excellent':
        return 'badge-success';
      case 'good':
        return 'badge-success';
      case 'fair':
        return 'badge-warning';
      case 'poor':
        return 'badge-warning';
      case 'critical':
        return 'badge-danger';
      default:
        return 'badge-info';
    }
  };

  if (readersLoading || panelLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-slate-400">Loading dashboard...</div>
      </div>
    );
  }

  const readers = readersData?.readers || [];
  const panel = panelData;

  // Calculate statistics
  const totalReaders = readers.length;
  const healthyReaders = readers.filter((r) => r.overall_health === 'excellent' || r.overall_health === 'good').length;
  const readersWithIssues = readers.filter((r) => r.issues > 0).length;

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-bold text-white">Dashboard</h1>
        <p className="text-slate-400 mt-2">
          Real-time monitoring of HAL access control system
        </p>
      </div>

      {/* System Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Total Readers */}
        <div className="card">
          <div className="card-body">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-slate-400 text-sm">Total Readers</p>
                <p className="text-3xl font-bold text-white mt-1">{totalReaders}</p>
                <p className="text-sm text-green-500 mt-2">
                  {healthyReaders} healthy
                </p>
              </div>
              <Cpu className="h-12 w-12 text-primary-500" />
            </div>
          </div>
        </div>

        {/* Readers with Issues */}
        <div className="card">
          <div className="card-body">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-slate-400 text-sm">Issues Detected</p>
                <p className="text-3xl font-bold text-white mt-1">{readersWithIssues}</p>
                <p className="text-sm text-slate-500 mt-2">
                  {readersWithIssues === 0 ? 'All systems nominal' : 'Requires attention'}
                </p>
              </div>
              <AlertCircle
                className={`h-12 w-12 ${readersWithIssues > 0 ? 'text-yellow-500' : 'text-green-500'}`}
              />
            </div>
          </div>
        </div>

        {/* Panel Status */}
        <div className="card">
          <div className="card-body">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-slate-400 text-sm">Panel Status</p>
                <p className="text-3xl font-bold text-white mt-1">
                  {panel?.online ? 'Online' : 'Offline'}
                </p>
                <p className="text-sm text-slate-500 mt-2">
                  Uptime: {panel?.uptime_hours.toFixed(1)}h
                </p>
              </div>
              <Server
                className={`h-12 w-12 ${panel?.online ? 'text-green-500' : 'text-red-500'}`}
              />
            </div>
          </div>
        </div>

        {/* System Health */}
        <div className="card">
          <div className="card-body">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-slate-400 text-sm">System Health</p>
                <p className="text-3xl font-bold text-white mt-1">
                  {panel?.health_score || 0}%
                </p>
                <p className={`text-sm mt-2 ${getHealthColor(panel?.overall_health || 'unknown')}`}>
                  {panel?.overall_health || 'Unknown'}
                </p>
              </div>
              <Activity className="h-12 w-12 text-primary-500" />
            </div>
          </div>
        </div>
      </div>

      {/* Readers Health */}
      <div className="card">
        <div className="card-header">
          <h2 className="text-xl font-semibold text-white">Readers Health</h2>
        </div>
        <div className="card-body">
          <div className="space-y-4">
            {readers.map((reader) => (
              <div
                key={reader.reader_id}
                className="flex items-center justify-between p-4 bg-slate-700 rounded-lg"
              >
                <div className="flex items-center space-x-4">
                  <Cpu className={`h-6 w-6 ${getHealthColor(reader.overall_health)}`} />
                  <div>
                    <p className="font-medium text-white">{reader.reader_name}</p>
                    <p className="text-sm text-slate-400">
                      Health Score: {reader.health_score}/100
                    </p>
                  </div>
                </div>

                <div className="flex items-center space-x-4">
                  {reader.issues > 0 && (
                    <span className="badge badge-warning">{reader.issues} issue(s)</span>
                  )}
                  <span className={`badge ${getHealthBadge(reader.overall_health)}`}>
                    {reader.overall_health}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Panel Health Details */}
      {panel && (
        <div className="card">
          <div className="card-header">
            <h2 className="text-xl font-semibold text-white">{panel.panel_name} Status</h2>
          </div>
          <div className="card-body">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {/* Power Status */}
              <div>
                <h3 className="text-sm font-medium text-slate-400 mb-2">Power Status</h3>
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-white">Main Power</span>
                    {panel.main_power ? (
                      <CheckCircle2 className="h-5 w-5 text-green-500" />
                    ) : (
                      <AlertCircle className="h-5 w-5 text-red-500" />
                    )}
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-white">Battery</span>
                    <span className="text-slate-300">
                      {panel.battery_charge_percent?.toFixed(0)}% ({panel.battery_voltage?.toFixed(1)}V)
                    </span>
                  </div>
                </div>
              </div>

              {/* I/O Status */}
              <div>
                <h3 className="text-sm font-medium text-slate-400 mb-2">I/O Status</h3>
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-white">Inputs</span>
                    <span className="text-slate-300">
                      {panel.inputs_ok} OK, {panel.inputs_fault} fault
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-white">Outputs</span>
                    <span className="text-slate-300">
                      {panel.outputs_ok} OK, {panel.outputs_fault} fault
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-white">Relays</span>
                    <span className="text-slate-300">
                      {panel.relays_ok} OK, {panel.relays_fault} fault
                    </span>
                  </div>
                </div>
              </div>

              {/* Network Status */}
              <div>
                <h3 className="text-sm font-medium text-slate-400 mb-2">Network Status</h3>
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-white">IP Address</span>
                    <span className="text-slate-300">{panel.ip_address}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-white">Uptime</span>
                    <span className="text-slate-300">{panel.network_uptime_percent.toFixed(1)}%</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-white">Latency</span>
                    <span className="text-slate-300">{panel.avg_latency_ms.toFixed(1)}ms</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Critical Alerts */}
            {panel.critical_alerts && panel.critical_alerts.length > 0 && (
              <div className="mt-6 p-4 bg-red-900/20 border border-red-500 rounded-lg">
                <h3 className="text-sm font-medium text-red-400 mb-2">Critical Alerts</h3>
                <ul className="space-y-1">
                  {panel.critical_alerts.map((alert, index) => (
                    <li key={index} className="text-red-300 text-sm">
                      • {alert}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Real-time Events */}
      <div className="card">
        <div className="card-header">
          <h2 className="text-xl font-semibold text-white">Real-time Events</h2>
        </div>
        <div className="card-body">
          {realtimeEvents.length === 0 ? (
            <p className="text-slate-400 text-center py-8">
              Waiting for real-time events...
            </p>
          ) : (
            <div className="space-y-2">
              {realtimeEvents.map((event, index) => (
                <div
                  key={index}
                  className="flex items-start space-x-3 p-3 bg-slate-700 rounded-lg"
                >
                  <Clock className="h-5 w-5 text-slate-400 mt-0.5" />
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <span className="font-medium text-white">{event.type}</span>
                      <span className="text-sm text-slate-400">
                        {new Date(event.timestamp).toLocaleTimeString()}
                      </span>
                    </div>
                    <p className="text-sm text-slate-300 mt-1">
                      {JSON.stringify(event, null, 2)}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
