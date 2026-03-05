/**
 * Chronicle - Audit Trail powered by Aether Skald
 * "The Skald remembers all."
 */

import { useEffect, useState } from 'react';
import { BookOpen, Shield, CheckCircle, AlertTriangle, Download, RefreshCw, Search, Hash, Clock } from 'lucide-react';
import { skaldApi } from '../api/bifrost';

interface ChronicleEvent {
  id: number;
  event_id: string;
  timestamp: string;
  event_type: string;
  source: string;
  actor_id?: string;
  actor_name?: string;
  target_id?: string;
  target_name?: string;
  action: string;
  result?: string;
  details?: string;
  hash: string;
  prev_hash?: string;
}

interface ChronicleStats {
  total_events: number;
  first_event?: string;
  last_event?: string;
  event_types: number;
  unique_actors: number;
  unique_targets: number;
  type_breakdown: Array<{ event_type: string; count: number }>;
}

interface IntegrityResult {
  verified: number;
  errors: number;
  integrity: 'VALID' | 'CORRUPTED';
  error_details: Array<{ event_id: string; error: string }>;
}

// DEMO MODE
const DEMO_MODE = true;
const MOCK_CHRONICLE: ChronicleEvent[] = [
  { id: 1, event_id: 'EVT-20260304120000001', timestamp: new Date(Date.now() - 60000).toISOString(), event_type: 'access', source: 'bifrost', actor_id: 'A1B2C3D4', actor_name: 'John Smith', target_id: '1', target_name: 'Main Entrance', action: 'card_presented', result: 'granted', hash: 'abc123...', prev_hash: 'GENESIS' },
  { id: 2, event_id: 'EVT-20260304120000002', timestamp: new Date(Date.now() - 120000).toISOString(), event_type: 'access', source: 'bifrost', actor_id: 'X9Y8Z7W6', actor_name: 'Unknown', target_id: '3', target_name: 'Server Room', action: 'card_presented', result: 'denied', hash: 'def456...', prev_hash: 'abc123...' },
  { id: 3, event_id: 'EVT-20260304120000003', timestamp: new Date(Date.now() - 180000).toISOString(), event_type: 'system', source: 'thrall', actor_id: '', actor_name: 'System', target_id: '2', target_name: 'Side Entrance', action: 'door_locked', result: 'success', hash: 'ghi789...', prev_hash: 'def456...' },
  { id: 4, event_id: 'EVT-20260304120000004', timestamp: new Date(Date.now() - 240000).toISOString(), event_type: 'access', source: 'bifrost', actor_id: 'E5F6G7H8', actor_name: 'Sarah Johnson', target_id: '1', target_name: 'Main Entrance', action: 'card_presented', result: 'granted', hash: 'jkl012...', prev_hash: 'ghi789...' },
  { id: 5, event_id: 'EVT-20260304120000005', timestamp: new Date(Date.now() - 300000).toISOString(), event_type: 'alarm', source: 'thrall', actor_id: '', actor_name: '', target_id: '5', target_name: 'Emergency Exit', action: 'door_forced', result: 'alert', hash: 'mno345...', prev_hash: 'jkl012...' },
  { id: 6, event_id: 'EVT-20260304120000006', timestamp: new Date(Date.now() - 360000).toISOString(), event_type: 'admin', source: 'saga', actor_id: 'ADMIN01', actor_name: 'Admin User', target_id: '', target_name: '', action: 'cardholder_created', result: 'success', hash: 'pqr678...', prev_hash: 'mno345...' },
  { id: 7, event_id: 'EVT-20260304120000007', timestamp: new Date(Date.now() - 420000).toISOString(), event_type: 'access', source: 'bifrost', actor_id: 'I9J0K1L2', actor_name: 'Mike Rodriguez', target_id: '4', target_name: 'Parking Garage', action: 'card_presented', result: 'granted', hash: 'stu901...', prev_hash: 'pqr678...' },
  { id: 8, event_id: 'EVT-20260304120000008', timestamp: new Date(Date.now() - 480000).toISOString(), event_type: 'system', source: 'skald', actor_id: '', actor_name: 'System', target_id: '', target_name: '', action: 'export_completed', result: 'success', hash: 'vwx234...', prev_hash: 'stu901...' },
];

const MOCK_STATS: ChronicleStats = {
  total_events: 1247,
  first_event: '2026-02-01T00:00:00Z',
  last_event: new Date().toISOString(),
  event_types: 4,
  unique_actors: 156,
  unique_targets: 8,
  type_breakdown: [
    { event_type: 'access', count: 1089 },
    { event_type: 'system', count: 98 },
    { event_type: 'admin', count: 42 },
    { event_type: 'alarm', count: 18 },
  ]
};

const MOCK_INTEGRITY: IntegrityResult = {
  verified: 1247,
  errors: 0,
  integrity: 'VALID',
  error_details: []
};

