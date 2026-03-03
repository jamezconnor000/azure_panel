/**
 * Door Management Page
 * Manage door configurations, naming, and OSDP Secure Channel settings
 */

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClientV2_1 from '../api/clientV2_1';
import { usePermission } from '../contexts/AuthContext';
import {
  Shield,
  Plus,
  Edit,
  Trash,
  Power,
  X,
  Save,
  AlertCircle,
  Check,
  Lock,
  Key,
  MapPin,
  Tag,
} from 'lucide-react';
import type { DoorConfig, DoorConfigCreate, DoorConfigUpdate, DoorType } from '../types/v2.1';

export default function DoorManagement() {
  const queryClient = useQueryClient();
  const canCreate = usePermission('door.create');
  const canUpdate = usePermission('door.update');
  const canDelete = usePermission('door.delete');
  const canConfigure = usePermission('door.configure');

  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showOSDPModal, setShowOSDPModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [selectedDoor, setSelectedDoor] = useState<DoorConfig | null>(null);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Fetch doors
  const { data: doors, isLoading } = useQuery({
    queryKey: ['doors'],
    queryFn: () => apiClientV2_1.getDoorConfigs(),
  });

  // Create door mutation
  const createMutation = useMutation({
    mutationFn: (data: DoorConfigCreate) => apiClientV2_1.createDoorConfig(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['doors'] });
      setShowCreateModal(false);
      setSuccess('Door created successfully');
      setTimeout(() => setSuccess(''), 3000);
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail || 'Failed to create door');
    },
  });

  // Update door mutation
  const updateMutation = useMutation({
    mutationFn: ({ doorId, data }: { doorId: number; data: DoorConfigUpdate }) =>
      apiClientV2_1.updateDoorConfig(doorId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['doors'] });
      setShowEditModal(false);
      setSuccess('Door updated successfully');
      setTimeout(() => setSuccess(''), 3000);
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail || 'Failed to update door');
    },
  });

  // Delete door mutation
  const deleteMutation = useMutation({
    mutationFn: (doorId: number) => apiClientV2_1.deleteDoorConfig(doorId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['doors'] });
      setShowDeleteModal(false);
      setSuccess('Door deleted successfully');
      setTimeout(() => setSuccess(''), 3000);
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail || 'Failed to delete door');
    },
  });

  // Enable OSDP mutation
  const enableOSDPMutation = useMutation({
    mutationFn: ({ doorId, scbk, readerAddress }: { doorId: number; scbk: string; readerAddress: number }) =>
      apiClientV2_1.enableOSDP(doorId, { scbk, reader_address: readerAddress }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['doors'] });
      setShowOSDPModal(false);
      setSuccess('OSDP Secure Channel enabled successfully');
      setTimeout(() => setSuccess(''), 3000);
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail || 'Failed to enable OSDP');
    },
  });

  // Disable OSDP mutation
  const disableOSDPMutation = useMutation({
    mutationFn: (doorId: number) => apiClientV2_1.disableOSDP(doorId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['doors'] });
      setSuccess('OSDP Secure Channel disabled successfully');
      setTimeout(() => setSuccess(''), 3000);
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail || 'Failed to disable OSDP');
    },
  });

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6 flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-white">Door Management</h1>
          <p className="text-gray-400 mt-1">Manage doors, naming, and OSDP Secure Channel</p>
        </div>
        {canCreate && (
          <button
            onClick={() => {
              setError('');
              setShowCreateModal(true);
            }}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg flex items-center transition"
          >
            <Plus className="w-5 h-5 mr-2" />
            Create Door
          </button>
        )}
      </div>

      {/* Success Message */}
      {success && (
        <div className="mb-4 bg-green-900/50 border border-green-500 rounded-lg p-4 flex items-center">
          <Check className="w-5 h-5 text-green-500 mr-3" />
          <p className="text-green-200">{success}</p>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="mb-4 bg-red-900/50 border border-red-500 rounded-lg p-4 flex items-center">
          <AlertCircle className="w-5 h-5 text-red-500 mr-3" />
          <p className="text-red-200">{error}</p>
          <button onClick={() => setError('')} className="ml-auto">
            <X className="w-5 h-5 text-red-400" />
          </button>
        </div>
      )}

      {/* Loading State */}
      {isLoading && (
        <div className="bg-gray-800 rounded-lg p-12 text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-400">Loading doors...</p>
        </div>
      )}

      {/* Doors Table */}
      {!isLoading && doors && (
        <div className="bg-gray-800 rounded-lg overflow-hidden shadow-lg">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-700">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    Door ID
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    Door Name
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    Location
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    Type
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    OSDP Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    Reader Addr
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-700">
                {doors.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="px-6 py-12 text-center text-gray-400">
                      No doors configured. Create your first door to get started.
                    </td>
                  </tr>
                ) : (
                  doors.map((door) => (
                    <tr key={door.door_id} className="hover:bg-gray-750 transition">
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-300">
                        {door.door_id}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-white font-medium">{door.door_name}</div>
                        {door.description && (
                          <div className="text-gray-400 text-sm">{door.description}</div>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                        {door.location || '-'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-700 text-gray-300">
                          {door.door_type || 'interior'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {door.osdp_enabled ? (
                          <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-green-900/50 text-green-400 border border-green-500">
                            <Shield className="w-3 h-3 mr-1" />
                            Enabled
                          </span>
                        ) : (
                          <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-gray-700 text-gray-400">
                            <Shield className="w-3 h-3 mr-1" />
                            Disabled
                          </span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300 font-mono">
                        {door.reader_address !== undefined && door.reader_address !== null
                          ? door.reader_address
                          : '-'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <div className="flex space-x-2">
                          {canConfigure && (
                            <button
                              onClick={() => {
                                setSelectedDoor(door);
                                setError('');
                                setShowOSDPModal(true);
                              }}
                              className={`p-2 rounded-lg transition ${
                                door.osdp_enabled
                                  ? 'text-green-400 hover:text-green-300 hover:bg-green-900/30'
                                  : 'text-blue-400 hover:text-blue-300 hover:bg-blue-900/30'
                              }`}
                              title={door.osdp_enabled ? 'Configure OSDP' : 'Enable OSDP'}
                            >
                              <Power className="w-5 h-5" />
                            </button>
                          )}
                          {door.osdp_enabled && canConfigure && (
                            <button
                              onClick={() => {
                                if (confirm('Are you sure you want to disable OSDP Secure Channel?')) {
                                  disableOSDPMutation.mutate(door.door_id);
                                }
                              }}
                              className="p-2 rounded-lg text-orange-400 hover:text-orange-300 hover:bg-orange-900/30 transition"
                              title="Disable OSDP"
                            >
                              <Lock className="w-5 h-5" />
                            </button>
                          )}
                          {canUpdate && (
                            <button
                              onClick={() => {
                                setSelectedDoor(door);
                                setError('');
                                setShowEditModal(true);
                              }}
                              className="p-2 rounded-lg text-yellow-400 hover:text-yellow-300 hover:bg-yellow-900/30 transition"
                              title="Edit Door"
                            >
                              <Edit className="w-5 h-5" />
                            </button>
                          )}
                          {canDelete && (
                            <button
                              onClick={() => {
                                setSelectedDoor(door);
                                setError('');
                                setShowDeleteModal(true);
                              }}
                              className="p-2 rounded-lg text-red-400 hover:text-red-300 hover:bg-red-900/30 transition"
                              title="Delete Door"
                            >
                              <Trash className="w-5 h-5" />
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Create Door Modal */}
      {showCreateModal && <CreateDoorModal onClose={() => setShowCreateModal(false)} onSubmit={createMutation} />}

      {/* Edit Door Modal */}
      {showEditModal && selectedDoor && (
        <EditDoorModal door={selectedDoor} onClose={() => setShowEditModal(false)} onSubmit={updateMutation} />
      )}

      {/* OSDP Configuration Modal */}
      {showOSDPModal && selectedDoor && (
        <OSDPConfigModal
          door={selectedDoor}
          onClose={() => setShowOSDPModal(false)}
          onSubmit={enableOSDPMutation}
        />
      )}

      {/* Delete Confirmation Modal */}
      {showDeleteModal && selectedDoor && (
        <DeleteConfirmModal
          door={selectedDoor}
          onClose={() => setShowDeleteModal(false)}
          onConfirm={() => deleteMutation.mutate(selectedDoor.door_id)}
          isLoading={deleteMutation.isPending}
        />
      )}
    </div>
  );
}

// Create Door Modal Component
function CreateDoorModal({ onClose, onSubmit }: any) {
  const [formData, setFormData] = useState<DoorConfigCreate>({
    door_id: 0,
    door_name: '',
    description: '',
    location: '',
    door_type: 'interior',
    osdp_enabled: false,
    baud_rate: 9600,
    led_control: true,
    buzzer_control: true,
    is_monitored: true,
    alert_on_failure: true,
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit.mutate(formData);
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-800 rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-gray-700 flex justify-between items-center sticky top-0 bg-gray-800">
          <h2 className="text-2xl font-bold text-white">Create Door</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-white">
            <X className="w-6 h-6" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-gray-300 text-sm font-medium mb-2">Door ID *</label>
              <input
                type="number"
                required
                value={formData.door_id}
                onChange={(e) => setFormData({ ...formData, door_id: parseInt(e.target.value) })}
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-gray-300 text-sm font-medium mb-2">Door Type</label>
              <select
                value={formData.door_type}
                onChange={(e) => setFormData({ ...formData, door_type: e.target.value as DoorType })}
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-blue-500"
              >
                <option value="entry">Entry</option>
                <option value="exit">Exit</option>
                <option value="interior">Interior</option>
                <option value="emergency">Emergency</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-gray-300 text-sm font-medium mb-2">Door Name *</label>
            <input
              type="text"
              required
              value={formData.door_name}
              onChange={(e) => setFormData({ ...formData, door_name: e.target.value })}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-blue-500"
              placeholder="e.g., Main Entrance"
            />
          </div>

          <div>
            <label className="block text-gray-300 text-sm font-medium mb-2">Description</label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-blue-500"
              rows={2}
              placeholder="Optional description"
            />
          </div>

          <div>
            <label className="block text-gray-300 text-sm font-medium mb-2">Location</label>
            <input
              type="text"
              value={formData.location}
              onChange={(e) => setFormData({ ...formData, location: e.target.value })}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-blue-500"
              placeholder="e.g., Building A - Ground Floor"
            />
          </div>

          <div className="border-t border-gray-700 pt-4">
            <h3 className="text-lg font-semibold text-white mb-3">Hardware Capabilities</h3>
            <div className="grid grid-cols-2 gap-3">
              <label className="flex items-center space-x-2 text-gray-300 cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.led_control}
                  onChange={(e) => setFormData({ ...formData, led_control: e.target.checked })}
                  className="rounded bg-gray-700 border-gray-600"
                />
                <span>LED Control</span>
              </label>
              <label className="flex items-center space-x-2 text-gray-300 cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.buzzer_control}
                  onChange={(e) => setFormData({ ...formData, buzzer_control: e.target.checked })}
                  className="rounded bg-gray-700 border-gray-600"
                />
                <span>Buzzer Control</span>
              </label>
              <label className="flex items-center space-x-2 text-gray-300 cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.is_monitored}
                  onChange={(e) => setFormData({ ...formData, is_monitored: e.target.checked })}
                  className="rounded bg-gray-700 border-gray-600"
                />
                <span>Health Monitoring</span>
              </label>
              <label className="flex items-center space-x-2 text-gray-300 cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.alert_on_failure}
                  onChange={(e) => setFormData({ ...formData, alert_on_failure: e.target.checked })}
                  className="rounded bg-gray-700 border-gray-600"
                />
                <span>Alert on Failure</span>
              </label>
            </div>
          </div>

          <div className="flex justify-end space-x-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 bg-gray-700 text-gray-300 rounded-lg hover:bg-gray-600 transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={onSubmit.isPending}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition disabled:opacity-50 flex items-center"
            >
              {onSubmit.isPending ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Creating...
                </>
              ) : (
                <>
                  <Save className="w-4 h-4 mr-2" />
                  Create Door
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// Edit Door Modal (similar to Create but with existing data)
function EditDoorModal({ door, onClose, onSubmit }: any) {
  const [formData, setFormData] = useState<DoorConfigUpdate>({
    door_name: door.door_name,
    description: door.description || '',
    location: door.location || '',
    door_type: door.door_type,
    led_control: door.led_control,
    buzzer_control: door.buzzer_control,
    is_monitored: door.is_monitored,
    alert_on_failure: door.alert_on_failure,
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit.mutate({ doorId: door.door_id, data: formData });
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-800 rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-gray-700 flex justify-between items-center sticky top-0 bg-gray-800">
          <h2 className="text-2xl font-bold text-white">Edit Door - {door.door_name}</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-white">
            <X className="w-6 h-6" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-gray-300 text-sm font-medium mb-2">Door ID</label>
              <input
                type="number"
                value={door.door_id}
                disabled
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-gray-400 cursor-not-allowed"
              />
            </div>

            <div>
              <label className="block text-gray-300 text-sm font-medium mb-2">Door Type</label>
              <select
                value={formData.door_type}
                onChange={(e) => setFormData({ ...formData, door_type: e.target.value as DoorType })}
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-blue-500"
              >
                <option value="entry">Entry</option>
                <option value="exit">Exit</option>
                <option value="interior">Interior</option>
                <option value="emergency">Emergency</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-gray-300 text-sm font-medium mb-2">Door Name *</label>
            <input
              type="text"
              required
              value={formData.door_name}
              onChange={(e) => setFormData({ ...formData, door_name: e.target.value })}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-gray-300 text-sm font-medium mb-2">Description</label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-blue-500"
              rows={2}
            />
          </div>

          <div>
            <label className="block text-gray-300 text-sm font-medium mb-2">Location</label>
            <input
              type="text"
              value={formData.location}
              onChange={(e) => setFormData({ ...formData, location: e.target.value })}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div className="border-t border-gray-700 pt-4">
            <h3 className="text-lg font-semibold text-white mb-3">Hardware Capabilities</h3>
            <div className="grid grid-cols-2 gap-3">
              <label className="flex items-center space-x-2 text-gray-300 cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.led_control}
                  onChange={(e) => setFormData({ ...formData, led_control: e.target.checked })}
                  className="rounded bg-gray-700 border-gray-600"
                />
                <span>LED Control</span>
              </label>
              <label className="flex items-center space-x-2 text-gray-300 cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.buzzer_control}
                  onChange={(e) => setFormData({ ...formData, buzzer_control: e.target.checked })}
                  className="rounded bg-gray-700 border-gray-600"
                />
                <span>Buzzer Control</span>
              </label>
              <label className="flex items-center space-x-2 text-gray-300 cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.is_monitored}
                  onChange={(e) => setFormData({ ...formData, is_monitored: e.target.checked })}
                  className="rounded bg-gray-700 border-gray-600"
                />
                <span>Health Monitoring</span>
              </label>
              <label className="flex items-center space-x-2 text-gray-300 cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.alert_on_failure}
                  onChange={(e) => setFormData({ ...formData, alert_on_failure: e.target.checked })}
                  className="rounded bg-gray-700 border-gray-600"
                />
                <span>Alert on Failure</span>
              </label>
            </div>
          </div>

          <div className="flex justify-end space-x-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 bg-gray-700 text-gray-300 rounded-lg hover:bg-gray-600 transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={onSubmit.isPending}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition disabled:opacity-50 flex items-center"
            >
              {onSubmit.isPending ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Saving...
                </>
              ) : (
                <>
                  <Save className="w-4 h-4 mr-2" />
                  Save Changes
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// OSDP Configuration Modal - THE KEY FEATURE!
function OSDPConfigModal({ door, onClose, onSubmit }: any) {
  const [scbk, setScbk] = useState(door.scbk || '');
  const [readerAddress, setReaderAddress] = useState(door.reader_address || 0);
  const [error, setError] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    // Validate SCBK
    if (scbk.length !== 32) {
      setError('SCBK must be exactly 32 hexadecimal characters (16 bytes)');
      return;
    }

    if (!/^[0-9A-Fa-f]{32}$/.test(scbk)) {
      setError('SCBK must contain only hexadecimal characters (0-9, A-F)');
      return;
    }

    if (readerAddress < 0 || readerAddress > 126) {
      setError('Reader address must be between 0 and 126');
      return;
    }

    onSubmit.mutate({ doorId: door.door_id, scbk: scbk.toUpperCase(), readerAddress });
  };

  const generateRandomSCBK = () => {
    const hex = '0123456789ABCDEF';
    let result = '';
    for (let i = 0; i < 32; i++) {
      result += hex[Math.floor(Math.random() * 16)];
    }
    setScbk(result);
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-800 rounded-lg shadow-xl max-w-2xl w-full">
        <div className="p-6 border-b border-gray-700 flex justify-between items-center bg-gradient-to-r from-blue-900 to-green-900">
          <div className="flex items-center">
            <Shield className="w-8 h-8 text-green-400 mr-3" />
            <div>
              <h2 className="text-2xl font-bold text-white">OSDP Secure Channel Configuration</h2>
              <p className="text-gray-300 text-sm">{door.door_name}</p>
            </div>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-white">
            <X className="w-6 h-6" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* Info Box */}
          <div className="bg-blue-900/30 border border-blue-500 rounded-lg p-4">
            <h3 className="text-blue-300 font-semibold mb-2 flex items-center">
              <Key className="w-5 h-5 mr-2" />
              About OSDP Secure Channel
            </h3>
            <p className="text-gray-300 text-sm">
              OSDP Secure Channel provides AES-128 encrypted communication between the control panel and readers.
              The SCBK (Secure Channel Base Key) is used to derive session encryption keys.
            </p>
          </div>

          {/* Error Message */}
          {error && (
            <div className="bg-red-900/50 border border-red-500 rounded-lg p-4 flex items-center">
              <AlertCircle className="w-5 h-5 text-red-500 mr-3 flex-shrink-0" />
              <p className="text-red-200">{error}</p>
            </div>
          )}

          {/* SCBK Input */}
          <div>
            <label className="block text-gray-300 text-sm font-medium mb-2">
              Secure Channel Base Key (SCBK) *
            </label>
            <div className="flex space-x-2">
              <input
                type="text"
                required
                value={scbk}
                onChange={(e) => setScbk(e.target.value.toUpperCase())}
                className="flex-1 px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white font-mono focus:ring-2 focus:ring-blue-500"
                placeholder="0102030405060708090A0B0C0D0E0F10"
                maxLength={32}
              />
              <button
                type="button"
                onClick={generateRandomSCBK}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition"
                title="Generate Random Key"
              >
                <Key className="w-5 h-5" />
              </button>
            </div>
            <p className="text-gray-400 text-xs mt-1">
              32 hexadecimal characters (16 bytes). Example: 0102030405060708090A0B0C0D0E0F10
            </p>
            <p className="text-xs mt-1">
              <span className={scbk.length === 32 ? 'text-green-400' : 'text-yellow-400'}>
                {scbk.length}/32 characters
              </span>
            </p>
          </div>

          {/* Reader Address */}
          <div>
            <label className="block text-gray-300 text-sm font-medium mb-2">Reader Address *</label>
            <input
              type="number"
              required
              min={0}
              max={126}
              value={readerAddress}
              onChange={(e) => setReaderAddress(parseInt(e.target.value))}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-blue-500"
            />
            <p className="text-gray-400 text-xs mt-1">OSDP address (0-126). Usually 0 for single reader.</p>
          </div>

          {/* Current Status */}
          {door.osdp_enabled && (
            <div className="bg-green-900/30 border border-green-500 rounded-lg p-4">
              <h3 className="text-green-300 font-semibold mb-2">Current Status</h3>
              <div className="space-y-1 text-sm">
                <p className="text-gray-300">
                  OSDP: <span className="text-green-400 font-semibold">Enabled</span>
                </p>
                <p className="text-gray-300">
                  Reader Address: <span className="text-white font-mono">{door.reader_address}</span>
                </p>
              </div>
            </div>
          )}

          {/* Buttons */}
          <div className="flex justify-end space-x-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 bg-gray-700 text-gray-300 rounded-lg hover:bg-gray-600 transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={onSubmit.isPending}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition disabled:opacity-50 flex items-center"
            >
              {onSubmit.isPending ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Configuring...
                </>
              ) : (
                <>
                  <Shield className="w-4 h-4 mr-2" />
                  {door.osdp_enabled ? 'Update Configuration' : 'Enable OSDP'}
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// Delete Confirmation Modal
function DeleteConfirmModal({ door, onClose, onConfirm, isLoading }: any) {
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-800 rounded-lg shadow-xl max-w-md w-full">
        <div className="p-6 border-b border-gray-700">
          <h2 className="text-2xl font-bold text-white">Confirm Delete</h2>
        </div>

        <div className="p-6">
          <p className="text-gray-300 mb-4">Are you sure you want to delete this door?</p>
          <div className="bg-gray-700 rounded-lg p-4 mb-6">
            <p className="text-white font-semibold">{door.door_name}</p>
            <p className="text-gray-400 text-sm">Door ID: {door.door_id}</p>
            {door.location && <p className="text-gray-400 text-sm">Location: {door.location}</p>}
          </div>
          <p className="text-red-400 text-sm font-semibold">This action cannot be undone.</p>
        </div>

        <div className="p-6 border-t border-gray-700 flex justify-end space-x-3">
          <button
            type="button"
            onClick={onClose}
            disabled={isLoading}
            className="px-4 py-2 bg-gray-700 text-gray-300 rounded-lg hover:bg-gray-600 transition"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            disabled={isLoading}
            className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition disabled:opacity-50 flex items-center"
          >
            {isLoading ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                Deleting...
              </>
            ) : (
              <>
                <Trash className="w-4 h-4 mr-2" />
                Delete Door
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
