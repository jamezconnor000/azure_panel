import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import { apiClient } from '../api/client';
import { DoorOpen, Power, Zap, Lock, Unlock, AlertTriangle, PlayCircle } from 'lucide-react';
import type { PanelIOStatus, Macro } from '../types';

export default function IOControl() {
  const queryClient = useQueryClient();
  const [selectedPanel] = useState(1);

  // Fetch panel I/O status
  const { data: ioStatus, isLoading: ioLoading } = useQuery({
    queryKey: ['panel', selectedPanel, 'io'],
    queryFn: () => apiClient.getPanelIO(selectedPanel),
    refetchInterval: 3000,
  });

  // Fetch available macros
  const { data: macrosData } = useQuery({
    queryKey: ['macros'],
    queryFn: () => apiClient.listMacros(),
  });

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-bold text-white">I/O Control</h1>
        <p className="text-slate-400 mt-2">
          Monitor and control doors, outputs, and relays
        </p>
      </div>

      {ioLoading ? (
        <div className="text-slate-400">Loading I/O status...</div>
      ) : (
        <>
          {/* Doors */}
          <div className="card">
            <div className="card-header">
              <h2 className="text-xl font-semibold text-white">Doors</h2>
            </div>
            <div className="card-body">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {/* Example doors - in production, fetch from API */}
                <DoorControl doorId={1} name="Main Entrance" />
                <DoorControl doorId={2} name="Side Door" />
                <DoorControl doorId={3} name="Server Room" />
              </div>
            </div>
          </div>

          {/* Outputs */}
          {ioStatus && ioStatus.outputs && ioStatus.outputs.length > 0 && (
            <div className="card">
              <div className="card-header">
                <h2 className="text-xl font-semibold text-white">Outputs</h2>
              </div>
              <div className="card-body">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {ioStatus.outputs.map((output) => (
                    <OutputControl key={output.id} output={output} />
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Relays */}
          {ioStatus && ioStatus.relays && ioStatus.relays.length > 0 && (
            <div className="card">
              <div className="card-header">
                <h2 className="text-xl font-semibold text-white">Relays</h2>
              </div>
              <div className="card-body">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {ioStatus.relays.map((relay) => (
                    <RelayControl key={relay.id} relay={relay} />
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Control Macros */}
          {macrosData && macrosData.macros && (
            <div className="card">
              <div className="card-header">
                <h2 className="text-xl font-semibold text-white">Control Macros</h2>
              </div>
              <div className="card-body">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {macrosData.macros.map((macro) => (
                    <MacroControl key={macro.macro_id} macro={macro} />
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Emergency Controls */}
          <div className="card border-2 border-red-500">
            <div className="card-header bg-red-900/20">
              <div className="flex items-center space-x-2">
                <AlertTriangle className="h-6 w-6 text-red-500" />
                <h2 className="text-xl font-semibold text-white">Emergency Controls</h2>
              </div>
            </div>
            <div className="card-body">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <EmergencyLockdownButton />
                <EmergencyUnlockButton />
                <ReturnToNormalButton />
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

function DoorControl({ doorId, name }: { doorId: number; name: string }) {
  const queryClient = useQueryClient();

  const unlockMutation = useMutation({
    mutationFn: (duration?: number) => apiClient.unlockDoor(doorId, duration, 'Web UI'),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['panel'] });
    },
  });

  const lockMutation = useMutation({
    mutationFn: () => apiClient.lockDoor(doorId, 'Web UI'),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['panel'] });
    },
  });

  return (
    <div className="p-4 bg-slate-700 rounded-lg">
      <div className="flex items-center space-x-3 mb-4">
        <DoorOpen className="h-6 w-6 text-primary-400" />
        <div>
          <h3 className="font-medium text-white">{name}</h3>
          <p className="text-xs text-slate-400">Door {doorId}</p>
        </div>
      </div>

      <div className="space-y-2">
        <button
          onClick={() => unlockMutation.mutate(5)}
          disabled={unlockMutation.isPending}
          className="btn btn-primary w-full text-sm"
        >
          <Unlock className="h-4 w-4 mr-2 inline" />
          Unlock (5s)
        </button>

        <button
          onClick={() => lockMutation.mutate()}
          disabled={lockMutation.isPending}
          className="btn btn-secondary w-full text-sm"
        >
          <Lock className="h-4 w-4 mr-2 inline" />
          Lock
        </button>
      </div>

      {(unlockMutation.isSuccess || lockMutation.isSuccess) && (
        <p className="text-xs text-green-400 mt-2">
          {unlockMutation.data?.message || lockMutation.data?.message}
        </p>
      )}
    </div>
  );
}

function OutputControl({ output }: { output: any }) {
  const queryClient = useQueryClient();

  const toggleMutation = useMutation({
    mutationFn: () => apiClient.toggleOutput(output.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['panel'] });
    },
  });

  const pulseMutation = useMutation({
    mutationFn: () => apiClient.pulseOutput(output.id, 2000),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['panel'] });
    },
  });

  const isActive = output.state === 'active';

  return (
    <div className="p-4 bg-slate-700 rounded-lg">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-3">
          <Power className={`h-6 w-6 ${isActive ? 'text-green-500' : 'text-slate-400'}`} />
          <div>
            <h3 className="font-medium text-white">{output.name}</h3>
            <p className="text-xs text-slate-400">{output.type}</p>
          </div>
        </div>
        <div className={`w-3 h-3 rounded-full ${isActive ? 'bg-green-500 animate-pulse' : 'bg-slate-600'}`} />
      </div>

      <div className="space-y-2">
        <button
          onClick={() => toggleMutation.mutate()}
          disabled={toggleMutation.isPending}
          className="btn btn-primary w-full text-sm"
        >
          Toggle
        </button>

        <button
          onClick={() => pulseMutation.mutate()}
          disabled={pulseMutation.isPending}
          className="btn btn-secondary w-full text-sm"
        >
          <Zap className="h-4 w-4 mr-2 inline" />
          Pulse (2s)
        </button>
      </div>

      <div className="mt-3 text-xs text-slate-400">
        <p>Activations today: {output.activation_count_today}</p>
      </div>
    </div>
  );
}

function RelayControl({ relay }: { relay: any }) {
  const queryClient = useQueryClient();

  const activateMutation = useMutation({
    mutationFn: () => apiClient.activateRelay(relay.id, 2000),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['panel'] });
    },
  });

  const isActive = relay.state === 'active';

  return (
    <div className="p-4 bg-slate-700 rounded-lg">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-3">
          <Zap className={`h-6 w-6 ${isActive ? 'text-yellow-500' : 'text-slate-400'}`} />
          <div>
            <h3 className="font-medium text-white">{relay.name}</h3>
            <p className="text-xs text-slate-400">{relay.mode}</p>
          </div>
        </div>
        <div className={`w-3 h-3 rounded-full ${isActive ? 'bg-yellow-500 animate-pulse' : 'bg-slate-600'}`} />
      </div>

      <button
        onClick={() => activateMutation.mutate()}
        disabled={activateMutation.isPending}
        className="btn btn-primary w-full text-sm"
      >
        Activate (2s)
      </button>

      {relay.linked_to && (
        <p className="mt-2 text-xs text-slate-400">Linked to: {relay.linked_to}</p>
      )}
    </div>
  );
}

function MacroControl({ macro }: { macro: Macro }) {
  const queryClient = useQueryClient();

  const executeMutation = useMutation({
    mutationFn: () => apiClient.executeMacro(macro.macro_id, 'Web UI'),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['panel'] });
    },
  });

  return (
    <div className="p-4 bg-slate-700 rounded-lg">
      <div className="flex items-center space-x-3 mb-3">
        <PlayCircle className="h-5 w-5 text-primary-400" />
        <h3 className="font-medium text-white">{macro.name}</h3>
      </div>

      <p className="text-sm text-slate-300 mb-4">{macro.description}</p>

      <button
        onClick={() => executeMutation.mutate()}
        disabled={executeMutation.isPending}
        className="btn btn-primary w-full text-sm"
      >
        Execute Macro
      </button>

      {executeMutation.isSuccess && (
        <p className="text-xs text-green-400 mt-2">
          Macro executed successfully
        </p>
      )}
    </div>
  );
}

