import { useEffect, useState } from 'react';
import { Plus, Edit2, Trash2, DoorOpen, Lock, Unlock } from 'lucide-react';
import { doorsApi } from '../api/bifrost';
import { READER_MODE_NAMES } from '../types';
import type { Door } from '../types';

function DoorModal({
  isOpen,
  onClose,
  onSave,
  door,
}: {
  isOpen: boolean;
  onClose: () => void;
  onSave: (data: Partial<Door>) => void;
  door?: Door | null;
}) {
  const [formData, setFormData] = useState<Partial<Door>>({
    door_id: 0,
    name: '',
    strike_time_ms: 3000,
    reader_mode: 5,
  });

  useEffect(() => {
    if (door) {
      setFormData(door);
    } else {
      setFormData({
        door_id: Math.floor(Math.random() * 100) + 1,
        name: '',
        strike_time_ms: 3000,
        reader_mode: 5,
      });
    }
  }, [door, isOpen]);

  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave(formData);
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="glass rounded-xl w-full max-w-lg mx-4">
        <div className="px-6 py-4 border-b border-white/10">
          <h2 className="text-lg font-semibold text-white">
            {door ? 'Edit Door' : 'Add Door'}
          </h2>
        </div>
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-sm text-gray-400 mb-1">Door ID</label>
            <input
              type="number"
              required
              className="w-full bg-aether-darker border border-white/10 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-aether-primary"
              value={formData.door_id || ''}
              onChange={(e) => setFormData({ ...formData, door_id: parseInt(e.target.value) })}
              disabled={!!door}
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
              placeholder="e.g., Main Entrance"
            />
          </div>

          <div>
            <label className="block text-sm text-gray-400 mb-1">Strike Time (ms)</label>
            <input
              type="number"
              className="w-full bg-aether-darker border border-white/10 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-aether-primary"
              value={formData.strike_time_ms || 3000}
              onChange={(e) => setFormData({ ...formData, strike_time_ms: parseInt(e.target.value) })}
              min={500}
              max={30000}
              step={500}
            />
            <p className="text-gray-500 text-xs mt-1">How long the door unlocks (500-30000ms)</p>
          </div>

          <div>
            <label className="block text-sm text-gray-400 mb-1">Reader Mode</label>
            <select
              className="w-full bg-aether-darker border border-white/10 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-aether-primary"
              value={formData.reader_mode || 5}
              onChange={(e) => setFormData({ ...formData, reader_mode: parseInt(e.target.value) })}
            >
              {Object.entries(READER_MODE_NAMES).map(([id, name]) => (
                <option key={id} value={id}>{name}</option>
              ))}
            </select>
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
              {door ? 'Save Changes' : 'Add Door'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export function Doors() {
  const [doors, setDoors] = useState<Door[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [selectedDoor, setSelectedDoor] = useState<Door | null>(null);
  const [unlocking, setUnlocking] = useState<number | null>(null);

  const fetchData = async () => {
    try {
      setLoading(true);
      const data = await doorsApi.list();
      setDoors(data.doors || []);
      setError(null);
    } catch (err) {
      setError('Failed to load doors');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleSave = async (data: Partial<Door>) => {
    try {
      if (selectedDoor) {
        // For updates, delete and re-create
        await doorsApi.delete(selectedDoor.door_id);
        await doorsApi.create(data);
      } else {
        await doorsApi.create(data);
      }
      setModalOpen(false);
      setSelectedDoor(null);
      fetchData();
    } catch (err) {
      console.error('Failed to save door:', err);
    }
  };

  const handleDelete = async (doorId: number) => {
    if (!confirm('Are you sure you want to delete this door?')) return;
    try {
      await doorsApi.delete(doorId);
      fetchData();
    } catch (err) {
      console.error('Failed to delete door:', err);
    }
  };

  const handleUnlock = async (doorId: number) => {
    try {
      setUnlocking(doorId);
      await doorsApi.unlock(doorId, 5);
      // Visual feedback - the unlock button will show as active for 5 seconds
      setTimeout(() => setUnlocking(null), 5000);
    } catch (err) {
      console.error('Failed to unlock door:', err);
      setUnlocking(null);
    }
  };

  const handleLock = async (doorId: number) => {
    try {
      await doorsApi.lock(doorId);
      setUnlocking(null);
    } catch (err) {
      console.error('Failed to lock door:', err);
    }
  };

  const handleSetMode = async (doorId: number, mode: number) => {
    try {
      await doorsApi.setReaderMode(doorId, mode);
      fetchData();
    } catch (err) {
      console.error('Failed to set reader mode:', err);
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
          <h1 className="text-2xl font-bold text-white">Doors</h1>
          <p className="text-gray-400">Manage door readers and access points</p>
        </div>
        <button
          onClick={() => {
            setSelectedDoor(null);
            setModalOpen(true);
          }}
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-aether-primary text-aether-darker font-medium hover:bg-aether-primary/90"
        >
          <Plus size={20} />
          Add Door
        </button>
      </div>

      {error && (
        <div className="glass rounded-xl p-4 border border-aether-danger/30">
          <p className="text-aether-danger">{error}</p>
        </div>
      )}

      {/* Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {doors.length === 0 ? (
          <div className="col-span-full glass rounded-xl p-8 text-center">
            <DoorOpen size={48} className="mx-auto text-gray-500 mb-4" />
            <p className="text-gray-400">No doors configured</p>
            <button
              onClick={() => setModalOpen(true)}
              className="mt-4 text-aether-primary hover:underline"
            >
              Add your first door
            </button>
          </div>
        ) : (
          doors.map((door) => {
            const isUnlocking = unlocking === door.door_id;
            const readerMode = door.reader_mode || 5;

            return (
              <div key={door.door_id} className="glass rounded-xl overflow-hidden">
                <div className="px-6 py-4 border-b border-white/10">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${isUnlocking ? 'bg-aether-success/20' : 'bg-aether-primary/20'}`}>
                        {isUnlocking ? (
                          <Unlock size={24} className="text-aether-success" />
                        ) : (
                          <DoorOpen size={24} className="text-aether-primary" />
                        )}
                      </div>
                      <div>
                        <h3 className="text-white font-medium">{door.name}</h3>
                        <p className="text-gray-400 text-sm">Door {door.door_id}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-1">
                      <button
                        onClick={() => {
                          setSelectedDoor(door);
                          setModalOpen(true);
                        }}
                        className="p-2 rounded-lg hover:bg-white/10 text-gray-400 hover:text-white"
                      >
                        <Edit2 size={16} />
                      </button>
                      <button
                        onClick={() => handleDelete(door.door_id)}
                        className="p-2 rounded-lg hover:bg-white/10 text-gray-400 hover:text-aether-danger"
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </div>
                </div>

                <div className="px-6 py-4 space-y-4">
                  {/* Door Info */}
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <p className="text-gray-500">Strike Time</p>
                      <p className="text-white">{door.strike_time_ms}ms</p>
                    </div>
                    <div>
                      <p className="text-gray-500">Reader Mode</p>
                      <p className="text-white">{READER_MODE_NAMES[readerMode] || 'Unknown'}</p>
                    </div>
                  </div>

                  {/* Controls */}
                  <div className="flex gap-2">
                    <button
                      onClick={() => isUnlocking ? handleLock(door.door_id) : handleUnlock(door.door_id)}
                      className={`flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors ${
                        isUnlocking
                          ? 'bg-aether-success text-white'
                          : 'bg-aether-primary/20 text-aether-primary hover:bg-aether-primary/30'
                      }`}
                    >
                      {isUnlocking ? (
                        <>
                          <Lock size={16} />
                          Lock
                        </>
                      ) : (
                        <>
                          <Unlock size={16} />
                          Unlock
                        </>
                      )}
                    </button>
                  </div>

                  {/* Quick Mode Buttons */}
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleSetMode(door.door_id, 2)}
                      className={`flex-1 px-3 py-1.5 rounded text-xs font-medium ${
                        readerMode === 2
                          ? 'bg-aether-success/20 text-aether-success'
                          : 'bg-white/5 text-gray-400 hover:bg-white/10'
                      }`}
                    >
                      Unlocked
                    </button>
                    <button
                      onClick={() => handleSetMode(door.door_id, 5)}
                      className={`flex-1 px-3 py-1.5 rounded text-xs font-medium ${
                        readerMode === 5
                          ? 'bg-aether-primary/20 text-aether-primary'
                          : 'bg-white/5 text-gray-400 hover:bg-white/10'
                      }`}
                    >
                      Card Only
                    </button>
                    <button
                      onClick={() => handleSetMode(door.door_id, 10)}
                      className={`flex-1 px-3 py-1.5 rounded text-xs font-medium ${
                        readerMode === 10
                          ? 'bg-aether-danger/20 text-aether-danger'
                          : 'bg-white/5 text-gray-400 hover:bg-white/10'
                      }`}
                    >
                      Blocked
                    </button>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>

      <DoorModal
        isOpen={modalOpen}
        onClose={() => {
          setModalOpen(false);
          setSelectedDoor(null);
        }}
        onSave={handleSave}
        door={selectedDoor}
      />
    </div>
  );
}
