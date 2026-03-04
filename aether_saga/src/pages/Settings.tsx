/**
 * Settings - Situ8-style System Configuration
 */

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
        <div className="animate-spin rounded-full h-8 w-8 border-2 border-t-transparent" style={{ borderColor: '#8b5cf6', borderTopColor: 'transparent' }} />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 mb-1">
          <span
            className="w-2 h-2 rounded-full"
            style={{ background: '#8b5cf6' }}
          />
          <h1 className="text-xl font-semibold" style={{ color: '#e6edf3' }}>
            Settings
          </h1>
        </div>
        <p className="text-sm" style={{ color: '#7d8590' }}>
          System configuration and status
        </p>
      </div>

      {error && (
        <div className="p-4 rounded-md" style={{ background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)' }}>
          <p style={{ color: '#ef4444' }}>{error}</p>
        </div>
      )}

      {/* System Status */}
      <div className="rounded-md overflow-hidden" style={{ background: '#161b22', border: '1px solid #30363d' }}>
        <div className="flex items-center gap-3 px-6 py-4" style={{ borderBottom: '1px solid #30363d' }}>
          <Server size={20} style={{ color: '#8b5cf6' }} />
          <h2 className="text-lg font-semibold" style={{ color: '#e6edf3' }}>System Status</h2>
        </div>
        <div className="p-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            <div>
              <p className="text-sm mb-1" style={{ color: '#7d8590' }}>System Status</p>
              <div className="flex items-center gap-2">
                {health?.status === 'healthy' ? (
                  <Check size={16} style={{ color: '#22c55e' }} />
                ) : (
                  <AlertCircle size={16} style={{ color: '#ef4444' }} />
                )}
                <span style={{ color: health?.status === 'healthy' ? '#22c55e' : '#ef4444' }}>
                  {health?.status || 'Unknown'}
                </span>
              </div>
            </div>
            <div>
              <p className="text-sm mb-1" style={{ color: '#7d8590' }}>Version</p>
              <p className="font-mono" style={{ color: '#e6edf3' }}>{health?.version || 'N/A'}</p>
            </div>
            <div>
              <p className="text-sm mb-1" style={{ color: '#7d8590' }}>HAL Status</p>
              <div className="flex items-center gap-2">
                {health?.hal?.status === 'healthy' ? (
                  <Check size={16} style={{ color: '#22c55e' }} />
                ) : (
                  <AlertCircle size={16} style={{ color: '#f59e0b' }} />
                )}
                <span style={{ color: health?.hal?.status === 'healthy' ? '#22c55e' : '#f59e0b' }}>
                  {health?.hal?.status || 'N/A'}
                </span>
              </div>
            </div>
            <div>
              <p className="text-sm mb-1" style={{ color: '#7d8590' }}>WebSocket Clients</p>
              <p style={{ color: '#e6edf3' }}>{health?.websocket_clients || 0}</p>
            </div>
          </div>

          <div className="mt-6 pt-6" style={{ borderTop: '1px solid #30363d' }}>
            <p className="text-sm mb-3" style={{ color: '#7d8590' }}>API Versions</p>
            <div className="flex gap-3">
              {Object.entries(health?.api_versions || {}).map(([version, available]) => (
                <span
                  key={version}
                  className="px-3 py-1 rounded-full text-sm"
                  style={{
                    background: available ? 'rgba(34, 197, 94, 0.15)' : 'rgba(127, 133, 144, 0.15)',
                    color: available ? '#22c55e' : '#7d8590'
                  }}
                >
                  {version}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Ambient.ai Integration */}
      <div className="rounded-md overflow-hidden" style={{ background: '#161b22', border: '1px solid #30363d' }}>
        <div className="flex items-center justify-between px-6 py-4" style={{ borderBottom: '1px solid #30363d' }}>
          <div className="flex items-center gap-3">
            <Cloud size={20} style={{ color: '#06b6d4' }} />
            <h2 className="text-lg font-semibold" style={{ color: '#e6edf3' }}>Ambient.ai Integration</h2>
          </div>
          {health?.ambient?.enabled && (
            <button
              onClick={handleAmbientSync}
              disabled={syncing}
              className="flex items-center gap-2 px-4 py-2 rounded-md transition-colors disabled:opacity-50"
              style={{ background: 'rgba(6, 182, 212, 0.15)', color: '#06b6d4' }}
            >
              <RefreshCw size={16} className={syncing ? 'animate-spin' : ''} />
              {syncing ? 'Syncing...' : 'Full Sync'}
            </button>
          )}
        </div>
        <div className="p-6">
          {!health?.ambient?.enabled ? (
            <div className="text-center py-8">
              <Cloud size={48} className="mx-auto mb-4" style={{ color: '#7d8590' }} />
              <p style={{ color: '#7d8590' }}>Ambient.ai integration is not configured</p>
              <p className="text-sm mt-2" style={{ color: '#484f58' }}>
                Set AMBIENT_API_KEY environment variable to enable
              </p>
            </div>
          ) : (
            <div className="space-y-6">
              {/* Connection Status */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                <div>
                  <p className="text-sm mb-1" style={{ color: '#7d8590' }}>Status</p>
                  <div className="flex items-center gap-2">
                    {health.ambient.export_daemon?.running ? (
                      <>
                        <span className="w-2 h-2 rounded-full animate-pulse" style={{ background: '#22c55e' }} />
                        <span style={{ color: '#22c55e' }}>Connected</span>
                      </>
                    ) : (
                      <>
                        <span className="w-2 h-2 rounded-full" style={{ background: '#ef4444' }} />
                        <span style={{ color: '#ef4444' }}>Disconnected</span>
                      </>
                    )}
                  </div>
                </div>
                <div>
                  <p className="text-sm mb-1" style={{ color: '#7d8590' }}>Queue Size</p>
                  <p style={{ color: '#e6edf3' }}>{health.ambient.export_daemon?.queue_size || 0}</p>
                </div>
                <div>
                  <p className="text-sm mb-1" style={{ color: '#7d8590' }}>Events Sent</p>
                  <p style={{ color: '#22c55e' }}>{health.ambient.export_daemon?.events_sent || 0}</p>
                </div>
                <div>
                  <p className="text-sm mb-1" style={{ color: '#7d8590' }}>Events Failed</p>
                  <p style={{ color: health.ambient.export_daemon?.events_failed ? '#ef4444' : '#7d8590' }}>
                    {health.ambient.export_daemon?.events_failed || 0}
                  </p>
                </div>
              </div>

              {/* Sync Status */}
              <div className="pt-6" style={{ borderTop: '1px solid #30363d' }}>
                <p className="text-sm mb-3" style={{ color: '#7d8590' }}>Entity Sync</p>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                  <div>
                    <p className="text-xs mb-1" style={{ color: '#484f58' }}>Devices Synced</p>
                    <p className="text-lg" style={{ color: '#e6edf3' }}>{health.ambient.sync?.devices_synced || 0}</p>
                  </div>
                  <div>
                    <p className="text-xs mb-1" style={{ color: '#484f58' }}>Persons Synced</p>
                    <p className="text-lg" style={{ color: '#e6edf3' }}>{health.ambient.sync?.persons_synced || 0}</p>
                  </div>
                  <div>
                    <p className="text-xs mb-1" style={{ color: '#484f58' }}>Last Full Sync</p>
                    <p className="text-sm" style={{ color: '#e6edf3' }}>
                      {health.ambient.sync?.last_full_sync
                        ? new Date(health.ambient.sync.last_full_sync).toLocaleString()
                        : 'Never'}
                    </p>
                  </div>
                </div>
              </div>

              {/* Source System UID */}
              {health.ambient.source_system_uid && (
                <div className="pt-6" style={{ borderTop: '1px solid #30363d' }}>
                  <p className="text-sm mb-1" style={{ color: '#7d8590' }}>Source System UID</p>
                  <p className="font-mono text-sm break-all" style={{ color: '#e6edf3' }}>
                    {health.ambient.source_system_uid}
                  </p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Configuration */}
      <div className="rounded-md overflow-hidden" style={{ background: '#161b22', border: '1px solid #30363d' }}>
        <div className="flex items-center gap-3 px-6 py-4" style={{ borderBottom: '1px solid #30363d' }}>
          <SettingsIcon size={20} style={{ color: '#8b5cf6' }} />
          <h2 className="text-lg font-semibold" style={{ color: '#e6edf3' }}>Configuration</h2>
        </div>
        <div className="p-6">
          <div className="space-y-4">
            <div className="flex items-center justify-between py-3" style={{ borderBottom: '1px solid #21262d' }}>
              <div>
                <p style={{ color: '#e6edf3' }}>API Base URL</p>
                <p className="text-sm" style={{ color: '#7d8590' }}>Bifrost API endpoint</p>
              </div>
              <p className="font-mono text-sm" style={{ color: '#7d8590' }}>
                {window.location.origin}
              </p>
            </div>
            <div className="flex items-center justify-between py-3" style={{ borderBottom: '1px solid #21262d' }}>
              <div>
                <p style={{ color: '#e6edf3' }}>WebSocket URL</p>
                <p className="text-sm" style={{ color: '#7d8590' }}>Real-time events</p>
              </div>
              <p className="font-mono text-sm" style={{ color: '#7d8590' }}>
                ws://{window.location.host}/ws/live
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