function EmergencyLockdownButton() {
  const queryClient = useQueryClient();

  const lockdownMutation = useMutation({
    mutationFn: () => apiClient.emergencyLockdown('Web UI Emergency', 'Administrator'),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['panel'] });
    },
  });

  return (
    <div className="p-4 bg-red-900/20 border border-red-500 rounded-lg">
      <h3 className="font-medium text-white mb-2">Emergency Lockdown</h3>
      <p className="text-sm text-slate-300 mb-4">Lock ALL doors immediately</p>

      <button
        onClick={() => {
          if (confirm('Are you sure you want to activate EMERGENCY LOCKDOWN?')) {
            lockdownMutation.mutate();
          }
        }}
        disabled={lockdownMutation.isPending}
        className="btn btn-danger w-full"
      >
        <Lock className="h-4 w-4 mr-2 inline" />
        LOCKDOWN
      </button>
    </div>
  );
}

function EmergencyUnlockButton() {
  const queryClient = useQueryClient();

  const unlockMutation = useMutation({
    mutationFn: () => apiClient.emergencyUnlockAll('Fire evacuation', 'Administrator'),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['panel'] });
    },
  });

  return (
    <div className="p-4 bg-orange-900/20 border border-orange-500 rounded-lg">
      <h3 className="font-medium text-white mb-2">Emergency Unlock All</h3>
      <p className="text-sm text-slate-300 mb-4">Unlock ALL doors for evacuation</p>

      <button
        onClick={() => {
          if (confirm('Are you sure you want to UNLOCK ALL doors?')) {
            unlockMutation.mutate();
          }
        }}
        disabled={unlockMutation.isPending}
        className="btn btn-danger w-full"
      >
        <Unlock className="h-4 w-4 mr-2 inline" />
        UNLOCK ALL
      </button>
    </div>
  );
}

function ReturnToNormalButton() {
  const queryClient = useQueryClient();

  const normalMutation = useMutation({
    mutationFn: () => apiClient.returnToNormal('Administrator'),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['panel'] });
    },
  });

  return (
    <div className="p-4 bg-green-900/20 border border-green-500 rounded-lg">
      <h3 className="font-medium text-white mb-2">Return to Normal</h3>
      <p className="text-sm text-slate-300 mb-4">Clear all overrides and return to normal operation</p>

      <button
        onClick={() => normalMutation.mutate()}
        disabled={normalMutation.isPending}
        className="btn btn-success w-full"
      >
        Return to Normal
      </button>
    </div>
  );
}
