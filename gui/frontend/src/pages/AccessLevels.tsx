/**
 * Access Level Management Page
 * Manage access level groups and assign doors to levels
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
  X,
  Save,
  AlertCircle,
  Check,
  DoorOpen,
  Users as UsersIcon,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import type { AccessLevel, AccessLevelCreate, AccessLevelUpdate, DoorConfig } from '../types/v2.1';

export default function AccessLevels() {
  const queryClient = useQueryClient();
  const canCreate = usePermission('access_level.create');
  const canUpdate = usePermission('access_level.update');
  const canDelete = usePermission('access_level.delete');

  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showDoorsModal, setShowDoorsModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [selectedLevel, setSelectedLevel] = useState<AccessLevel | null>(null);
  const [expandedLevels, setExpandedLevels] = useState<Set<number>>(new Set());
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Fetch access levels
  const { data: accessLevels, isLoading } = useQuery({
    queryKey: ['access-levels'],
    queryFn: () => apiClientV2_1.getAccessLevels(false),
  });

  // Create access level mutation
  const createMutation = useMutation({
    mutationFn: (data: AccessLevelCreate) => apiClientV2_1.createAccessLevel(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['access-levels'] });
      setShowCreateModal(false);
      setSuccess('Access level created successfully');
      setTimeout(() => setSuccess(''), 3000);
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail || 'Failed to create access level');
    },
  });

  // Update access level mutation
  const updateMutation = useMutation({
    mutationFn: ({ levelId, data }: { levelId: number; data: AccessLevelUpdate }) =>
      apiClientV2_1.updateAccessLevel(levelId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['access-levels'] });
      setShowEditModal(false);
      setSuccess('Access level updated successfully');
      setTimeout(() => setSuccess(''), 3000);
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail || 'Failed to update access level');
    },
  });

  // Delete access level mutation
  const deleteMutation = useMutation({
    mutationFn: (levelId: number) => apiClientV2_1.deleteAccessLevel(levelId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['access-levels'] });
      setShowDeleteModal(false);
      setSuccess('Access level deleted successfully');
      setTimeout(() => setSuccess(''), 3000);
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail || 'Failed to delete access level');
    },
  });

  const toggleExpanded = (levelId: number) => {
    const newExpanded = new Set(expandedLevels);
    if (newExpanded.has(levelId)) {
      newExpanded.delete(levelId);
    } else {
      newExpanded.add(levelId);
    }
    setExpandedLevels(newExpanded);
  };

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6 flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-white">Access Level Management</h1>
          <p className="text-gray-400 mt-1">Manage access level groups and door assignments</p>
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
            Create Access Level
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
          <p className="text-gray-400">Loading access levels...</p>
        </div>
      )}

      {/* Access Levels List */}
      {!isLoading && accessLevels && (
        <div className="space-y-4">
          {accessLevels.length === 0 ? (
            <div className="bg-gray-800 rounded-lg p-12 text-center">
              <Shield className="w-16 h-16 text-gray-600 mx-auto mb-4" />
              <p className="text-gray-400">No access levels configured. Create one to get started.</p>
            </div>
          ) : (
            accessLevels.map((level) => (
              <AccessLevelCard
                key={level.id}
                level={level}
                isExpanded={expandedLevels.has(level.id)}
                onToggleExpand={() => toggleExpanded(level.id)}
                onEdit={() => {
                  setSelectedLevel(level);
                  setError('');
                  setShowEditModal(true);
                }}
                onManageDoors={() => {
                  setSelectedLevel(level);
                  setError('');
                  setShowDoorsModal(true);
                }}
                onDelete={() => {
                  setSelectedLevel(level);
                  setError('');
                  setShowDeleteModal(true);
                }}
                canUpdate={canUpdate}
                canDelete={canDelete}
              />
            ))
          )}
        </div>
      )}

      {/* Modals */}
      {showCreateModal && <CreateAccessLevelModal onClose={() => setShowCreateModal(false)} onSubmit={createMutation} />}
      {showEditModal && selectedLevel && (
        <EditAccessLevelModal level={selectedLevel} onClose={() => setShowEditModal(false)} onSubmit={updateMutation} />
      )}
      {showDoorsModal && selectedLevel && <ManageDoorsModal level={selectedLevel} onClose={() => setShowDoorsModal(false)} />}
      {showDeleteModal && selectedLevel && (
        <DeleteAccessLevelModal
          level={selectedLevel}
          onClose={() => setShowDeleteModal(false)}
          onConfirm={() => deleteMutation.mutate(selectedLevel.id)}
          isLoading={deleteMutation.isPending}
        />
      )}
    </div>
  );
}

