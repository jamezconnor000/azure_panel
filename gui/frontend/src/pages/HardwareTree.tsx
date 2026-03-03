import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  ChevronRight,
  ChevronDown,
  Server,
  Cpu,
  DoorOpen,
  ArrowRight,
  ArrowLeft,
  ToggleLeft,
  Activity,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Plus,
  Settings
} from 'lucide-react';
import apiClientV2_1 from '../api/clientV2_1';

interface PanelReader {
  reader_id: number;
  panel_id: number;
  reader_address: number;
  reader_name: string | null;
  status: string;
  osdp_enabled: boolean;
  last_seen: number;
}

interface PanelIO {
  input_id?: number;
  output_id?: number;
  relay_id?: number;
  panel_id: number;
  number: number;
  name: string | null;
  state: string;
  last_state_change: number;
}

interface PanelNode {
  panel_id: number;
  panel_name: string;
  panel_type: string;
  parent_panel_id: number | null;
  rs485_address: number | null;
  status: string;
  firmware_version: string | null;
  last_seen: number;
  readers: PanelReader[];
  inputs: PanelIO[];
  outputs: PanelIO[];
  relays: PanelIO[];
  children?: PanelNode[];
}

export default function HardwareTree() {
  const [expandedPanels, setExpandedPanels] = useState<Set<number>>(new Set());
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({});

  const { data: hardwareTree, isLoading, error, refetch } = useQuery({
    queryKey: ['hardwareTree'],
    queryFn: async () => {
      const response = await fetch('/api/v2.1/hardware-tree', {
        headers: {
          'Authorization': `Bearer ${apiClientV2_1.getCurrentUser()?.token || ''}`
        }
      });
      if (!response.ok) throw new Error('Failed to fetch hardware tree');
      return response.json() as Promise<PanelNode[]>;
    },
    refetchInterval: 5000, // Refresh every 5 seconds for live status
  });

  useEffect(() => {
    // Auto-expand all panels on first load
    if (hardwareTree && expandedPanels.size === 0) {
      const allPanelIds = new Set<number>();
      hardwareTree.forEach(panel => {
        allPanelIds.add(panel.panel_id);
        panel.children?.forEach(child => allPanelIds.add(child.panel_id));
      });
      setExpandedPanels(allPanelIds);
    }
  }, [hardwareTree]);

  const togglePanel = (panelId: number) => {
    setExpandedPanels(prev => {
      const newSet = new Set(prev);
      if (newSet.has(panelId)) {
        newSet.delete(panelId);
      } else {
        newSet.add(panelId);
      }
      return newSet;
    });
  };

  const toggleSection = (key: string) => {
    setExpandedSections(prev => ({
      ...prev,
      [key]: !prev[key]
    }));
  };

  const getStatusIcon = (status: string) => {
    switch (status.toUpperCase()) {
      case 'ONLINE':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'OFFLINE':
        return <XCircle className="h-4 w-4 text-gray-500" />;
      case 'FAULT':
      case 'TAMPER':
        return <AlertTriangle className="h-4 w-4 text-red-500" />;
      default:
        return <Activity className="h-4 w-4 text-gray-400" />;
    }
  };

  const getStatusBadge = (status: string) => {
    const baseClasses = "px-2 py-0.5 rounded text-xs font-medium";
    switch (status.toUpperCase()) {
      case 'ONLINE':
        return `${baseClasses} bg-green-900/50 text-green-400 border border-green-500`;
      case 'OFFLINE':
        return `${baseClasses} bg-gray-700 text-gray-400 border border-gray-600`;
      case 'FAULT':
      case 'TAMPER':
        return `${baseClasses} bg-red-900/50 text-red-400 border border-red-500`;
      case 'ACTIVE':
        return `${baseClasses} bg-blue-900/50 text-blue-400 border border-blue-500`;
      case 'INACTIVE':
        return `${baseClasses} bg-gray-700 text-gray-400 border border-gray-600`;
      default:
        return `${baseClasses} bg-gray-700 text-gray-400 border border-gray-600`;
    }
  };

  const renderIO = (items: PanelIO[], type: 'input' | 'output' | 'relay', panelId: number, Icon: any) => {
    if (items.length === 0) return null;

    const sectionKey = `${panelId}-${type}`;
    const isExpanded = expandedSections[sectionKey] ?? true;

    return (
      <div className="ml-8 mt-2">
        <button
          onClick={() => toggleSection(sectionKey)}
          className="flex items-center space-x-2 text-gray-300 hover:text-white transition py-1"
        >
          {isExpanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
          <Icon className="h-4 w-4 text-purple-400" />
          <span className="text-sm font-medium capitalize">{type}s ({items.length})</span>
        </button>

        {isExpanded && (
          <div className="ml-6 mt-1 space-y-1">
            {items.map((item, idx) => (
              <div
                key={idx}
                className="flex items-center justify-between py-1.5 px-3 rounded bg-slate-800 border border-slate-700"
              >
                <div className="flex items-center space-x-2">
                  <Icon className="h-3.5 w-3.5 text-purple-400" />
                  <span className="text-sm text-gray-300">
                    {item.name || `${type.charAt(0).toUpperCase() + type.slice(1)} ${item.number}`}
                  </span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className={getStatusBadge(item.state)}>
                    {item.state}
                  </span>
                  {getStatusIcon(item.state)}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  };

  const renderReaders = (readers: PanelReader[], panelId: number) => {
    if (readers.length === 0) return null;

    const sectionKey = `${panelId}-readers`;
    const isExpanded = expandedSections[sectionKey] ?? true;

    return (
      <div className="ml-8 mt-2">
        <button
          onClick={() => toggleSection(sectionKey)}
          className="flex items-center space-x-2 text-gray-300 hover:text-white transition py-1"
        >
          {isExpanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
          <Cpu className="h-4 w-4 text-blue-400" />
          <span className="text-sm font-medium">Readers ({readers.length})</span>
        </button>

        {isExpanded && (
          <div className="ml-6 mt-1 space-y-1">
            {readers.map((reader) => (
              <div
                key={reader.reader_id}
                className="flex items-center justify-between py-1.5 px-3 rounded bg-slate-800 border border-slate-700"
              >
                <div className="flex items-center space-x-2">
                  <Cpu className="h-3.5 w-3.5 text-blue-400" />
                  <span className="text-sm text-gray-300">
                    {reader.reader_name || `Reader ${reader.reader_address}`}
                  </span>
                  {reader.osdp_enabled && (
                    <span className="px-1.5 py-0.5 rounded text-xs bg-blue-900/50 text-blue-300 border border-blue-600">
                      OSDP
                    </span>
                  )}
                </div>
                <div className="flex items-center space-x-2">
                  <span className={getStatusBadge(reader.status)}>
                    {reader.status}
                  </span>
                  {getStatusIcon(reader.status)}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  };

  const renderPanel = (panel: PanelNode, isDownstream: boolean = false) => {
    const isExpanded = expandedPanels.has(panel.panel_id);
    const hasChildren = panel.children && panel.children.length > 0;
    const hasDevices = panel.readers.length > 0 || panel.inputs.length > 0 ||
                      panel.outputs.length > 0 || panel.relays.length > 0;

    return (
      <div key={panel.panel_id} className={isDownstream ? 'ml-8' : ''}>
        <div className="mb-2">
          <button
            onClick={() => togglePanel(panel.panel_id)}
            className={`
              w-full flex items-center justify-between p-3 rounded-lg border transition-all
              ${isDownstream
                ? 'bg-slate-800 border-slate-600 hover:border-slate-500'
                : 'bg-slate-700 border-slate-600 hover:border-slate-500'
              }
            `}
          >
            <div className="flex items-center space-x-3">
              {(hasChildren || hasDevices) && (
                isExpanded ? <ChevronDown className="h-5 w-5" /> : <ChevronRight className="h-5 w-5" />
              )}
              <Server className={`h-5 w-5 ${isDownstream ? 'text-orange-400' : 'text-cyan-400'}`} />
              <div className="flex items-center space-x-2">
                <span className="text-white font-medium">{panel.panel_name}</span>
                <span className="text-xs text-gray-400">#{panel.panel_id}</span>
                {isDownstream && panel.rs485_address !== null && (
                  <span className="px-2 py-0.5 rounded text-xs bg-orange-900/50 text-orange-300 border border-orange-600">
                    RS-485: {panel.rs485_address}
                  </span>
                )}
              </div>
            </div>

            <div className="flex items-center space-x-3">
              {panel.firmware_version && (
                <span className="text-xs text-gray-400">{panel.firmware_version}</span>
              )}
              <span className={getStatusBadge(panel.status)}>
                {panel.status}
              </span>
              {getStatusIcon(panel.status)}
            </div>
          </button>

          {isExpanded && (
            <div className="mt-2">
              {/* Readers */}
              {renderReaders(panel.readers, panel.panel_id)}

              {/* Inputs */}
              {renderIO(panel.inputs, 'input', panel.panel_id, ArrowRight)}

              {/* Outputs */}
              {renderIO(panel.outputs, 'output', panel.panel_id, ArrowLeft)}

              {/* Relays */}
              {renderIO(panel.relays, 'relay', panel.panel_id, ToggleLeft)}

              {/* Downstream Panels */}
              {hasChildren && (
                <div className="mt-3">
                  <div className="ml-8 mb-2 flex items-center space-x-2 text-gray-400">
                    <DoorOpen className="h-4 w-4" />
                    <span className="text-sm font-medium">Downstream Panels ({panel.children?.length})</span>
                  </div>
                  {panel.children?.map(child => renderPanel(child, true))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    );
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Activity className="h-8 w-8 text-blue-500 animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-900/20 border border-red-500 rounded-lg p-4">
        <div className="flex items-center space-x-2">
          <AlertTriangle className="h-5 w-5 text-red-500" />
          <p className="text-red-400">Failed to load hardware tree</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Hardware Tree</h1>
          <p className="text-gray-400 mt-1">Live status of all panels, readers, and I/O devices</p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={() => refetch()}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition flex items-center space-x-2"
          >
            <Activity className="h-4 w-4" />
            <span>Refresh</span>
          </button>
          <button
            className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition flex items-center space-x-2"
          >
            <Plus className="h-4 w-4" />
            <span>Add Panel</span>
          </button>
        </div>
      </div>

      {/* Legend */}
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
        <div className="flex items-center space-x-6 text-sm">
          <span className="text-gray-400 font-medium">Status:</span>
          <div className="flex items-center space-x-2">
            <CheckCircle className="h-4 w-4 text-green-500" />
            <span className="text-gray-300">Online</span>
          </div>
          <div className="flex items-center space-x-2">
            <XCircle className="h-4 w-4 text-gray-500" />
            <span className="text-gray-300">Offline</span>
          </div>
          <div className="flex items-center space-x-2">
            <AlertTriangle className="h-4 w-4 text-red-500" />
            <span className="text-gray-300">Fault/Tamper</span>
          </div>
          <div className="ml-auto flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <Server className="h-4 w-4 text-cyan-400" />
              <span className="text-gray-300">Master Panel</span>
            </div>
            <div className="flex items-center space-x-2">
              <Server className="h-4 w-4 text-orange-400" />
              <span className="text-gray-300">Downstream Panel</span>
            </div>
          </div>
        </div>
      </div>

      {/* Hardware Tree */}
      <div className="space-y-3">
        {hardwareTree && hardwareTree.length > 0 ? (
          hardwareTree.map(panel => renderPanel(panel))
        ) : (
          <div className="bg-slate-800 border border-slate-700 rounded-lg p-8 text-center">
            <Server className="h-12 w-12 text-gray-600 mx-auto mb-3" />
            <p className="text-gray-400">No panels configured</p>
            <button className="mt-4 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition">
              Add First Panel
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
