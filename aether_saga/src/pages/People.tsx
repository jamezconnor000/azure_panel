/**
 * People - Situ8-style Cardholder Management
 */

import { useEffect, useState } from 'react';
import {
  Plus, Search, Edit2, Trash2, User, Key, ChevronRight,
  CheckCircle, XCircle, Activity, DoorOpen, Download,
  MoreHorizontal, X
} from 'lucide-react';
import type { CardHolder, AccessLevel, Door } from '../types';

// ============================================================================
// MOCK DATA
// ============================================================================

const MOCK_CARDHOLDERS: CardHolder[] = [
  { id: 1, card_number: 'A1B2C3D4', first_name: 'Erik', last_name: 'Bloodaxe', email: 'erik@company.com', phone: '555-0101', department: 'Security', employee_id: 'EMP001', is_active: true, activation_date: 0, expiration_date: 0, created_at: 0, updated_at: 0 },
  { id: 2, card_number: 'E5F6G7H8', first_name: 'Sarah', last_name: 'Mitchell', email: 'sarah@company.com', phone: '555-0102', department: 'Administration', employee_id: 'EMP002', is_active: true, activation_date: 0, expiration_date: 0, created_at: 0, updated_at: 0 },
  { id: 3, card_number: 'I9J0K1L2', first_name: 'James', last_name: 'Thompson', email: 'james@company.com', phone: '555-0103', department: 'Engineering', employee_id: 'EMP003', is_active: true, activation_date: 0, expiration_date: 0, created_at: 0, updated_at: 0 },
  { id: 4, card_number: 'M3N4O5P6', first_name: 'Michael', last_name: 'Rodriguez', email: 'michael@company.com', phone: '555-0104', department: 'Research', employee_id: 'EMP004', is_active: false, activation_date: 0, expiration_date: 0, created_at: 0, updated_at: 0 },
  { id: 5, card_number: 'Q7R8S9T0', first_name: 'Lisa', last_name: 'Kim', email: 'lisa@company.com', phone: '555-0105', department: 'Operations', employee_id: 'EMP005', is_active: true, activation_date: 0, expiration_date: 0, created_at: 0, updated_at: 0 },
  { id: 6, card_number: 'U1V2W3X4', first_name: 'David', last_name: 'Chen', email: 'david@company.com', phone: '555-0106', department: 'Security', employee_id: 'EMP006', is_active: true, activation_date: 0, expiration_date: 0, created_at: 0, updated_at: 0 },
  { id: 7, card_number: 'Y5Z6A7B8', first_name: 'Amanda', last_name: 'Foster', email: 'amanda@company.com', phone: '555-0107', department: 'Legal', employee_id: 'EMP007', is_active: true, activation_date: 0, expiration_date: 0, created_at: 0, updated_at: 0 },
  { id: 8, card_number: 'EXPIRED01', first_name: 'Robert', last_name: 'Johnson', email: 'robert@company.com', phone: '555-0108', department: 'Executive', employee_id: 'EMP008', is_active: false, activation_date: 0, expiration_date: 0, created_at: 0, updated_at: 0 },
];

const MOCK_ACCESS_LEVELS: AccessLevel[] = [
  { id: 1, permission_id: 1, name: 'All Access', description: 'Full facility access', doors: [1, 2, 3, 4, 5, 6, 7, 8], priority: 1, is_active: true },
  { id: 2, permission_id: 2, name: 'Standard Employee', description: 'Common areas only', doors: [1, 2, 4], priority: 2, is_active: true },
  { id: 3, permission_id: 3, name: 'Server Room', description: 'IT and server room access', doors: [1, 2, 3], priority: 3, is_active: true },
  { id: 4, permission_id: 4, name: 'Executive', description: 'Executive suite access', doors: [1, 2, 7], priority: 4, is_active: true },
  { id: 5, permission_id: 5, name: 'Visitor', description: 'Main entrance only', doors: [1], priority: 5, is_active: true },
];

const MOCK_DOORS: Door[] = [
  { door_id: 1, name: 'Main Entrance', strike_time_ms: 5000 },
  { door_id: 2, name: 'Side Entrance', strike_time_ms: 5000 },
  { door_id: 3, name: 'Server Room', strike_time_ms: 3000 },
  { door_id: 4, name: 'Parking Garage', strike_time_ms: 10000 },
  { door_id: 5, name: 'Emergency Exit', strike_time_ms: 0 },
  { door_id: 6, name: 'Loading Dock', strike_time_ms: 15000 },
  { door_id: 7, name: 'Executive Suite', strike_time_ms: 5000 },
  { door_id: 8, name: 'Lab Access', strike_time_ms: 5000 },
];

