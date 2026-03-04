import { useEffect, useState } from 'react';
import { Settings as SettingsIcon, Server, Cloud, RefreshCw, Check, AlertCircle } from 'lucide-react';
import { systemApi } from '../api/bifrost';

interface HealthData {
  status: string;
  version: string;
  hal: {
    status: string;
    version?: string;
  };
  ambient?: {
    enabled: boolean;
    source_system_uid?: string;
    export_daemon?: {
      running: boolean;
      queue_size: number;
      events_sent: number;
      events_failed: number;
    };
    sync?: {
      devices_synced: number;
      persons_synced: number;
      last_full_sync?: string;
    };
  };
  api_versions: {
    v1: boolean;
    'v2.1': boolean;
    'v2.2': boolean;
  };
  websocket_clients: number;
}

export function Settings() {
  const [health, setHealth] = useState<HealthData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [syncing, setSyncing] = useState(false);

  const fetchHealth = async () => {
    try {
      const data = await systemApi.health();
      setHealth(data);
      setError(null);
    } catch (err) {
      setError('Failed to fetch system health');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
    const interval = setInterval(fetchHealth, 10000);
    return () => clearInterval(interval);
  }, []);

  const handleAmbientSync = async () => {
    setSyncing(true);
    try {
      // Call the sync endpoint
      const response = await fetch('/api/v1/ambient/sync', { method: 'POST' });
      if (!response.ok) throw new Error('Sync failed');
      await fetchHealth();
    } catch (err) {
      console.error('Ambient sync failed:', err);
    } finally {
      setSyncing(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-2 border-aether-primary border-t-transparent"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white">Settings</h1>
        <p className="text-gray-400">System configuration and status</p>
      </div>

      {error && (
        <div className="glass rounded-xl p-4 border border-aether-danger/30">
          <p className="text-aether-danger">{error}</p>
        </div>
      )}

      {/* System Status */}
      <div className="glass rounded-xl overflow-hidden">
        <div className="px-6 py-4 border-b border-white/10 flex items-center gap-3">
          <Server className="text-aether-primary" size={20} />
          <h2 className="text-lg font-semibold text-white">System Status</h2>
        </div>
        <div className="p-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            <div>
              <p className="text-gray-400 text-sm mb-1">System Status</p>
              <div className="flex items-center gap-2">
                {health?.status === 'healthy' ? (
                  <Check size={16} className="text-aether-success" />
                ) : (
                  <AlertCircle size={16} className="text-aether-danger" />
                )}
                <span className={health?.status === 'healthy' ? 'text-aether-success' : 'text-aether-danger'}>
                  {health?.status || 'Unknown'}
                </span>
              </div>
            </div>
            <div>
              <p className="text-gray-400 text-sm mb-1">Version</p>
              <p className="text-white font-mono">{health?.version || 'N/A'}</p>
            </div>
            <div>
              <p className="text-gray-400 text-sm mb-1">HAL Status</p>
              <div className="flex items-center gap-2">
                {health?.hal?.status === 'healthy' ? (
                  <Check size={16} className="text-aether-success" />
                ) : (
                  <AlertCircle size={16} className="text-aether-warning" />
                )}
                <span className={health?.hal?.status === 'healthy' ? 'text-aether-success' : 'text-aether-warning'}>
                  {health?.hal?.status || 'N/A'}
                </span>
              </div>
            </div>
            <div>
              <p className="text-gray-400 text-sm mb-1">WebSocket Clients</p>
              <p className="text-white">{health?.websocket_clients || 0}</p>
            </div>
          </div>

          <div className="mt-6 pt-6 border-t border-white/10">
            <p className="text-gray-400 text-sm mb-3">API Versions</p>
            <div className="flex gap-3">
              {Object.entries(health?.api_versions || {}).map(([version, available]) => (
                <span
                  key={version}
                  className={`px-3 py-1 rounded-full text-sm ${
                    available
                      ? 'bg-aether-success/20 text-aether-success'
                      : 'bg-gray-500/20 text-gray-500'
                  }`}
                >
                  {version}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Ambient.ai Integration */}
      <div className="glass rounded-xl overflow-hidden">
        <div className="px-6 py-4 border-b border-white/10 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Cloud className="text-aether-secondary" size={20} />
            <h2 className="text-lg font-semibold text-white">Ambient.ai Integration</h2>
          </div>
          {health?.ambient?.enabled && (
            <button
              onClick={handleAmbientSync}
              disabled={syncing}
              className="flex items-center gap-2 px-4 py-2 rounded-lg bg-aether-secondary/20 text-aether-secondary hover:bg-aether-secondary/30 disabled:opacity-50"
            >
              <RefreshCw size={16} className={syncing ? 'animate-spin' : ''} />
              {syncing ? 'Syncing...' : 'Full Sync'}
            </button>
          )}
        </div>
        <div className="p-6">
          {!health?.ambient?.enabled ? (
            <div className="text-center py-8">
              <Cloud size={48} className="mx-auto text-gray-500 mb-4" />
              <p className="text-gray-400">Ambient.ai integration is not configured</p>
              <p className="text-gray-500 text-sm mt-2">
                Set AMBIENT_API_KEY environment variable to enable
              </p>
            </div>
          ) : (
            <div className="space-y-6">
              {/* Connection Status */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                <div>
                  <p className="text-gray-400 text-sm mb-1">Status</p>
                  <div className="flex items-center gap-2">
                    {health.ambient.export_daemon?.running ? (
                      <>
                        <span className="w-2 h-2 rounded-full bg-aether-success animate-pulse"></span>
                        <span className="text-aether-success">Connected</span>
                      </>
                    ) : (
                      <>
                        <span className="w-2 h-2 rounded-full bg-aether-danger"></span>
                        <span className="text-aether-danger">Disconnected</span>
                      </>
                    )}
                  </div>
                </div>
                <div>
                  <p className="text-gray-400 text-sm mb-1">Queue Size</p>
                  <p className="text-white">{health.ambient.export_daemon?.queue_size || 0}</p>
                </div>
                <div>
                  <p className="text-gray-400 text-sm mb-1">Events Sent</p>
                  <p className="text-aether-success">{health.ambient.export_daemon?.events_sent || 0}</p>
                </div>
                <div>
                  <p className="text-gray-400 text-sm mb-1">Events Failed</p>
                  <p className={health.ambient.export_daemon?.events_failed ? 'text-aether-danger' : 'text-gray-400'}>
                    {health.ambient.export_daemon?.events_failed || 0}
                  </p>
                </div>
              </div>

              {/* Sync Status */}
              <div className="pt-6 border-t border-white/10">
                <p className="text-gray-400 text-sm mb-3">Entity Sync</p>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                  <div>
                    <p className="text-gray-500 text-xs mb-1">Devices Synced</p>
                    <p className="text-white text-lg">{health.ambient.sync?.devices_synced || 0}</p>
                  </div>
                  <div>
                    <p className="text-gray-500 text-xs mb-1">Persons Synced</p>
                    <p className="text-white text-lg">{health.ambient.sync?.persons_synced || 0}</p>
                  </div>
                  <div>
                    <p className="text-gray-500 text-xs mb-1">Last Full Sync</p>
                    <p className="text-white text-sm">
                      {health.ambient.sync?.last_full_sync
                        ? new Date(health.ambient.sync.last_full_sync).toLocaleString()
                        : 'Never'}
                    </p>
                  </div>
                </div>
              </div>

              {/* Source System UID */}
              {health.ambient.source_system_uid && (
                <div className="pt-6 border-t border-white/10">
                  <p className="text-gray-400 text-sm mb-1">Source System UID</p>
                  <p className="text-white font-mono text-sm break-all">
                    {health.ambient.source_system_uid}
                  </p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Configuration */}
      <div className="glass rounded-xl overflow-hidden">
        <div className="px-6 py-4 border-b border-white/10 flex items-center gap-3">
          <SettingsIcon className="text-aether-primary" size={20} />
          <h2 className="text-lg font-semibold text-white">Configuration</h2>
        </div>
        <div className="p-6">
          <div className="space-y-4">
            <div className="flex items-center justify-between py-3 border-b border-white/5">
              <div>
                <p className="text-white">API Base URL</p>
                <p className="text-gray-400 text-sm">Bifrost API endpoint</p>
              </div>
              <p className="text-gray-300 font-mono text-sm">
                {window.location.origin}
              </p>
            </div>
            <div className="flex items-center justify-between py-3 border-b border-white/5">
              <div>
                <p className="text-white">WebSocket URL</p>
                <p className="text-gray-400 text-sm">Real-time events</p>
              </div>
              <p className="text-gray-300 font-mono text-sm">
                ws://{window.location.host}/ws/live
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