function ResultBadge({ result }: { result?: string }) {
  const isGood = result === 'granted' || result === 'success';
  const isBad = result === 'denied' || result === 'alert' || result === 'failed';

  return (
    <span
      className="px-2.5 py-1 rounded text-xs font-medium"
      style={{
        background: isGood
          ? 'rgba(34, 197, 94, 0.15)'
          : isBad
          ? 'rgba(239, 68, 68, 0.15)'
          : 'rgba(245, 158, 11, 0.15)',
        color: isGood ? '#22c55e' : isBad ? '#ef4444' : '#f59e0b'
      }}
    >
      {result || 'unknown'}
    </span>
  );
}

function SourceBadge({ source }: { source: string }) {
  const colors: Record<string, string> = {
    bifrost: '#58a6ff',
    thrall: '#22c55e',
    saga: '#8b5cf6',
    skald: '#f59e0b',
  };
  const color = colors[source] || '#7d8590';

  return (
    <span
      className="px-2 py-0.5 rounded text-xs font-medium"
      style={{ background: `${color}20`, color }}
    >
      {source}
    </span>
  );
}

export function Chronicle() {
  const [events, setEvents] = useState<ChronicleEvent[]>([]);
  const [stats, setStats] = useState<ChronicleStats | null>(null);
  const [integrity, setIntegrity] = useState<IntegrityResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [verifying, setVerifying] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState<string>('all');

  const fetchData = async () => {
    if (DEMO_MODE) {
      setEvents(MOCK_CHRONICLE);
      setStats(MOCK_STATS);
      setIntegrity(MOCK_INTEGRITY);
      setLoading(false);
      return;
    }
    try {
      setLoading(true);
      const [eventsData, statusData] = await Promise.all([
        skaldApi.getChronicle(),
        skaldApi.getStatus(),
      ]);
      setEvents(eventsData.events || []);
      setStats(statusData.statistics || null);
      setError(null);
    } catch (err) {
      setError('Failed to connect to Skald Chronicle');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const verifyIntegrity = async () => {
    if (DEMO_MODE) {
      setVerifying(true);
      setTimeout(() => {
        setIntegrity(MOCK_INTEGRITY);
        setVerifying(false);
      }, 1500);
      return;
    }
    try {
      setVerifying(true);
      const result = await skaldApi.verifyIntegrity();
      setIntegrity(result);
    } catch (err) {
      console.error('Integrity verification failed:', err);
    } finally {
      setVerifying(false);
    }
  };

  const exportChronicle = async (format: 'json' | 'csv' | 'siem') => {
    if (DEMO_MODE) {
      setExporting(true);
      setTimeout(() => {
        alert(`Export to ${format.toUpperCase()} initiated (Demo Mode)`);
        setExporting(false);
      }, 1000);
      return;
    }
    try {
      setExporting(true);
      const result = await skaldApi.createExport(format);
      alert(`Export job created: ${result.job_id}`);
    } catch (err) {
      console.error('Export failed:', err);
    } finally {
      setExporting(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const filteredEvents = events.filter((event) => {
    if (filter !== 'all' && event.event_type !== filter) return false;

    if (search) {
      const searchLower = search.toLowerCase();
      const matchesId = event.event_id.toLowerCase().includes(searchLower);
      const matchesActor = event.actor_name?.toLowerCase().includes(searchLower);
      const matchesTarget = event.target_name?.toLowerCase().includes(searchLower);
      const matchesAction = event.action.toLowerCase().includes(searchLower);
      return matchesId || matchesActor || matchesTarget || matchesAction;
    }

    return true;
  });

  if (loading && events.length === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-2 border-t-transparent" style={{ borderColor: '#f59e0b', borderTopColor: 'transparent' }} />
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
              style={{ background: '#f59e0b' }}
            />
            <h1 className="text-xl font-semibold" style={{ color: '#e6edf3' }}>
              Chronicle
            </h1>
            <span className="text-xs px-2 py-0.5 rounded" style={{ background: 'rgba(245, 158, 11, 0.15)', color: '#f59e0b' }}>
              Skald
            </span>
          </div>
          <p className="text-sm" style={{ color: '#7d8590' }}>
            Immutable audit trail with integrity verification
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={verifyIntegrity}
            disabled={verifying}
            className="flex items-center gap-2 px-4 py-2 rounded-md transition-colors"
            style={{ background: '#21262d', border: '1px solid #30363d', color: '#7d8590' }}
          >
            <Shield size={16} className={verifying ? 'animate-pulse' : ''} />
            {verifying ? 'Verifying...' : 'Verify Integrity'}
          </button>
          <button
            onClick={fetchData}
            className="flex items-center gap-2 px-4 py-2 rounded-md transition-colors"
            style={{ background: '#21262d', border: '1px solid #30363d', color: '#7d8590' }}
          >
            <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
            Refresh
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-5 gap-4">
        <div className="p-4 rounded-md" style={{ background: '#161b22', border: '1px solid #30363d' }}>
          <div className="flex items-center gap-2 mb-2">
            <BookOpen size={16} style={{ color: '#f59e0b' }} />
            <p className="text-xs" style={{ color: '#7d8590' }}>Total Records</p>
          </div>
          <p className="text-2xl font-semibold" style={{ color: '#e6edf3' }}>{stats?.total_events.toLocaleString() || '0'}</p>
        </div>

        <div className="p-4 rounded-md" style={{ background: '#161b22', border: '1px solid #30363d' }}>
          <div className="flex items-center gap-2 mb-2">
            <Hash size={16} style={{ color: '#8b5cf6' }} />
            <p className="text-xs" style={{ color: '#7d8590' }}>Event Types</p>
          </div>
          <p className="text-2xl font-semibold" style={{ color: '#8b5cf6' }}>{stats?.event_types || '0'}</p>
        </div>

        <div className="p-4 rounded-md" style={{ background: '#161b22', border: '1px solid #30363d' }}>
          <div className="flex items-center gap-2 mb-2">
            <span className="w-4 h-4 rounded-full flex items-center justify-center text-xs" style={{ background: 'rgba(88, 166, 255, 0.15)', color: '#58a6ff' }}>U</span>
            <p className="text-xs" style={{ color: '#7d8590' }}>Unique Actors</p>
          </div>
          <p className="text-2xl font-semibold" style={{ color: '#58a6ff' }}>{stats?.unique_actors || '0'}</p>
        </div>

        <div className="p-4 rounded-md" style={{ background: '#161b22', border: '1px solid #30363d' }}>
          <div className="flex items-center gap-2 mb-2">
            <Clock size={16} style={{ color: '#22c55e' }} />
            <p className="text-xs" style={{ color: '#7d8590' }}>Unique Targets</p>
          </div>
          <p className="text-2xl font-semibold" style={{ color: '#22c55e' }}>{stats?.unique_targets || '0'}</p>
        </div>

        <div className="p-4 rounded-md" style={{
          background: integrity?.integrity === 'VALID' ? 'rgba(34, 197, 94, 0.1)' : 'rgba(239, 68, 68, 0.1)',
          border: `1px solid ${integrity?.integrity === 'VALID' ? 'rgba(34, 197, 94, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`
        }}>
          <div className="flex items-center gap-2 mb-2">
            {integrity?.integrity === 'VALID' ? (
              <CheckCircle size={16} style={{ color: '#22c55e' }} />
            ) : (
              <AlertTriangle size={16} style={{ color: '#ef4444' }} />
            )}
            <p className="text-xs" style={{ color: '#7d8590' }}>Chain Integrity</p>
          </div>
          <p className="text-2xl font-semibold" style={{ color: integrity?.integrity === 'VALID' ? '#22c55e' : '#ef4444' }}>
            {integrity?.integrity || 'UNKNOWN'}
          </p>
        </div>
      </div>

      {/* Search & Filters & Export */}
      <div className="flex items-center gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2" size={18} style={{ color: '#7d8590' }} />
          <input
            type="text"
            placeholder="Search chronicle..."
            className="w-full rounded-md pl-11 pr-4 py-2.5 focus:outline-none"
            style={{ background: '#0d1117', border: '1px solid #30363d', color: '#e6edf3' }}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <div className="flex rounded-md p-1" style={{ background: '#21262d' }}>
          <button
            onClick={() => setFilter('all')}
            className="px-3 py-1.5 rounded text-sm font-medium transition-colors"
            style={{
              background: filter === 'all' ? '#30363d' : 'transparent',
              color: filter === 'all' ? '#e6edf3' : '#7d8590'
            }}
          >
            All
          </button>
          <button
            onClick={() => setFilter('access')}
            className="px-3 py-1.5 rounded text-sm font-medium transition-colors"
            style={{
              background: filter === 'access' ? 'rgba(34, 197, 94, 0.15)' : 'transparent',
              color: filter === 'access' ? '#22c55e' : '#7d8590'
            }}
          >
            Access
          </button>
          <button
            onClick={() => setFilter('admin')}
            className="px-3 py-1.5 rounded text-sm font-medium transition-colors"
            style={{
              background: filter === 'admin' ? 'rgba(139, 92, 246, 0.15)' : 'transparent',
              color: filter === 'admin' ? '#8b5cf6' : '#7d8590'
            }}
          >
            Admin
          </button>
          <button
            onClick={() => setFilter('alarm')}
            className="px-3 py-1.5 rounded text-sm font-medium transition-colors"
            style={{
              background: filter === 'alarm' ? 'rgba(239, 68, 68, 0.15)' : 'transparent',
              color: filter === 'alarm' ? '#ef4444' : '#7d8590'
            }}
          >
            Alarm
          </button>
        </div>

        {/* Export Dropdown */}
        <div className="relative group">
          <button
            disabled={exporting}
            className="flex items-center gap-2 px-4 py-2.5 rounded-md transition-colors"
            style={{ background: 'rgba(245, 158, 11, 0.15)', border: '1px solid rgba(245, 158, 11, 0.3)', color: '#f59e0b' }}
          >
            <Download size={16} />
            {exporting ? 'Exporting...' : 'Export'}
          </button>
          <div
            className="absolute right-0 mt-2 w-40 rounded-md shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-10"
            style={{ background: '#161b22', border: '1px solid #30363d' }}
          >
            <button
              onClick={() => exportChronicle('json')}
              className="w-full px-4 py-2 text-left text-sm hover:bg-[#21262d] transition-colors"
              style={{ color: '#e6edf3' }}
            >
              Export JSON
            </button>
            <button
              onClick={() => exportChronicle('csv')}
              className="w-full px-4 py-2 text-left text-sm hover:bg-[#21262d] transition-colors"
              style={{ color: '#e6edf3' }}
            >
              Export CSV
            </button>
            <button
              onClick={() => exportChronicle('siem')}
              className="w-full px-4 py-2 text-left text-sm hover:bg-[#21262d] transition-colors"
              style={{ color: '#e6edf3' }}
            >
              Export SIEM (CEF)
            </button>
          </div>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-md" style={{ background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)' }}>
          <p style={{ color: '#ef4444' }}>{error}</p>
        </div>
      )}

      {/* Chronicle Table */}
      <div className="rounded-md overflow-hidden" style={{ background: '#161b22', border: '1px solid #30363d' }}>
        <table className="w-full">
          <thead>
            <tr style={{ borderBottom: '1px solid #30363d', background: '#0d1117' }}>
              <th className="text-left py-3 px-4 text-sm font-medium" style={{ color: '#7d8590' }}>EVENT ID</th>
              <th className="text-left py-3 px-4 text-sm font-medium" style={{ color: '#7d8590' }}>SOURCE</th>
              <th className="text-left py-3 px-4 text-sm font-medium" style={{ color: '#7d8590' }}>ACTOR</th>
              <th className="text-left py-3 px-4 text-sm font-medium" style={{ color: '#7d8590' }}>ACTION</th>
              <th className="text-left py-3 px-4 text-sm font-medium" style={{ color: '#7d8590' }}>TARGET</th>
              <th className="text-left py-3 px-4 text-sm font-medium" style={{ color: '#7d8590' }}>RESULT</th>
              <th className="text-left py-3 px-4 text-sm font-medium" style={{ color: '#7d8590' }}>TIMESTAMP</th>
              <th className="text-left py-3 px-4 text-sm font-medium" style={{ color: '#7d8590' }}>HASH</th>
            </tr>
          </thead>
          <tbody>
            {filteredEvents.length === 0 ? (
              <tr>
                <td colSpan={8} className="py-12 text-center" style={{ color: '#7d8590' }}>
                  No chronicle entries found
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
                    <span className="font-mono text-xs" style={{ color: '#f59e0b' }}>{event.event_id.slice(0, 18)}...</span>
                  </td>
                  <td className="py-3 px-4">
                    <SourceBadge source={event.source} />
                  </td>
                  <td className="py-3 px-4 text-sm" style={{ color: '#e6edf3' }}>
                    {event.actor_name || event.actor_id || '-'}
                  </td>
                  <td className="py-3 px-4 text-sm" style={{ color: '#7d8590' }}>
                    {event.action}
                  </td>
                  <td className="py-3 px-4 text-sm" style={{ color: '#7d8590' }}>
                    {event.target_name || event.target_id || '-'}
                  </td>
                  <td className="py-3 px-4">
                    <ResultBadge result={event.result} />
                  </td>
                  <td className="py-3 px-4 text-sm whitespace-nowrap" style={{ color: '#7d8590' }}>
                    {new Date(event.timestamp).toLocaleString()}
                  </td>
                  <td className="py-3 px-4">
                    <span className="font-mono text-xs px-2 py-1 rounded" style={{ background: '#21262d', color: '#7d8590' }}>
                      {event.hash.slice(0, 8)}...
                    </span>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Footer Info */}
      <div className="flex items-center justify-between text-sm" style={{ color: '#484f58' }}>
        <p>Showing {filteredEvents.length} of {events.length} entries</p>
        <p className="flex items-center gap-2">
          <span style={{ color: '#f59e0b' }}>ᛋ</span>
          "The Skald remembers all."
        </p>
      </div>
    </div>
  );
}