// ============================================================================
// CARDHOLDER MODAL
// ============================================================================

function CardholderModal({
  isOpen,
  onClose,
  onSave,
  cardholder,
}: {
  isOpen: boolean;
  onClose: () => void;
  onSave: (data: Partial<CardHolder>) => void;
  cardholder?: CardHolder | null;
}) {
  const [formData, setFormData] = useState<Partial<CardHolder>>({
    card_number: '',
    first_name: '',
    last_name: '',
    email: '',
    phone: '',
    department: '',
    employee_id: '',
    is_active: true,
  });

  useEffect(() => {
    if (cardholder) {
      setFormData(cardholder);
    } else {
      setFormData({
        card_number: '',
        first_name: '',
        last_name: '',
        email: '',
        phone: '',
        department: '',
        employee_id: '',
        is_active: true,
      });
    }
  }, [cardholder, isOpen]);

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
            {cardholder ? 'Edit Cardholder' : 'Add Cardholder'}
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
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs mb-1.5" style={{ color: '#7d8590' }}>First Name *</label>
              <input
                type="text"
                required
                className="w-full rounded-md px-4 py-2.5 focus:outline-none"
                style={{ background: '#0d1117', border: '1px solid #30363d', color: '#e6edf3' }}
                value={formData.first_name || ''}
                onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
              />
            </div>
            <div>
              <label className="block text-xs mb-1.5" style={{ color: '#7d8590' }}>Last Name *</label>
              <input
                type="text"
                required
                className="w-full rounded-md px-4 py-2.5 focus:outline-none"
                style={{ background: '#0d1117', border: '1px solid #30363d', color: '#e6edf3' }}
                value={formData.last_name || ''}
                onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
              />
            </div>
          </div>

          <div>
            <label className="block text-xs mb-1.5" style={{ color: '#7d8590' }}>Card Number *</label>
            <input
              type="text"
              required
              className="w-full rounded-md px-4 py-2.5 font-mono focus:outline-none"
              style={{ background: '#0d1117', border: '1px solid #30363d', color: '#e6edf3' }}
              value={formData.card_number || ''}
              onChange={(e) => setFormData({ ...formData, card_number: e.target.value })}
              disabled={!!cardholder}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs mb-1.5" style={{ color: '#7d8590' }}>Email</label>
              <input
                type="email"
                className="w-full rounded-md px-4 py-2.5 focus:outline-none"
                style={{ background: '#0d1117', border: '1px solid #30363d', color: '#e6edf3' }}
                value={formData.email || ''}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              />
            </div>
            <div>
              <label className="block text-xs mb-1.5" style={{ color: '#7d8590' }}>Phone</label>
              <input
                type="tel"
                className="w-full rounded-md px-4 py-2.5 focus:outline-none"
                style={{ background: '#0d1117', border: '1px solid #30363d', color: '#e6edf3' }}
                value={formData.phone || ''}
                onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs mb-1.5" style={{ color: '#7d8590' }}>Department</label>
              <input
                type="text"
                className="w-full rounded-md px-4 py-2.5 focus:outline-none"
                style={{ background: '#0d1117', border: '1px solid #30363d', color: '#e6edf3' }}
                value={formData.department || ''}
                onChange={(e) => setFormData({ ...formData, department: e.target.value })}
              />
            </div>
            <div>
              <label className="block text-xs mb-1.5" style={{ color: '#7d8590' }}>Employee ID</label>
              <input
                type="text"
                className="w-full rounded-md px-4 py-2.5 focus:outline-none"
                style={{ background: '#0d1117', border: '1px solid #30363d', color: '#e6edf3' }}
                value={formData.employee_id || ''}
                onChange={(e) => setFormData({ ...formData, employee_id: e.target.value })}
              />
            </div>
          </div>

          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="is_active"
              checked={formData.is_active}
              onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
              className="w-4 h-4 rounded"
            />
            <label htmlFor="is_active" className="text-sm" style={{ color: '#7d8590' }}>Active</label>
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
              {cardholder ? 'Save Changes' : 'Add Cardholder'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ============================================================================
// DETAIL PANEL
// ============================================================================

function DetailPanel({
  cardholder,
  accessLevels,
  doors,
  onClose,
  onEdit,
}: {
  cardholder: CardHolder | null;
  accessLevels: AccessLevel[];
  doors: Door[];
  onClose: () => void;
  onEdit: () => void;
}) {
  if (!cardholder) return null;

  const assignedLevel = accessLevels[Math.floor(Math.random() * accessLevels.length)];
  const accessibleDoors = doors.filter(d => assignedLevel?.doors?.includes(d.door_id));

  return (
    <div
      className="fixed right-0 top-0 bottom-0 w-[400px] z-40 overflow-y-auto"
      style={{ background: '#161b22', borderLeft: '1px solid #30363d' }}
    >
      {/* Header */}
      <div
        className="sticky top-0 p-4 z-10"
        style={{ background: '#161b22', borderBottom: '1px solid #30363d' }}
      >
        <div className="flex items-center justify-between">
          <h3 className="font-semibold" style={{ color: '#e6edf3' }}>Cardholder Details</h3>
          <button
            onClick={onClose}
            className="p-2 rounded-md transition-colors"
            style={{ color: '#7d8590' }}
          >
            <X size={18} />
          </button>
        </div>
      </div>

      <div className="p-4 space-y-4">
        {/* Profile Card */}
        <div className="p-4 rounded-md" style={{ background: '#21262d' }}>
          <div className="flex items-center gap-4 mb-4">
            <div
              className="w-14 h-14 rounded-md flex items-center justify-center text-lg font-semibold"
              style={{
                background: cardholder.is_active ? 'rgba(139, 92, 246, 0.15)' : '#21262d',
                color: cardholder.is_active ? '#8b5cf6' : '#7d8590'
              }}
            >
              {cardholder.first_name[0]}{cardholder.last_name[0]}
            </div>
            <div className="flex-1">
              <h4 className="font-semibold" style={{ color: '#e6edf3' }}>
                {cardholder.first_name} {cardholder.last_name}
              </h4>
              <p className="text-sm" style={{ color: '#7d8590' }}>{cardholder.department || 'No department'}</p>
              <span
                className="inline-flex items-center gap-1.5 mt-1.5 px-2 py-0.5 rounded text-xs"
                style={{
                  background: cardholder.is_active ? 'rgba(34, 197, 94, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                  color: cardholder.is_active ? '#22c55e' : '#ef4444'
                }}
              >
                {cardholder.is_active ? <CheckCircle size={10} /> : <XCircle size={10} />}
                {cardholder.is_active ? 'Active' : 'Inactive'}
              </span>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="p-3 rounded-md" style={{ background: '#0d1117' }}>
              <p className="text-xs" style={{ color: '#484f58' }}>Card Number</p>
              <p className="font-mono text-sm mt-1" style={{ color: '#e6edf3' }}>{cardholder.card_number}</p>
            </div>
            <div className="p-3 rounded-md" style={{ background: '#0d1117' }}>
              <p className="text-xs" style={{ color: '#484f58' }}>Employee ID</p>
              <p className="text-sm mt-1" style={{ color: '#e6edf3' }}>{cardholder.employee_id || '-'}</p>
            </div>
          </div>

          {cardholder.email && (
            <div className="mt-3 p-3 rounded-md" style={{ background: '#0d1117' }}>
              <p className="text-xs" style={{ color: '#484f58' }}>Email</p>
              <p className="text-sm mt-1" style={{ color: '#e6edf3' }}>{cardholder.email}</p>
            </div>
          )}
        </div>

        {/* Access Level */}
        <div className="p-4 rounded-md" style={{ background: '#21262d' }}>
          <div className="flex items-center justify-between mb-3">
            <h4 className="text-sm font-medium flex items-center gap-2" style={{ color: '#e6edf3' }}>
              <Key size={14} style={{ color: '#7d8590' }} />
              Access Level
            </h4>
            <button className="text-xs" style={{ color: '#58a6ff' }}>Change</button>
          </div>
          <div
            className="p-3 rounded-md"
            style={{ background: 'rgba(249, 115, 22, 0.1)', border: '1px solid rgba(249, 115, 22, 0.3)' }}
          >
            <p className="font-medium" style={{ color: '#f97316' }}>{assignedLevel?.name || 'No Access'}</p>
            <p className="text-xs mt-1" style={{ color: '#7d8590' }}>{assignedLevel?.description}</p>
          </div>
        </div>

        {/* Door Access */}
        <div className="p-4 rounded-md" style={{ background: '#21262d' }}>
          <h4 className="text-sm font-medium flex items-center gap-2 mb-3" style={{ color: '#e6edf3' }}>
            <DoorOpen size={14} style={{ color: '#7d8590' }} />
            Accessible Doors ({accessibleDoors.length})
          </h4>
          <div className="space-y-2">
            {accessibleDoors.map(door => (
              <div key={door.door_id} className="flex items-center gap-2 p-2 rounded" style={{ background: '#0d1117' }}>
                <DoorOpen size={14} style={{ color: '#7d8590' }} />
                <span className="text-sm" style={{ color: '#e6edf3' }}>{door.name}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Recent Activity */}
        <div className="p-4 rounded-md" style={{ background: '#21262d' }}>
          <h4 className="text-sm font-medium flex items-center gap-2 mb-3" style={{ color: '#e6edf3' }}>
            <Activity size={14} style={{ color: '#7d8590' }} />
            Recent Activity
          </h4>
          <div className="space-y-2">
            <div className="flex items-center justify-between p-2 rounded" style={{ background: 'rgba(34, 197, 94, 0.05)' }}>
              <div className="flex items-center gap-2">
                <CheckCircle size={12} style={{ color: '#22c55e' }} />
                <span className="text-xs" style={{ color: '#e6edf3' }}>Main Entrance</span>
              </div>
              <span className="text-xs" style={{ color: '#7d8590' }}>2m ago</span>
            </div>
            <div className="flex items-center justify-between p-2 rounded" style={{ background: 'rgba(34, 197, 94, 0.05)' }}>
              <div className="flex items-center gap-2">
                <CheckCircle size={12} style={{ color: '#22c55e' }} />
                <span className="text-xs" style={{ color: '#e6edf3' }}>Parking Garage</span>
              </div>
              <span className="text-xs" style={{ color: '#7d8590' }}>8:45 AM</span>
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="space-y-2">
          <button
            onClick={onEdit}
            className="w-full flex items-center gap-3 p-3 rounded-md transition-colors"
            style={{ background: 'rgba(88, 166, 255, 0.1)', color: '#58a6ff' }}
          >
            <Edit2 size={18} />
            <span>Edit Cardholder</span>
          </button>
          <button
            className="w-full flex items-center gap-3 p-3 rounded-md transition-colors"
            style={{ background: '#21262d', color: '#e6edf3' }}
          >
            <Activity size={18} />
            <span>View Full Activity</span>
          </button>
          {cardholder.is_active ? (
            <button
              className="w-full flex items-center gap-3 p-3 rounded-md transition-colors"
              style={{ background: 'rgba(239, 68, 68, 0.1)', color: '#ef4444' }}
            >
              <XCircle size={18} />
              <span>Deactivate Card</span>
            </button>
          ) : (
            <button
              className="w-full flex items-center gap-3 p-3 rounded-md transition-colors"
              style={{ background: 'rgba(34, 197, 94, 0.1)', color: '#22c55e' }}
            >
              <CheckCircle size={18} />
              <span>Reactivate Card</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// MAIN PEOPLE PAGE
// ============================================================================

export function People() {
  const [activeTab, setActiveTab] = useState<'cardholders' | 'access-levels'>('cardholders');
  const [cardholders, setCardholders] = useState<CardHolder[]>(MOCK_CARDHOLDERS);
  const [accessLevels] = useState<AccessLevel[]>(MOCK_ACCESS_LEVELS);
  const [doors] = useState<Door[]>(MOCK_DOORS);
  const [search, setSearch] = useState('');
  const [filterActive, setFilterActive] = useState<'all' | 'active' | 'inactive'>('all');
  const [modalOpen, setModalOpen] = useState(false);
  const [selectedCardholder, setSelectedCardholder] = useState<CardHolder | null>(null);
  const [detailCardholder, setDetailCardholder] = useState<CardHolder | null>(null);

  const filteredCardholders = cardholders.filter((ch) => {
    if (filterActive === 'active' && !ch.is_active) return false;
    if (filterActive === 'inactive' && ch.is_active) return false;

    if (search) {
      const searchLower = search.toLowerCase();
      return (
        ch.first_name?.toLowerCase().includes(searchLower) ||
        ch.last_name?.toLowerCase().includes(searchLower) ||
        ch.card_number?.toLowerCase().includes(searchLower) ||
        ch.email?.toLowerCase().includes(searchLower) ||
        ch.department?.toLowerCase().includes(searchLower)
      );
    }
    return true;
  });

  const handleSave = (data: Partial<CardHolder>) => {
    if (selectedCardholder) {
      setCardholders(cardholders.map(ch =>
        ch.id === selectedCardholder.id ? { ...ch, ...data } : ch
      ));
    } else {
      const newCardholder: CardHolder = {
        ...data as CardHolder,
        id: Math.max(...cardholders.map(c => c.id)) + 1,
        activation_date: Date.now(),
        expiration_date: 0,
        created_at: Date.now(),
        updated_at: Date.now(),
      };
      setCardholders([...cardholders, newCardholder]);
    }
    setModalOpen(false);
    setSelectedCardholder(null);
  };

  const activeCount = cardholders.filter(c => c.is_active).length;
  const inactiveCount = cardholders.filter(c => !c.is_active).length;

  return (
    <div className="space-y-6">
      {/* Main Content */}
      <div className={`transition-all ${detailCardholder ? 'mr-[400px]' : ''}`}>
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span
                className="w-2 h-2 rounded-full"
                style={{ background: '#8b5cf6' }}
              />
              <h1 className="text-xl font-semibold" style={{ color: '#e6edf3' }}>
                People
              </h1>
            </div>
            <p className="text-sm" style={{ color: '#7d8590' }}>
              Manage cardholders and access permissions
            </p>
          </div>
          <button
            onClick={() => {
              setSelectedCardholder(null);
              setModalOpen(true);
            }}
            className="flex items-center gap-2 px-4 py-2 rounded-md font-medium transition-colors"
            style={{ background: '#238636', color: '#ffffff' }}
          >
            <Plus size={18} />
            Add Cardholder
          </button>
        </div>

        {/* Tabs */}
        <div className="flex items-center gap-1 mb-6 p-1 rounded-md" style={{ background: '#21262d' }}>
          <button
            onClick={() => setActiveTab('cardholders')}
            className="flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors"
            style={{
              background: activeTab === 'cardholders' ? '#30363d' : 'transparent',
              color: activeTab === 'cardholders' ? '#e6edf3' : '#7d8590'
            }}
          >
            <User size={16} />
            Cardholders
            <span
              className="px-2 py-0.5 rounded text-xs"
              style={{ background: 'rgba(139, 92, 246, 0.15)', color: '#8b5cf6' }}
            >
              {cardholders.length}
            </span>
          </button>
          <button
            onClick={() => setActiveTab('access-levels')}
            className="flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors"
            style={{
              background: activeTab === 'access-levels' ? '#30363d' : 'transparent',
              color: activeTab === 'access-levels' ? '#e6edf3' : '#7d8590'
            }}
          >
            <Key size={16} />
            Access Levels
            <span
              className="px-2 py-0.5 rounded text-xs"
              style={{ background: 'rgba(139, 92, 246, 0.15)', color: '#8b5cf6' }}
            >
              {accessLevels.length}
            </span>
          </button>
        </div>

        {activeTab === 'cardholders' && (
          <>
            {/* Stats */}
            <div className="grid grid-cols-4 gap-4 mb-6">
              <div className="p-4 rounded-md" style={{ background: '#161b22', border: '1px solid #30363d' }}>
                <p className="text-xs" style={{ color: '#7d8590' }}>Total</p>
                <p className="text-2xl font-semibold mt-1" style={{ color: '#e6edf3' }}>{cardholders.length}</p>
              </div>
              <div className="p-4 rounded-md" style={{ background: '#161b22', border: '1px solid #30363d' }}>
                <div className="flex items-center gap-2 mb-1">
                  <span className="w-2 h-2 rounded-full" style={{ background: '#22c55e' }} />
                  <p className="text-xs" style={{ color: '#7d8590' }}>Active</p>
                </div>
                <p className="text-2xl font-semibold" style={{ color: '#22c55e' }}>{activeCount}</p>
              </div>
              <div className="p-4 rounded-md" style={{ background: '#161b22', border: '1px solid #30363d' }}>
                <div className="flex items-center gap-2 mb-1">
                  <span className="w-2 h-2 rounded-full" style={{ background: '#ef4444' }} />
                  <p className="text-xs" style={{ color: '#7d8590' }}>Inactive</p>
                </div>
                <p className="text-2xl font-semibold" style={{ color: '#ef4444' }}>{inactiveCount}</p>
              </div>
              <div className="p-4 rounded-md" style={{ background: '#161b22', border: '1px solid #30363d' }}>
                <div className="flex items-center gap-2 mb-1">
                  <span className="w-2 h-2 rounded-full" style={{ background: '#f59e0b' }} />
                  <p className="text-xs" style={{ color: '#7d8590' }}>Departments</p>
                </div>
                <p className="text-2xl font-semibold" style={{ color: '#f59e0b' }}>
                  {new Set(cardholders.map(c => c.department).filter(Boolean)).size}
                </p>
              </div>
            </div>

            {/* Search & Filters */}
            <div className="flex items-center gap-4 mb-4">
              <div className="relative flex-1">
                <Search className="absolute left-4 top-1/2 -translate-y-1/2" size={18} style={{ color: '#7d8590' }} />
                <input
                  type="text"
                  placeholder="Search by name, card number, email, or department..."
                  className="w-full rounded-md pl-11 pr-4 py-2.5 focus:outline-none"
                  style={{ background: '#0d1117', border: '1px solid #30363d', color: '#e6edf3' }}
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                />
              </div>
              <div className="flex rounded-md p-1" style={{ background: '#21262d' }}>
                {(['all', 'active', 'inactive'] as const).map(status => (
                  <button
                    key={status}
                    onClick={() => setFilterActive(status)}
                    className="px-3 py-1.5 rounded text-sm font-medium capitalize transition-colors"
                    style={{
                      background: filterActive === status
                        ? status === 'active' ? 'rgba(34, 197, 94, 0.15)'
                        : status === 'inactive' ? 'rgba(239, 68, 68, 0.15)'
                        : '#30363d'
                        : 'transparent',
                      color: filterActive === status
                        ? status === 'active' ? '#22c55e'
                        : status === 'inactive' ? '#ef4444'
                        : '#e6edf3'
                        : '#7d8590'
                    }}
                  >
                    {status}
                  </button>
                ))}
              </div>
              <button
                className="p-2.5 rounded-md transition-colors"
                style={{ border: '1px solid #30363d', color: '#7d8590' }}
              >
                <Download size={18} />
              </button>
            </div>

            {/* Table */}
            <div className="rounded-md overflow-hidden" style={{ background: '#161b22', border: '1px solid #30363d' }}>
              <table className="w-full">
                <thead>
                  <tr style={{ borderBottom: '1px solid #30363d', background: '#0d1117' }}>
                    <th className="text-left py-3 px-4 text-sm font-medium" style={{ color: '#7d8590' }}>NAME</th>
                    <th className="text-left py-3 px-4 text-sm font-medium" style={{ color: '#7d8590' }}>CARD</th>
                    <th className="text-left py-3 px-4 text-sm font-medium" style={{ color: '#7d8590' }}>DEPARTMENT</th>
                    <th className="text-left py-3 px-4 text-sm font-medium" style={{ color: '#7d8590' }}>STATUS</th>
                    <th className="text-right py-3 px-4 text-sm font-medium" style={{ color: '#7d8590' }}>ACTIONS</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredCardholders.length === 0 ? (
                    <tr>
                      <td colSpan={5} className="py-12 text-center" style={{ color: '#7d8590' }}>
                        No cardholders found
                      </td>
                    </tr>
                  ) : (
                    filteredCardholders.map((ch) => (
                      <tr
                        key={ch.id}
                        onClick={() => setDetailCardholder(ch)}
                        className="cursor-pointer transition-colors"
                        style={{
                          borderBottom: '1px solid #21262d',
                          background: detailCardholder?.id === ch.id ? 'rgba(139, 92, 246, 0.1)' : 'transparent'
                        }}
                        onMouseEnter={(e) => {
                          if (detailCardholder?.id !== ch.id) {
                            e.currentTarget.style.background = '#21262d';
                          }
                        }}
                        onMouseLeave={(e) => {
                          if (detailCardholder?.id !== ch.id) {
                            e.currentTarget.style.background = 'transparent';
                          }
                        }}
                      >
                        <td className="py-3 px-4">
                          <div className="flex items-center gap-3">
                            <div
                              className="w-9 h-9 rounded-md flex items-center justify-center text-sm font-medium"
                              style={{
                                background: ch.is_active ? 'rgba(139, 92, 246, 0.15)' : '#21262d',
                                color: ch.is_active ? '#8b5cf6' : '#7d8590'
                              }}
                            >
                              {ch.first_name[0]}{ch.last_name[0]}
                            </div>
                            <div>
                              <p style={{ color: '#e6edf3' }}>{ch.first_name} {ch.last_name}</p>
                              <p className="text-xs" style={{ color: '#7d8590' }}>{ch.email || '-'}</p>
                            </div>
                          </div>
                        </td>
                        <td className="py-3 px-4 font-mono text-sm" style={{ color: '#7d8590' }}>{ch.card_number}</td>
                        <td className="py-3 px-4" style={{ color: '#7d8590' }}>{ch.department || '-'}</td>
                        <td className="py-3 px-4">
                          <span
                            className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-medium"
                            style={{
                              background: ch.is_active ? 'rgba(34, 197, 94, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                              color: ch.is_active ? '#22c55e' : '#ef4444'
                            }}
                          >
                            {ch.is_active ? <CheckCircle size={10} /> : <XCircle size={10} />}
                            {ch.is_active ? 'Active' : 'Inactive'}
                          </span>
                        </td>
                        <td className="py-3 px-4">
                          <div className="flex items-center justify-end gap-1">
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                setSelectedCardholder(ch);
                                setModalOpen(true);
                              }}
                              className="p-2 rounded-md transition-colors"
                              style={{ color: '#7d8590' }}
                            >
                              <Edit2 size={14} />
                            </button>
                            <button
                              onClick={(e) => e.stopPropagation()}
                              className="p-2 rounded-md transition-colors"
                              style={{ color: '#7d8590' }}
                            >
                              <MoreHorizontal size={14} />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </>
        )}

        {activeTab === 'access-levels' && (
          <div className="grid grid-cols-2 gap-4">
            {accessLevels.map(level => (
              <div
                key={level.id}
                className="p-4 rounded-md cursor-pointer transition-colors"
                style={{ background: '#161b22', border: '1px solid #30363d' }}
              >
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <div
                      className="p-2 rounded-md"
                      style={{ background: 'rgba(249, 115, 22, 0.1)', color: '#f97316' }}
                    >
                      <Key size={18} />
                    </div>
                    <div>
                      <h3 className="font-medium" style={{ color: '#e6edf3' }}>{level.name}</h3>
                      <p className="text-xs" style={{ color: '#7d8590' }}>{level.description}</p>
                    </div>
                  </div>
                  <button className="p-2 rounded-md transition-colors" style={{ color: '#7d8590' }}>
                    <Edit2 size={14} />
                  </button>
                </div>
                <div className="flex flex-wrap gap-2">
                  {level.doors?.map(doorId => {
                    const door = doors.find(d => d.door_id === doorId);
                    return door ? (
                      <span
                        key={doorId}
                        className="inline-flex items-center gap-1 px-2 py-1 rounded text-xs"
                        style={{ background: 'rgba(139, 92, 246, 0.1)', color: '#8b5cf6' }}
                      >
                        <DoorOpen size={10} />
                        {door.name}
                      </span>
                    ) : null;
                  })}
                </div>
                <div
                  className="mt-3 pt-3 flex items-center justify-between text-xs"
                  style={{ borderTop: '1px solid #30363d', color: '#7d8590' }}
                >
                  <span>{level.doors?.length || 0} doors</span>
                  <span>Priority: {level.priority}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Detail Panel */}
      <DetailPanel
        cardholder={detailCardholder}
        accessLevels={accessLevels}
        doors={doors}
        onClose={() => setDetailCardholder(null)}
        onEdit={() => {
          setSelectedCardholder(detailCardholder);
          setModalOpen(true);
        }}
      />

      {/* Modal */}
      <CardholderModal
        isOpen={modalOpen}
        onClose={() => {
          setModalOpen(false);
          setSelectedCardholder(null);
        }}
        onSave={handleSave}
        cardholder={selectedCardholder}
      />
    </div>
  );
}
