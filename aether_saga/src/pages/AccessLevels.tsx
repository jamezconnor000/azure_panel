/**
 * AccessLevels - Situ8-style Access Level Management
 */

import { useEffect, useState } from 'react';
import { Plus, Edit2, Trash2, Key, DoorOpen, X } from 'lucide-react';
import { accessLevelsApi, doorsApi } from '../api/bifrost';
import type { AccessLevel, Door } from '../types';

// DEMO MODE
const DEMO_MODE = true;
const MOCK_ACCESS_LEVELS: AccessLevel[] = [
  { id: 1, permission_id: 1, name: 'All Access', description: 'Full facility access', doors: [1, 2, 3, 4, 5, 6], priority: 1, is_active: true },
  { id: 2, permission_id: 2, name: 'Standard Employee', description: 'Common areas only', doors: [1, 2, 4], priority: 2, is_active: true },
  { id: 3, permission_id: 3, name: 'Server Room', description: 'IT and server room access', doors: [1, 2, 3], priority: 3, is_active: true },
  { id: 4, permission_id: 4, name: 'Executive', description: 'Executive suite access', doors: [1, 2, 5], priority: 4, is_active: true },
  { id: 5, permission_id: 5, name: 'Visitor', description: 'Main entrance only', doors: [1], priority: 5, is_active: true },
];

const MOCK_DOORS: Door[] = [
  { door_id: 1, name: 'Main Entrance', strike_time_ms: 5000 },
  { door_id: 2, name: 'Side Entrance', strike_time_ms: 5000 },
  { door_id: 3, name: 'Server Room', strike_time_ms: 3000 },
  { door_id: 4, name: 'Parking Garage', strike_time_ms: 10000 },
  { door_id: 5, name: 'Executive Suite', strike_time_ms: 5000 },
  { door_id: 6, name: 'Loading Dock', strike_time_ms: 15000 },
];

