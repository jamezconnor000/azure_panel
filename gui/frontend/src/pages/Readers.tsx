import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../api/client';
import { Cpu, Wifi, Shield, Thermometer, Battery, AlertTriangle } from 'lucide-react';
import type { ReaderHealth } from '../types';

export default function Readers() {
  // For now, hardcode reader IDs (in production, fetch from API)
  const readerIds = [1, 2, 3];

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-bold text-white">Readers</h1>
        <p className="text-slate-400 mt-2">
          Monitor OSDP reader health and secure channel status
        </p>
      </div>

      {/* Reader Cards */}
      <div className="space-y-6">
        {readerIds.map((readerId) => (
          <ReaderCard key={readerId} readerId={readerId} />
        ))}
      </div>
    </div>
  );
}

function ReaderCard({ readerId }: { readerId: number }) {
  const { data: reader, isLoading } = useQuery({
    queryKey: ['reader', readerId, 'health'],
    queryFn: () => apiClient.getReaderHealth(readerId),
    refetchInterval: 5000,
  });

  if (isLoading) {
    return (
      <div className="card">
        <div className="card-body">
          <div className="text-slate-400">Loading reader {readerId}...</div>
        </div>
      </div>
    );
  }

  if (!reader) return null;

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

  const getHealthBg = (health: string) => {
    switch (health) {
      case 'excellent':
        return 'bg-green-500/10 border-green-500';
      case 'good':
        return 'bg-lime-500/10 border-lime-500';
      case 'fair':
        return 'bg-yellow-500/10 border-yellow-500';
      case 'poor':
        return 'bg-orange-500/10 border-orange-500';
      case 'critical':
        return 'bg-red-500/10 border-red-500';
      default:
        return 'bg-slate-500/10 border-slate-500';
    }
  };

  return (
    <div className="card">
      {/* Header */}
      <div className="card-header">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Cpu className={`h-6 w-6 ${getHealthColor(reader.overall_health)}`} />
            <div>
              <h2 className="text-xl font-semibold text-white">{reader.reader_name}</h2>
              <p className="text-sm text-slate-400">Health Score: {reader.health_score}/100</p>
            </div>
          </div>

          <div className={`px-4 py-2 rounded-lg border ${getHealthBg(reader.overall_health)}`}>
            <span className={`font-medium ${getHealthColor(reader.overall_health)}`}>
              {reader.overall_health.toUpperCase()}
            </span>
          </div>
        </div>
      </div>

      <div className="card-body">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {/* Communication Health */}
          <div>
            <div className="flex items-center space-x-2 mb-3">
              <Wifi className="h-5 w-5 text-primary-400" />
              <h3 className="text-sm font-medium text-slate-300">Communication</h3>
            </div>
            <div className="space-y-2">
              <div>
                <p className="text-xs text-slate-500">Health</p>
                <p className={`text-sm font-medium ${getHealthColor(reader.comm_health)}`}>
                  {reader.comm_health}
                </p>
              </div>
              <div>
                <p className="text-xs text-slate-500">Uptime</p>
                <p className="text-sm text-white">{reader.comm_uptime_percent.toFixed(1)}%</p>
              </div>
              <div>
                <p className="text-xs text-slate-500">Response Time</p>
                <p className="text-sm text-white">{reader.avg_response_time_ms.toFixed(1)}ms</p>
              </div>
              <div>
                <p className="text-xs text-slate-500">Failed Polls (1h)</p>
                <p className="text-sm text-white">{reader.failed_polls_last_hour}</p>
              </div>
            </div>
          </div>

          {/* Secure Channel Health */}
          <div>
            <div className="flex items-center space-x-2 mb-3">
              <Shield className="h-5 w-5 text-primary-400" />
              <h3 className="text-sm font-medium text-slate-300">Secure Channel</h3>
            </div>
            <div className="space-y-2">
              <div>
                <p className="text-xs text-slate-500">Health</p>
                <p className={`text-sm font-medium ${getHealthColor(reader.sc_health)}`}>
                  {reader.sc_health}
                </p>
              </div>
              <div>
                <p className="text-xs text-slate-500">Handshake Success</p>
                <p className="text-sm text-white">{reader.sc_handshake_success_rate.toFixed(1)}%</p>
              </div>
              <div>
                <p className="text-xs text-slate-500">MAC Failures</p>
                <p className={`text-sm ${reader.sc_mac_failure_rate > 0 ? 'text-red-500' : 'text-white'}`}>
                  {reader.sc_mac_failure_rate.toFixed(1)}%
                </p>
              </div>
              <div>
                <p className="text-xs text-slate-500">Avg Handshake Time</p>
                <p className="text-sm text-white">{reader.sc_avg_handshake_time_ms.toFixed(0)}ms</p>
              </div>
            </div>
          </div>

          {/* Hardware Health */}
          <div>
            <div className="flex items-center space-x-2 mb-3">
              <Battery className="h-5 w-5 text-primary-400" />
              <h3 className="text-sm font-medium text-slate-300">Hardware</h3>
            </div>
            <div className="space-y-2">
              <div>
                <p className="text-xs text-slate-500">Health</p>
                <p className={`text-sm font-medium ${getHealthColor(reader.hardware_health)}`}>
                  {reader.hardware_health}
                </p>
              </div>
              <div>
                <p className="text-xs text-slate-500">Tamper Status</p>
                <p className={`text-sm ${reader.tamper_status === 'OK' ? 'text-white' : 'text-red-500'}`}>
                  {reader.tamper_status}
                </p>
              </div>
              <div>
                <p className="text-xs text-slate-500">Power</p>
                <p className="text-sm text-white">
                  {reader.power_voltage?.toFixed(1)}V ({reader.power_status})
                </p>
              </div>
              <div>
                <p className="text-xs text-slate-500">Temperature</p>
                <p className="text-sm text-white">{reader.temperature_celsius?.toFixed(1)}°C</p>
              </div>
            </div>
          </div>

          {/* Card Reader Health */}
          <div>
            <div className="flex items-center space-x-2 mb-3">
              <Cpu className="h-5 w-5 text-primary-400" />
              <h3 className="text-sm font-medium text-slate-300">Card Reader</h3>
            </div>
            <div className="space-y-2">
              <div>
                <p className="text-xs text-slate-500">Health</p>
                <p className={`text-sm font-medium ${getHealthColor(reader.card_reader_health)}`}>
                  {reader.card_reader_health}
                </p>
              </div>
              <div>
                <p className="text-xs text-slate-500">Reads Today</p>
                <p className="text-sm text-white">{reader.successful_reads_today}</p>
              </div>
              <div>
                <p className="text-xs text-slate-500">Success Rate</p>
                <p className="text-sm text-white">{reader.read_success_rate.toFixed(1)}%</p>
              </div>
              <div>
                <p className="text-xs text-slate-500">Avg Read Time</p>
                <p className="text-sm text-white">{reader.avg_read_time_ms.toFixed(0)}ms</p>
              </div>
            </div>
          </div>
        </div>

        {/* Warnings and Recommendations */}
        {(reader.warnings.length > 0 || reader.recommendations.length > 0) && (
          <div className="mt-6 space-y-4">
            {reader.warnings.length > 0 && (
              <div className="p-4 bg-yellow-900/20 border border-yellow-500 rounded-lg">
                <div className="flex items-center space-x-2 mb-2">
                  <AlertTriangle className="h-5 w-5 text-yellow-500" />
                  <h3 className="text-sm font-medium text-yellow-400">Warnings</h3>
                </div>
                <ul className="space-y-1">
                  {reader.warnings.map((warning, index) => (
                    <li key={index} className="text-yellow-300 text-sm">
                      • {warning}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {reader.recommendations.length > 0 && (
              <div className="p-4 bg-blue-900/20 border border-blue-500 rounded-lg">
                <h3 className="text-sm font-medium text-blue-400 mb-2">Recommendations</h3>
                <ul className="space-y-1">
                  {reader.recommendations.map((rec, index) => (
                    <li key={index} className="text-blue-300 text-sm">
                      • {rec}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {/* Firmware Info */}
        <div className="mt-6 pt-6 border-t border-slate-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-400">Firmware Version</p>
              <p className="text-white">{reader.firmware_version}</p>
            </div>
            <div>
              {reader.firmware_up_to_date ? (
                <span className="badge badge-success">Up to date</span>
              ) : (
                <span className="badge badge-warning">
                  {reader.pending_updates} update(s) available
                </span>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