// Access Level Card Component
function AccessLevelCard({ level, isExpanded, onToggleExpand, onEdit, onManageDoors, onDelete, canUpdate, canDelete }: any) {
  const { data: doors } = useQuery({
    queryKey: ['access-level-doors', level.id],
    queryFn: () => apiClientV2_1.getAccessLevelDoors(level.id),
    enabled: isExpanded,
  });

  const getPriorityColor = (priority: number) => {
    if (priority >= 80) return 'text-red-400';
    if (priority >= 50) return 'text-yellow-400';
    if (priority >= 20) return 'text-green-400';
    return 'text-gray-400';
  };

  return (
    <div className="bg-gray-800 rounded-lg shadow-lg overflow-hidden border border-gray-700">
      {/* Header */}
      <div className="p-6 flex items-center justify-between">
        <div className="flex items-center space-x-4 flex-1">
          <div className={`p-3 rounded-lg bg-blue-900/30 border border-blue-500`}>
            <Shield className="w-6 h-6 text-blue-400" />
          </div>
          <div className="flex-1">
            <div className="flex items-center space-x-3">
              <h3 className="text-xl font-bold text-white">{level.name}</h3>
              <span className={`text-sm font-semibold ${getPriorityColor(level.priority)}`}>
                Priority: {level.priority}
              </span>
              {!level.is_active && (
                <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-gray-700 text-gray-400">
                  Inactive
                </span>
              )}
            </div>
            {level.description && <p className="text-gray-400 mt-1">{level.description}</p>}
            {doors && (
              <p className="text-gray-500 text-sm mt-1">
                {doors.length} {doors.length === 1 ? 'door' : 'doors'} assigned
              </p>
            )}
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center space-x-2">
          {canUpdate && (
            <>
              <button
                onClick={onManageDoors}
                className="p-2 rounded-lg text-purple-400 hover:text-purple-300 hover:bg-purple-900/30 transition"
                title="Manage Doors"
              >
                <DoorOpen className="w-5 h-5" />
              </button>
              <button
                onClick={onEdit}
                className="p-2 rounded-lg text-yellow-400 hover:text-yellow-300 hover:bg-yellow-900/30 transition"
                title="Edit Access Level"
              >
                <Edit className="w-5 h-5" />
              </button>
            </>
          )}
          {canDelete && (
            <button
              onClick={onDelete}
              className="p-2 rounded-lg text-red-400 hover:text-red-300 hover:bg-red-900/30 transition"
              title="Delete Access Level"
            >
              <Trash className="w-5 h-5" />
            </button>
          )}
          <button
            onClick={onToggleExpand}
            className="p-2 rounded-lg text-gray-400 hover:text-white hover:bg-gray-700 transition"
            title={isExpanded ? 'Collapse' : 'Expand'}
          >
            {isExpanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {/* Expanded Content */}
      {isExpanded && doors && (
        <div className="border-t border-gray-700 p-6 bg-gray-750">
          <h4 className="text-lg font-semibold text-white mb-4 flex items-center">
            <DoorOpen className="w-5 h-5 mr-2" />
            Assigned Doors
          </h4>
          {doors.length === 0 ? (
            <p className="text-gray-400 text-sm">No doors assigned to this access level</p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {doors.map((door: any) => (
                <div key={door.door_id} className="bg-gray-800 rounded-lg p-3 border border-gray-600">
                  <p className="text-white font-medium">{door.door_name}</p>
                  {door.location && <p className="text-gray-400 text-xs mt-1">{door.location}</p>}
                  <div className="mt-2 flex space-x-2">
                    {door.entry_allowed && (
                      <span className="text-xs bg-green-900/50 text-green-400 px-2 py-0.5 rounded">Entry</span>
                    )}
                    {door.exit_allowed && (
                      <span className="text-xs bg-blue-900/50 text-blue-400 px-2 py-0.5 rounded">Exit</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// Create Access Level Modal
function CreateAccessLevelModal({ onClose, onSubmit }: any) {
  const [formData, setFormData] = useState<AccessLevelCreate>({
    name: '',
    description: '',
    priority: 50,
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit.mutate(formData);
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-800 rounded-lg shadow-xl max-w-2xl w-full">
        <div className="p-6 border-b border-gray-700 flex justify-between items-center">
          <h2 className="text-2xl font-bold text-white">Create Access Level</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-white">
            <X className="w-6 h-6" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-gray-300 text-sm font-medium mb-2">Name *</label>
            <input
              type="text"
              required
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-blue-500"
              placeholder="e.g., Executive Access"
            />
          </div>

          <div>
            <label className="block text-gray-300 text-sm font-medium mb-2">Description</label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-blue-500"
              rows={3}
              placeholder="Optional description"
            />
          </div>

          <div>
            <label className="block text-gray-300 text-sm font-medium mb-2">
              Priority: {formData.priority}
            </label>
            <input
              type="range"
              min="0"
              max="100"
              value={formData.priority}
              onChange={(e) => setFormData({ ...formData, priority: parseInt(e.target.value) })}
              className="w-full"
            />
            <div className="flex justify-between text-xs text-gray-400 mt-1">
              <span>Low (0)</span>
              <span>Medium (50)</span>
              <span>High (100)</span>
            </div>
            <p className="text-gray-400 text-xs mt-2">
              Higher priority access levels take precedence when a user has multiple levels.
            </p>
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
                  Create Access Level
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// Edit Access Level Modal
function EditAccessLevelModal({ level, onClose, onSubmit }: any) {
  const [formData, setFormData] = useState<AccessLevelUpdate>({
    name: level.name,
    description: level.description || '',
    priority: level.priority,
    is_active: level.is_active,
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit.mutate({ levelId: level.id, data: formData });
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-800 rounded-lg shadow-xl max-w-2xl w-full">
        <div className="p-6 border-b border-gray-700 flex justify-between items-center">
          <h2 className="text-2xl font-bold text-white">Edit Access Level - {level.name}</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-white">
            <X className="w-6 h-6" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-gray-300 text-sm font-medium mb-2">Name *</label>
            <input
              type="text"
              required
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-gray-300 text-sm font-medium mb-2">Description</label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-blue-500"
              rows={3}
            />
          </div>

          <div>
            <label className="block text-gray-300 text-sm font-medium mb-2">
              Priority: {formData.priority}
            </label>
            <input
              type="range"
              min="0"
              max="100"
              value={formData.priority}
              onChange={(e) => setFormData({ ...formData, priority: parseInt(e.target.value) })}
              className="w-full"
            />
            <div className="flex justify-between text-xs text-gray-400 mt-1">
              <span>Low (0)</span>
              <span>Medium (50)</span>
              <span>High (100)</span>
            </div>
          </div>

          <div>
            <label className="flex items-center space-x-2 text-gray-300 cursor-pointer">
              <input
                type="checkbox"
                checked={formData.is_active}
                onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                className="rounded bg-gray-700 border-gray-600"
              />
              <span>Active</span>
            </label>
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

// Manage Doors Modal
function ManageDoorsModal({ level, onClose }: any) {
  const queryClient = useQueryClient();
  const [selectedDoors, setSelectedDoors] = useState<Set<number>>(new Set());

  const { data: allDoors } = useQuery({
    queryKey: ['doors'],
    queryFn: () => apiClientV2_1.getDoorConfigs(),
  });

  const { data: assignedDoors } = useQuery({
    queryKey: ['access-level-doors', level.id],
    queryFn: () => apiClientV2_1.getAccessLevelDoors(level.id),
  });

  const addDoorMutation = useMutation({
    mutationFn: (doorId: number) =>
      apiClientV2_1.addDoorToAccessLevel(level.id, {
        door_id: doorId,
        timezone_id: 2,
        entry_allowed: true,
        exit_allowed: true,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['access-level-doors', level.id] });
    },
  });

  const removeDoorMutation = useMutation({
    mutationFn: (doorId: number) => apiClientV2_1.removeDoorFromAccessLevel(level.id, doorId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['access-level-doors', level.id] });
    },
  });

  const assignedDoorIds = new Set(assignedDoors?.map((d: any) => d.door_id) || []);
  const availableDoors = allDoors?.filter((d: DoorConfig) => !assignedDoorIds.has(d.door_id)) || [];

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-800 rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-gray-700 flex justify-between items-center sticky top-0 bg-gray-800">
          <h2 className="text-2xl font-bold text-white">Manage Doors - {level.name}</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-white">
            <X className="w-6 h-6" />
          </button>
        </div>

        <div className="p-6">
          <div className="grid grid-cols-2 gap-6">
            {/* Available Doors */}
            <div>
              <h3 className="text-lg font-semibold text-white mb-4">Available Doors</h3>
              {availableDoors.length === 0 ? (
                <p className="text-gray-400 text-sm">All doors are already assigned</p>
              ) : (
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {availableDoors.map((door) => (
                    <div
                      key={door.door_id}
                      className="bg-gray-700 rounded-lg p-3 flex justify-between items-center hover:bg-gray-650 transition"
                    >
                      <div>
                        <p className="text-white font-medium">{door.door_name}</p>
                        {door.location && <p className="text-gray-400 text-xs">{door.location}</p>}
                      </div>
                      <button
                        onClick={() => addDoorMutation.mutate(door.door_id)}
                        disabled={addDoorMutation.isPending}
                        className="px-3 py-1 bg-green-600 text-white rounded hover:bg-green-700 transition disabled:opacity-50 text-sm"
                      >
                        Add
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Assigned Doors */}
            <div>
              <h3 className="text-lg font-semibold text-white mb-4">Assigned Doors</h3>
              {!assignedDoors || assignedDoors.length === 0 ? (
                <p className="text-gray-400 text-sm">No doors assigned yet</p>
              ) : (
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {assignedDoors.map((door: any) => (
                    <div
                      key={door.door_id}
                      className="bg-gray-700 rounded-lg p-3 flex justify-between items-center hover:bg-gray-650 transition"
                    >
                      <div>
                        <p className="text-white font-medium">{door.door_name}</p>
                        {door.location && <p className="text-gray-400 text-xs">{door.location}</p>}
                      </div>
                      <button
                        onClick={() => removeDoorMutation.mutate(door.door_id)}
                        disabled={removeDoorMutation.isPending}
                        className="px-3 py-1 bg-red-600 text-white rounded hover:bg-red-700 transition disabled:opacity-50 text-sm"
                      >
                        Remove
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          <div className="flex justify-end pt-6">
            <button
              onClick={onClose}
              className="px-4 py-2 bg-gray-700 text-gray-300 rounded-lg hover:bg-gray-600 transition"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// Delete Access Level Modal
function DeleteAccessLevelModal({ level, onClose, onConfirm, isLoading }: any) {
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-800 rounded-lg shadow-xl max-w-md w-full">
        <div className="p-6 border-b border-gray-700">
          <h2 className="text-2xl font-bold text-white">Confirm Delete</h2>
        </div>

        <div className="p-6">
          <p className="text-gray-300 mb-4">Are you sure you want to delete this access level?</p>
          <div className="bg-gray-700 rounded-lg p-4 mb-6">
            <p className="text-white font-semibold">{level.name}</p>
            {level.description && <p className="text-gray-400 text-sm">{level.description}</p>}
            <p className="text-gray-400 text-sm">Priority: {level.priority}</p>
          </div>
          <p className="text-red-400 text-sm font-semibold">
            This will also remove all door assignments and user assignments for this access level.
          </p>
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
                Delete Access Level
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
