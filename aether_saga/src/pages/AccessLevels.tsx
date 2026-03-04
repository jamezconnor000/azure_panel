import { useEffect, useState } from 'react';
import { Plus, Edit2, Trash2, Key, DoorOpen } from 'lucide-react';
import { accessLevelsApi, doorsApi } from '../api/bifrost';
import type { AccessLevel, Door } from '../types';

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
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="glass rounded-xl w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto">
        <div className="px-6 py-4 border-b border-white/10">
          <h2 className="text-lg font-semibold text-white">
            {accessLevel ? 'Edit Access Level' : 'Add Access Level'}
          </h2>
        </div>
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-sm text-gray-400 mb-1">Permission ID</label>
            <input
              type="number"
              required
              className="w-full bg-aether-darker border border-white/10 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-aether-primary"
              value={formData.permission_id || ''}
              onChange={(e) => setFormData({ ...formData, permission_id: parseInt(e.target.value) })}
              disabled={!!accessLevel}
            />
          </div>

          <div>
            <label className="block text-sm text-gray-400 mb-1">Name *</label>
            <input
              type="text"
              required
              className="w-full bg-aether-darker border border-white/10 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-aether-primary"
              value={formData.name || ''}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            />
          </div>

          <div>
            <label className="block text-sm text-gray-400 mb-1">Description</label>
            <textarea
              className="w-full bg-aether-darker border border-white/10 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-aether-primary"
              value={formData.description || ''}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              rows={3}
            />
          </div>

          <div>
            <label className="block text-sm text-gray-400 mb-2">Doors</label>
            <div className="space-y-2 max-h-48 overflow-y-auto">
              {doors.length === 0 ? (
                <p className="text-gray-500 text-sm">No doors available</p>
              ) : (
                doors.map((door) => (
                  <label
                    key={door.door_id}
                    className="flex items-center gap-3 p-3 rounded-lg bg-aether-darker hover:bg-white/5 cursor-pointer"
                  >
                    <input
                      type="checkbox"
                      checked={formData.doors?.includes(door.door_id) || false}
                      onChange={() => toggleDoor(door.door_id)}
                      className="rounded border-white/10 bg-aether-darker text-aether-primary focus:ring-aether-primary"
                    />
                    <DoorOpen size={16} className="text-gray-400" />
                    <span className="text-white">{door.name}</span>
                    <span className="text-gray-500 text-sm ml-auto">ID: {door.door_id}</span>
                  </label>
                ))
              )}
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-lg border border-white/10 text-gray-300 hover:bg-white/5"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 rounded-lg bg-aether-primary text-aether-darker font-medium hover:bg-aether-primary/90"
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
        // For updates, we need to delete and re-create since HAL doesn't have update
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
        <div className="animate-spin rounded-full h-8 w-8 border-2 border-aether-primary border-t-transparent"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">Access Levels</h1>
          <p className="text-gray-400">Manage permission groups and door access</p>
        </div>
        <button
          onClick={() => {
            setSelectedLevel(null);
            setModalOpen(true);
          }}
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-aether-primary text-aether-darker font-medium hover:bg-aether-primary/90"
        >
          <Plus size={20} />
          Add Access Level
        </button>
      </div>

      {error && (
        <div className="glass rounded-xl p-4 border border-aether-danger/30">
          <p className="text-aether-danger">{error}</p>
        </div>
      )}

      {/* Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {accessLevels.length === 0 ? (
          <div className="col-span-full glass rounded-xl p-8 text-center">
            <Key size={48} className="mx-auto text-gray-500 mb-4" />
            <p className="text-gray-400">No access levels configured</p>
            <button
              onClick={() => setModalOpen(true)}
              className="mt-4 text-aether-primary hover:underline"
            >
              Add your first access level
            </button>
          </div>
        ) : (
          accessLevels.map((level) => (
            <div key={level.permission_id} className="glass rounded-xl overflow-hidden">
              <div className="px-6 py-4 border-b border-white/10">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-aether-secondary/20 flex items-center justify-center">
                      <Key size={20} className="text-aether-secondary" />
                    </div>
                    <div>
                      <h3 className="text-white font-medium">{level.name}</h3>
                      <p className="text-gray-400 text-sm">ID: {level.permission_id}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => {
                        setSelectedLevel(level);
                        setModalOpen(true);
                      }}
                      className="p-2 rounded-lg hover:bg-white/10 text-gray-400 hover:text-white"
                    >
                      <Edit2 size={16} />
                    </button>
                    <button
                      onClick={() => handleDelete(level.permission_id)}
                      className="p-2 rounded-lg hover:bg-white/10 text-gray-400 hover:text-aether-danger"
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                </div>
              </div>
              <div className="px-6 py-4">
                {level.description && (
                  <p className="text-gray-400 text-sm mb-4">{level.description}</p>
                )}
                <div>
                  <p className="text-gray-500 text-xs uppercase tracking-wide mb-2">Doors</p>
                  {level.doors && level.doors.length > 0 ? (
                    <div className="flex flex-wrap gap-2">
                      {level.doors.map((doorId) => {
                        const door = doors.find((d) => d.door_id === doorId);
                        return (
                          <span
                            key={doorId}
                            className="px-2 py-1 rounded bg-aether-primary/10 text-aether-primary text-sm"
                          >
                            {door?.name || `Door ${doorId}`}
                          </span>
                        );
                      })}
                    </div>
                  ) : (
                    <p className="text-gray-500 text-sm">No doors assigned</p>
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