function AccessLevelModal({
  isOpen,
  onClose,
  onSave,
  accessLevel,
  doors,
}: {
  isOpen: boolean;
  onClose: () => void;
  onSave: (data: Partial<AccessLevel>) => void;
  accessLevel?: AccessLevel | null;
  doors: Door[];
}) {
  const [formData, setFormData] = useState<Partial<AccessLevel>>({
    permission_id: 0,
    name: '',
    description: '',
    doors: [],
  });

  useEffect(() => {
    if (accessLevel) {
      setFormData(accessLevel);
    } else {
      setFormData({
        permission_id: Math.floor(Math.random() * 1000) + 100,
        name: '',
        description: '',
        doors: [],
      });
    }
  }, [accessLevel, isOpen]);

  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave(formData);
  };

  const toggleDoor = (doorId: number) => {
    const currentDoors = formData.doors || [];
    if (currentDoors.includes(doorId)) {
      setFormData({ ...formData, doors: currentDoors.filter((d) => d !== doorId) });
    } else {
      setFormData({ ...formData, doors: [...currentDoors, doorId] });
    }
  };

  return (
    <div className="fixed inset-0 flex items-center justify-center z-50" style={{ background: 'rgba(0, 0, 0, 0.7)' }}>
      <div
        className="w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto rounded-md"
        style={{ background: '#161b22', border: '1px solid #30363d' }}
      >
        <div
          className="flex items-center justify-between px-6 py-4"
          style={{ borderBottom: '1px solid #30363d' }}
        >
          <h2 className="text-lg font-semibold" style={{ color: '#e6edf3' }}>
            {accessLevel ? 'Edit Access Level' : 'Add Access Level'}
          </h2>
          <button
            onClick={onClose}
            className="p-2 rounded-md transition-colors"
            style={{ color: '#7d8590' }}
          >
            <X size={18} />
          </button>
        </div>
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-xs mb-1.5" style={{ color: '#7d8590' }}>Permission ID</label>
            <input
              type="number"
              required
              className="w-full rounded-md px-4 py-2.5 focus:outline-none"
              style={{ background: '#0d1117', border: '1px solid #30363d', color: '#e6edf3' }}
              value={formData.permission_id || ''}
              onChange={(e) => setFormData({ ...formData, permission_id: parseInt(e.target.value) })}
              disabled={!!accessLevel}
            />
          </div>

          <div>
            <label className="block text-xs mb-1.5" style={{ color: '#7d8590' }}>Name *</label>
            <input
              type="text"
              required
              className="w-full rounded-md px-4 py-2.5 focus:outline-none"
              style={{ background: '#0d1117', border: '1px solid #30363d', color: '#e6edf3' }}
              value={formData.name || ''}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            />
          </div>

          <div>
            <label className="block text-xs mb-1.5" style={{ color: '#7d8590' }}>Description</label>
            <textarea
              className="w-full rounded-md px-4 py-2.5 focus:outline-none resize-none"
              style={{ background: '#0d1117', border: '1px solid #30363d', color: '#e6edf3' }}
              value={formData.description || ''}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              rows={3}
            />
          </div>

          <div>
            <label className="block text-xs mb-2" style={{ color: '#7d8590' }}>Doors</label>
            <div className="space-y-2 max-h-48 overflow-y-auto">
              {doors.length === 0 ? (
                <p className="text-sm" style={{ color: '#7d8590' }}>No doors available</p>
              ) : (
                doors.map((door) => (
                  <label
                    key={door.door_id}
                    className="flex items-center gap-3 p-3 rounded-md cursor-pointer transition-colors"
                    style={{ background: '#0d1117' }}
                  >
                    <input
                      type="checkbox"
                      checked={formData.doors?.includes(door.door_id) || false}
                      onChange={() => toggleDoor(door.door_id)}
                      className="w-4 h-4 rounded"
                    />
                    <DoorOpen size={16} style={{ color: '#7d8590' }} />
                    <span style={{ color: '#e6edf3' }}>{door.name}</span>
                    <span className="ml-auto text-sm" style={{ color: '#484f58' }}>ID: {door.door_id}</span>
                  </label>
                ))
              )}
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-4" style={{ borderTop: '1px solid #30363d' }}>
            <button
              type="button"
              onClick={onClose}
              className="px-5 py-2.5 rounded-md transition-colors"
              style={{ border: '1px solid #30363d', color: '#7d8590' }}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-5 py-2.5 rounded-md font-medium transition-colors"
              style={{ background: '#238636', color: '#ffffff' }}
            >
              {accessLevel ? 'Save Changes' : 'Add Access Level'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export function AccessLevels() {
  const [accessLevels, setAccessLevels] = useState<AccessLevel[]>([]);
  const [doors, setDoors] = useState<Door[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [selectedLevel, setSelectedLevel] = useState<AccessLevel | null>(null);

  const fetchData = async () => {
    if (DEMO_MODE) {
      setAccessLevels(MOCK_ACCESS_LEVELS);
      setDoors(MOCK_DOORS);
      setLoading(false);
      return;
    }
    try {
      setLoading(true);
      const [levelsData, doorsData] = await Promise.all([
        accessLevelsApi.list(),
        doorsApi.list(),
      ]);
      setAccessLevels(levelsData.access_levels || []);
      setDoors(doorsData.doors || []);
      setError(null);
    } catch (err) {
      setError('Failed to load access levels');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleSave = async (data: Partial<AccessLevel>) => {
    try {
      if (selectedLevel) {
        await accessLevelsApi.delete(selectedLevel.permission_id);
        await accessLevelsApi.create(data);
      } else {
        await accessLevelsApi.create(data);
      }
      setModalOpen(false);
      setSelectedLevel(null);
      fetchData();
    } catch (err) {
      console.error('Failed to save access level:', err);
    }
  };

  const handleDelete = async (permissionId: number) => {
    if (!confirm('Are you sure you want to delete this access level?')) return;
    try {
      await accessLevelsApi.delete(permissionId);
      fetchData();
    } catch (err) {
      console.error('Failed to delete access level:', err);
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
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span
              className="w-2 h-2 rounded-full"
              style={{ background: '#f97316' }}
            />
            <h1 className="text-xl font-semibold" style={{ color: '#e6edf3' }}>
              Access Levels
            </h1>
          </div>
          <p className="text-sm" style={{ color: '#7d8590' }}>
            Manage permission groups and door access
          </p>
        </div>
        <button
          onClick={() => {
            setSelectedLevel(null);
            setModalOpen(true);
          }}
          className="flex items-center gap-2 px-4 py-2 rounded-md font-medium transition-colors"
          style={{ background: '#238636', color: '#ffffff' }}
        >
          <Plus size={18} />
          Add Access Level
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-md" style={{ background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)' }}>
          <p style={{ color: '#ef4444' }}>{error}</p>
        </div>
      )}

      {/* Access Level Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {accessLevels.length === 0 ? (
          <div className="col-span-full p-8 text-center rounded-md" style={{ background: '#161b22', border: '1px solid #30363d' }}>
            <Key size={48} className="mx-auto mb-4" style={{ color: '#7d8590' }} />
            <p style={{ color: '#7d8590' }}>No access levels configured</p>
            <button
              onClick={() => setModalOpen(true)}
              className="mt-4"
              style={{ color: '#58a6ff' }}
            >
              Add your first access level
            </button>
          </div>
        ) : (
          accessLevels.map((level) => (
            <div
              key={level.permission_id}
              className="rounded-md overflow-hidden"
              style={{ background: '#161b22', border: '1px solid #30363d' }}
            >
              <div className="px-4 py-3" style={{ borderBottom: '1px solid #30363d' }}>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div
                      className="w-10 h-10 rounded-md flex items-center justify-center"
                      style={{ background: 'rgba(249, 115, 22, 0.15)', color: '#f97316' }}
                    >
                      <Key size={20} />
                    </div>
                    <div>
                      <h3 className="font-medium" style={{ color: '#e6edf3' }}>{level.name}</h3>
                      <p className="text-xs" style={{ color: '#7d8590' }}>ID: {level.permission_id}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => {
                        setSelectedLevel(level);
                        setModalOpen(true);
                      }}
                      className="p-2 rounded-md transition-colors"
                      style={{ color: '#7d8590' }}
                    >
                      <Edit2 size={14} />
                    </button>
                    <button
                      onClick={() => handleDelete(level.permission_id)}
                      className="p-2 rounded-md transition-colors"
                      style={{ color: '#7d8590' }}
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                </div>
              </div>
              <div className="p-4">
                {level.description && (
                  <p className="text-sm mb-4" style={{ color: '#7d8590' }}>{level.description}</p>
                )}
                <div>
                  <p className="text-xs uppercase tracking-wide mb-2" style={{ color: '#484f58' }}>Doors</p>
                  {level.doors && level.doors.length > 0 ? (
                    <div className="flex flex-wrap gap-2">
                      {level.doors.map((doorId) => {
                        const door = doors.find((d) => d.door_id === doorId);
                        return (
                          <span
                            key={doorId}
                            className="px-2 py-1 rounded text-xs"
                            style={{ background: 'rgba(139, 92, 246, 0.15)', color: '#8b5cf6' }}
                          >
                            {door?.name || `Door ${doorId}`}
                          </span>
                        );
                      })}
                    </div>
                  ) : (
                    <p className="text-sm" style={{ color: '#7d8590' }}>No doors assigned</p>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      <AccessLevelModal
        isOpen={modalOpen}
        onClose={() => {
          setModalOpen(false);
          setSelectedLevel(null);
        }}
        onSave={handleSave}
        accessLevel={selectedLevel}
        doors={doors}
      />
    </div>
  );
}
