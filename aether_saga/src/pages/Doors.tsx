/**
 * Doors - Situ8-style Door Management
 */

import { useEffect, useState } from 'react';
import { Plus, Edit2, Trash2, DoorOpen, Lock, Unlock, X } from 'lucide-react';
import { doorsApi } from '../api/bifrost';
import { READER_MODE_NAMES } from '../types';
import type { Door } from '../types';

// DEMO MODE
const DEMO_MODE = true;
const MOCK_DOORS: Door[] = [
  { door_id: 1, name: 'Main Entrance', strike_time_ms: 5000, reader_mode: 5, osdp_enabled: true },
  { door_id: 2, name: 'Side Entrance', strike_time_ms: 3000, reader_mode: 5, osdp_enabled: true },
  { door_id: 3, name: 'Server Room', strike_time_ms: 2000, reader_mode: 7, osdp_enabled: true },
  { door_id: 4, name: 'Parking Garage', strike_time_ms: 8000, reader_mode: 5, osdp_enabled: false },
  { door_id: 5, name: 'Emergency Exit', strike_time_ms: 5000, reader_mode: 3, osdp_enabled: false },
  { door_id: 6, name: 'Loading Dock', strike_time_ms: 10000, reader_mode: 5, osdp_enabled: true },
];

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
    <div className="fixed inset-0 flex items-center justify-center z-50" style={{ background: 'rgba(0, 0, 0, 0.7)' }}>
      <div
        className="w-full max-w-lg mx-4 rounded-md"
        style={{ background: '#161b22', border: '1px solid #30363d' }}
      >
        <div
          className="flex items-center justify-between px-6 py-4"
          style={{ borderBottom: '1px solid #30363d' }}
        >
          <h2 className="text-lg font-semibold" style={{ color: '#e6edf3' }}>
            {door ? 'Edit Door' : 'Add Door'}
          </h2>
          <button
            onClick={onClose}
            className="p-2 rounded-md transition-colors"
            style={{ color: '#7d8590' }}
          >
            <X size={18} />
          </button>
        </div>
        <form onSubmit={handleSubmit} className="p-6 space-y-5">
          <div>
            <label className="block text-xs mb-1.5" style={{ color: '#7d8590' }}>Door ID</label>
            <input
              type="number"
              required
              className="w-full rounded-md px-4 py-2.5 focus:outline-none"
              style={{ background: '#0d1117', border: '1px solid #30363d', color: '#e6edf3' }}
              value={formData.door_id || ''}
              onChange={(e) => setFormData({ ...formData, door_id: parseInt(e.target.value) })}
              disabled={!!door}
            />
          </div>

          <div>
            <label className="block text-xs mb-1.5" style={{ color: '#7d8590' }}>Door Name *</label>
            <input
              type="text"
              required
              className="w-full rounded-md px-4 py-2.5 focus:outline-none"
              style={{ background: '#0d1117', border: '1px solid #30363d', color: '#e6edf3' }}
              value={formData.name || ''}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="e.g., Main Entrance"
            />
          </div>

          <div>
            <label className="block text-xs mb-1.5" style={{ color: '#7d8590' }}>Strike Duration (ms)</label>
            <input
              type="number"
              className="w-full rounded-md px-4 py-2.5 focus:outline-none"
              style={{ background: '#0d1117', border: '1px solid #30363d', color: '#e6edf3' }}
              value={formData.strike_time_ms || 3000}
              onChange={(e) => setFormData({ ...formData, strike_time_ms: parseInt(e.target.value) })}
              min={500}
              max={30000}
              step={500}
            />
            <p className="text-xs mt-1" style={{ color: '#484f58' }}>How long the door remains unlocked (500-30000ms)</p>
          </div>

          <div>
            <label className="block text-xs mb-1.5" style={{ color: '#7d8590' }}>Reader Mode</label>
            <select
              className="w-full rounded-md px-4 py-2.5 focus:outline-none"
              style={{ background: '#0d1117', border: '1px solid #30363d', color: '#e6edf3' }}
              value={formData.reader_mode || 5}
              onChange={(e) => setFormData({ ...formData, reader_mode: parseInt(e.target.value) })}
            >
              {Object.entries(READER_MODE_NAMES).map(([id, name]) => (
                <option key={id} value={id}>{name}</option>
              ))}
            </select>
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
    if (DEMO_MODE) {
      setDoors(MOCK_DOORS);
      setLoading(false);
      return;
    }
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
              style={{ background: '#22c55e' }}
            />
            <h1 className="text-xl font-semibold" style={{ color: '#e6edf3' }}>
              Doors
            </h1>
          </div>
          <p className="text-sm" style={{ color: '#7d8590' }}>
            Manage door readers and access points
          </p>
        </div>
        <button
          onClick={() => {
            setSelectedDoor(null);
            setModalOpen(true);
          }}
          className="flex items-center gap-2 px-4 py-2 rounded-md font-medium transition-colors"
          style={{ background: '#238636', color: '#ffffff' }}
        >
          <Plus size={18} />
          Add Door
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-md" style={{ background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)' }}>
          <p style={{ color: '#ef4444' }}>{error}</p>
        </div>
      )}

      {/* Door Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {doors.length === 0 ? (
          <div className="col-span-full p-8 text-center rounded-md" style={{ background: '#161b22', border: '1px solid #30363d' }}>
            <DoorOpen size={48} className="mx-auto mb-4" style={{ color: '#7d8590' }} />
            <p style={{ color: '#7d8590' }}>No doors configured</p>
            <button
              onClick={() => setModalOpen(true)}
              className="mt-4"
              style={{ color: '#58a6ff' }}
            >
              Add your first door
            </button>
          </div>
        ) : (
          doors.map((door) => {
            const isUnlocking = unlocking === door.door_id;
            const readerMode = door.reader_mode || 5;

            return (
              <div
                key={door.door_id}
                className="rounded-md overflow-hidden transition-colors"
                style={{ background: '#161b22', border: '1px solid #30363d' }}
              >
                {/* Door Header */}
                <div className="px-4 py-3" style={{ borderBottom: '1px solid #30363d' }}>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div
                        className="w-10 h-10 rounded-md flex items-center justify-center transition-colors"
                        style={{
                          background: isUnlocking ? 'rgba(34, 197, 94, 0.15)' : 'rgba(139, 92, 246, 0.15)',
                          color: isUnlocking ? '#22c55e' : '#8b5cf6'
                        }}
                      >
                        {isUnlocking ? <Unlock size={20} /> : <DoorOpen size={20} />}
                      </div>
                      <div>
                        <h3 className="font-medium" style={{ color: '#e6edf3' }}>{door.name}</h3>
                        <p className="text-xs" style={{ color: '#7d8590' }}>Door {door.door_id}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-1">
                      <button
                        onClick={() => {
                          setSelectedDoor(door);
                          setModalOpen(true);
                        }}
                        className="p-2 rounded-md transition-colors"
                        style={{ color: '#7d8590' }}
                      >
                        <Edit2 size={14} />
                      </button>
                      <button
                        onClick={() => handleDelete(door.door_id)}
                        className="p-2 rounded-md transition-colors"
                        style={{ color: '#7d8590' }}
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </div>
                </div>

                <div className="p-4 space-y-4">
                  {/* Door Info */}
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <p className="text-xs" style={{ color: '#7d8590' }}>Strike Time</p>
                      <p style={{ color: '#e6edf3' }}>{door.strike_time_ms}ms</p>
                    </div>
                    <div>
                      <p className="text-xs" style={{ color: '#7d8590' }}>Reader Mode</p>
                      <p style={{ color: '#e6edf3' }}>{READER_MODE_NAMES[readerMode] || 'Unknown'}</p>
                    </div>
                  </div>

                  {/* Main Control */}
                  <button
                    onClick={() => isUnlocking ? handleLock(door.door_id) : handleUnlock(door.door_id)}
                    className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-md font-medium transition-colors"
                    style={{
                      background: isUnlocking ? 'rgba(34, 197, 94, 0.15)' : 'rgba(139, 92, 246, 0.15)',
                      border: isUnlocking ? '1px solid rgba(34, 197, 94, 0.3)' : '1px solid rgba(139, 92, 246, 0.3)',
                      color: isUnlocking ? '#22c55e' : '#8b5cf6'
                    }}
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

                  {/* Mode Buttons */}
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleSetMode(door.door_id, 2)}
                      className="flex-1 px-3 py-2 rounded-md text-xs font-medium transition-colors"
                      style={{
                        background: readerMode === 2 ? 'rgba(34, 197, 94, 0.15)' : '#0d1117',
                        border: readerMode === 2 ? '1px solid rgba(34, 197, 94, 0.3)' : '1px solid #30363d',
                        color: readerMode === 2 ? '#22c55e' : '#7d8590'
                      }}
                    >
                      Unlocked
                    </button>
                    <button
                      onClick={() => handleSetMode(door.door_id, 5)}
                      className="flex-1 px-3 py-2 rounded-md text-xs font-medium transition-colors"
                      style={{
                        background: readerMode === 5 ? 'rgba(139, 92, 246, 0.15)' : '#0d1117',
                        border: readerMode === 5 ? '1px solid rgba(139, 92, 246, 0.3)' : '1px solid #30363d',
                        color: readerMode === 5 ? '#8b5cf6' : '#7d8590'
                      }}
                    >
                      Card Only
                    </button>
                    <button
                      onClick={() => handleSetMode(door.door_id, 10)}
                      className="flex-1 px-3 py-2 rounded-md text-xs font-medium transition-colors"
                      style={{
                        background: readerMode === 10 ? 'rgba(239, 68, 68, 0.15)' : '#0d1117',
                        border: readerMode === 10 ? '1px solid rgba(239, 68, 68, 0.3)' : '1px solid #30363d',
                        color: readerMode === 10 ? '#ef4444' : '#7d8590'
                      }}
                    >
                      Locked
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
