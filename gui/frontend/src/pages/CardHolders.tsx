import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { CreditCard, Plus, Pencil, Trash2, Shield, DoorOpen, X } from 'lucide-react';
import { apiClient } from '../api/clientV2_1';

interface CardHolder {
  id: number;
  card_number: string;
  first_name: string;
  last_name: string;
  email?: string;
  phone?: string;
  department?: string;
  employee_id?: string;
  badge_number?: string;
  activation_date: number;
  expiration_date: number;
  is_active: boolean;
  notes?: string;
  created_at: number;
  updated_at: number;
}

interface AccessLevel {
  level_id: number;
  level_name: string;
  description?: string;
  priority: number;
}

interface Door {
  door_id: number;
  door_name: string;
  location?: string;
  level_name: string;
}

export default function CardHolders() {
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [isAccessLevelsModalOpen, setIsAccessLevelsModalOpen] = useState(false);
  const [isDoorsModalOpen, setIsDoorsModalOpen] = useState(false);
  const [selectedCardHolder, setSelectedCardHolder] = useState<CardHolder | null>(null);

  const queryClient = useQueryClient();

  // Fetch card holders
  const { data: cardHolders = [], isLoading } = useQuery<CardHolder[]>({
    queryKey: ['cardHolders'],
    queryFn: () => apiClient.getCardHolders(),
  });

  const handleCreate = (cardHolder: CardHolder) => {
    setSelectedCardHolder(cardHolder);
    setIsCreateModalOpen(false);
    queryClient.invalidateQueries({ queryKey: ['cardHolders'] });
  };

  const handleEdit = (cardHolder: CardHolder) => {
    setSelectedCardHolder(cardHolder);
    setIsEditModalOpen(true);
  };

  const handleDelete = (cardHolder: CardHolder) => {
    setSelectedCardHolder(cardHolder);
    setIsDeleteModalOpen(true);
  };

  const handleAccessLevels = (cardHolder: CardHolder) => {
    setSelectedCardHolder(cardHolder);
    setIsAccessLevelsModalOpen(true);
  };

  const handleDoors = (cardHolder: CardHolder) => {
    setSelectedCardHolder(cardHolder);
    setIsDoorsModalOpen(true);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-400">Loading card holders...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-white">Card Holders</h1>
          <p className="text-gray-400 mt-1">Manage card holder credentials and access</p>
        </div>
        <button
          onClick={() => setIsCreateModalOpen(true)}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg flex items-center gap-2"
        >
          <Plus className="h-5 w-5" />
          Add Card Holder
        </button>
      </div>

      {/* Card Holders Table */}
      <div className="bg-slate-800 rounded-lg overflow-hidden">
        <table className="w-full">
          <thead className="bg-slate-700">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase">Card Number</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase">Name</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase">Department</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase">Employee ID</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase">Status</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-700">
            {cardHolders.map((holder) => (
              <tr key={holder.id} className="hover:bg-slate-700/50">
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center">
                    <CreditCard className="h-5 w-5 text-blue-400 mr-2" />
                    <span className="text-white font-mono">{holder.card_number}</span>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div>
                    <div className="text-white font-medium">{holder.first_name} {holder.last_name}</div>
                    {holder.email && <div className="text-gray-400 text-sm">{holder.email}</div>}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-gray-300">
                  {holder.department || '-'}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-gray-300">
                  {holder.employee_id || '-'}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span
                    className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                      holder.is_active
                        ? 'bg-green-900/50 text-green-400 border border-green-500'
                        : 'bg-red-900/50 text-red-400 border border-red-500'
                    }`}
                  >
                    {holder.is_active ? 'Active' : 'Inactive'}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm">
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleAccessLevels(holder)}
                      className="text-blue-400 hover:text-blue-300"
                      title="Manage Access Levels"
                    >
                      <Shield className="h-5 w-5" />
                    </button>
                    <button
                      onClick={() => handleDoors(holder)}
                      className="text-purple-400 hover:text-purple-300"
                      title="View Accessible Doors"
                    >
                      <DoorOpen className="h-5 w-5" />
                    </button>
                    <button
                      onClick={() => handleEdit(holder)}
                      className="text-yellow-400 hover:text-yellow-300"
                      title="Edit"
                    >
                      <Pencil className="h-5 w-5" />
                    </button>
                    <button
                      onClick={() => handleDelete(holder)}
                      className="text-red-400 hover:text-red-300"
                      title="Delete"
                    >
                      <Trash2 className="h-5 w-5" />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {cardHolders.length === 0 && (
          <div className="text-center py-12 text-gray-400">
            No card holders found. Click "Add Card Holder" to create one.
          </div>
        )}
      </div>

      {/* Modals */}
      {isCreateModalOpen && (
        <CreateCardHolderModal
          onClose={() => setIsCreateModalOpen(false)}
          onSuccess={handleCreate}
        />
      )}

      {isEditModalOpen && selectedCardHolder && (
        <EditCardHolderModal
          cardHolder={selectedCardHolder}
          onClose={() => {
            setIsEditModalOpen(false);
            setSelectedCardHolder(null);
          }}
          onSuccess={() => {
            setIsEditModalOpen(false);
            setSelectedCardHolder(null);
            queryClient.invalidateQueries({ queryKey: ['cardHolders'] });
          }}
        />
      )}

      {isDeleteModalOpen && selectedCardHolder && (
        <DeleteCardHolderModal
          cardHolder={selectedCardHolder}
          onClose={() => {
            setIsDeleteModalOpen(false);
            setSelectedCardHolder(null);
          }}
          onSuccess={() => {
            setIsDeleteModalOpen(false);
            setSelectedCardHolder(null);
            queryClient.invalidateQueries({ queryKey: ['cardHolders'] });
          }}
        />
      )}

      {isAccessLevelsModalOpen && selectedCardHolder && (
        <AccessLevelsModal
          cardHolder={selectedCardHolder}
          onClose={() => {
            setIsAccessLevelsModalOpen(false);
            setSelectedCardHolder(null);
          }}
        />
      )}

      {isDoorsModalOpen && selectedCardHolder && (
        <DoorsModal
          cardHolder={selectedCardHolder}
          onClose={() => {
            setIsDoorsModalOpen(false);
            setSelectedCardHolder(null);
          }}
        />
      )}
    </div>
  );
}

// Create Card Holder Modal
function CreateCardHolderModal({ onClose, onSuccess }: any) {
  const [formData, setFormData] = useState({
    card_number: '',
    first_name: '',
    last_name: '',
    email: '',
    phone: '',
    department: '',
    employee_id: '',
    badge_number: '',
    notes: '',
    is_active: true,
  });
  const [error, setError] = useState('');

  const createMutation = useMutation({
    mutationFn: (data: any) => apiClient.createCardHolder(data),
    onSuccess: (data) => onSuccess(data),
    onError: (error: any) => {
      setError(error.response?.data?.detail || 'Failed to create card holder');
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!formData.card_number || !formData.first_name || !formData.last_name) {
      setError('Card number, first name, and last name are required');
      return;
    }

    createMutation.mutate(formData);
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
      <div className="bg-slate-800 rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-slate-700 flex justify-between items-center">
          <h2 className="text-xl font-bold text-white">Add Card Holder</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-white">
            <X className="h-6 w-6" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="bg-red-900/50 border border-red-500 text-red-200 px-4 py-3 rounded">
              {error}
            </div>
          )}

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Card Number *
              </label>
              <input
                type="text"
                value={formData.card_number}
                onChange={(e) => setFormData({ ...formData, card_number: e.target.value })}
                className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white"
                placeholder="1234567890"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Employee ID
              </label>
              <input
                type="text"
                value={formData.employee_id}
                onChange={(e) => setFormData({ ...formData, employee_id: e.target.value })}
                className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white"
                placeholder="EMP001"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                First Name *
              </label>
              <input
                type="text"
                value={formData.first_name}
                onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
                className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Last Name *
              </label>
              <input
                type="text"
                value={formData.last_name}
                onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
                className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white"
                required
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Email
              </label>
              <input
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Phone
              </label>
              <input
                type="tel"
                value={formData.phone}
                onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Department
              </label>
              <input
                type="text"
                value={formData.department}
                onChange={(e) => setFormData({ ...formData, department: e.target.value })}
                className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Badge Number
              </label>
              <input
                type="text"
                value={formData.badge_number}
                onChange={(e) => setFormData({ ...formData, badge_number: e.target.value })}
                className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Notes
            </label>
            <textarea
              value={formData.notes}
              onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
              className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white"
              rows={3}
            />
          </div>

          <div className="flex items-center">
            <input
              type="checkbox"
              checked={formData.is_active}
              onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
              className="mr-2"
            />
            <label className="text-sm text-gray-300">Active</label>
          </div>

          <div className="flex justify-end gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={createMutation.isPending}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded disabled:opacity-50"
            >
              {createMutation.isPending ? 'Creating...' : 'Create Card Holder'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// Edit, Delete, Access Levels, and Doors modals would follow similar patterns
// For brevity, I'll create simplified versions

function EditCardHolderModal({ cardHolder, onClose, onSuccess }: any) {
  const [formData, setFormData] = useState({
    card_number: cardHolder.card_number,
    first_name: cardHolder.first_name,
    last_name: cardHolder.last_name,
    email: cardHolder.email || '',
    phone: cardHolder.phone || '',
    department: cardHolder.department || '',
    employee_id: cardHolder.employee_id || '',
    badge_number: cardHolder.badge_number || '',
    notes: cardHolder.notes || '',
    is_active: cardHolder.is_active,
  });

  const updateMutation = useMutation({
    mutationFn: (data: any) => apiClient.updateCardHolder(cardHolder.id, data),
    onSuccess: () => onSuccess(),
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    updateMutation.mutate(formData);
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
      <div className="bg-slate-800 rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-slate-700 flex justify-between items-center">
          <h2 className="text-xl font-bold text-white">Edit Card Holder</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-white">
            <X className="h-6 w-6" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {/* Same fields as Create modal */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Card Number</label>
              <input
                type="text"
                value={formData.card_number}
                onChange={(e) => setFormData({ ...formData, card_number: e.target.value })}
                className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Employee ID</label>
              <input
                type="text"
                value={formData.employee_id}
                onChange={(e) => setFormData({ ...formData, employee_id: e.target.value })}
                className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">First Name</label>
              <input
                type="text"
                value={formData.first_name}
                onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
                className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Last Name</label>
              <input
                type="text"
                value={formData.last_name}
                onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
                className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Email</label>
              <input
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Phone</label>
              <input
                type="tel"
                value={formData.phone}
                onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Department</label>
              <input
                type="text"
                value={formData.department}
                onChange={(e) => setFormData({ ...formData, department: e.target.value })}
                className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Badge Number</label>
              <input
                type="text"
                value={formData.badge_number}
                onChange={(e) => setFormData({ ...formData, badge_number: e.target.value })}
                className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Notes</label>
            <textarea
              value={formData.notes}
              onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
              className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white"
              rows={3}
            />
          </div>

          <div className="flex items-center">
            <input
              type="checkbox"
              checked={formData.is_active}
              onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
              className="mr-2"
            />
            <label className="text-sm text-gray-300">Active</label>
          </div>

          <div className="flex justify-end gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={updateMutation.isPending}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded disabled:opacity-50"
            >
              {updateMutation.isPending ? 'Updating...' : 'Update Card Holder'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function DeleteCardHolderModal({ cardHolder, onClose, onSuccess }: any) {
  const deleteMutation = useMutation({
    mutationFn: () => apiClient.deleteCardHolder(cardHolder.id),
    onSuccess: () => onSuccess(),
  });

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
      <div className="bg-slate-800 rounded-lg max-w-md w-full">
        <div className="p-6">
          <h2 className="text-xl font-bold text-white mb-4">Delete Card Holder</h2>
          <p className="text-gray-300 mb-6">
            Are you sure you want to delete card holder "{cardHolder.first_name} {cardHolder.last_name}" (Card: {cardHolder.card_number})?
            This action cannot be undone.
          </p>
          <div className="flex justify-end gap-3">
            <button
              onClick={onClose}
              className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded"
            >
              Cancel
            </button>
            <button
              onClick={() => deleteMutation.mutate()}
              disabled={deleteMutation.isPending}
              className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded disabled:opacity-50"
            >
              {deleteMutation.isPending ? 'Deleting...' : 'Delete'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function AccessLevelsModal({ cardHolder, onClose }: any) {
  const queryClient = useQueryClient();

  const { data: accessLevels = [] } = useQuery<AccessLevel[]>({
    queryKey: ['cardHolderAccessLevels', cardHolder.id],
    queryFn: () => apiClient.getCardHolderAccessLevels(cardHolder.id),
  });

  const { data: allAccessLevels = [] } = useQuery<AccessLevel[]>({
    queryKey: ['accessLevels'],
    queryFn: () => apiClient.getAccessLevels(),
  });

  const grantMutation = useMutation({
    mutationFn: (levelId: number) => apiClient.grantCardHolderAccessLevel(cardHolder.id, levelId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cardHolderAccessLevels', cardHolder.id] });
    },
  });

  const revokeMutation = useMutation({
    mutationFn: (levelId: number) => apiClient.revokeCardHolderAccessLevel(cardHolder.id, levelId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cardHolderAccessLevels', cardHolder.id] });
    },
  });

  const assignedLevelIds = accessLevels.map((al: any) => al.level_id);
  const availableLevels = allAccessLevels.filter((al: any) => !assignedLevelIds.includes(al.level_id));

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
      <div className="bg-slate-800 rounded-lg max-w-4xl w-full max-h-[80vh] overflow-y-auto">
        <div className="p-6 border-b border-slate-700 flex justify-between items-center">
          <div>
            <h2 className="text-xl font-bold text-white">Access Levels</h2>
            <p className="text-gray-400 text-sm">
              {cardHolder.first_name} {cardHolder.last_name} - {cardHolder.card_number}
            </p>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-white">
            <X className="h-6 w-6" />
          </button>
        </div>

        <div className="p-6 grid grid-cols-2 gap-6">
          {/* Available Access Levels */}
          <div>
            <h3 className="text-lg font-semibold text-white mb-4">Available Access Levels</h3>
            <div className="space-y-2">
              {availableLevels.map((level: any) => (
                <div key={level.level_id} className="bg-slate-700 p-3 rounded flex justify-between items-center">
                  <div>
                    <div className="text-white font-medium">{level.name}</div>
                    <div className="text-gray-400 text-sm">Priority: {level.priority}</div>
                  </div>
                  <button
                    onClick={() => grantMutation.mutate(level.level_id)}
                    disabled={grantMutation.isPending}
                    className="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded disabled:opacity-50"
                  >
                    Grant
                  </button>
                </div>
              ))}
              {availableLevels.length === 0 && (
                <div className="text-gray-400 text-center py-8">No available access levels</div>
              )}
            </div>
          </div>

          {/* Assigned Access Levels */}
          <div>
            <h3 className="text-lg font-semibold text-white mb-4">Assigned Access Levels</h3>
            <div className="space-y-2">
              {accessLevels.map((level: any) => (
                <div key={level.level_id} className="bg-slate-700 p-3 rounded flex justify-between items-center">
                  <div>
                    <div className="text-white font-medium">{level.level_name}</div>
                    <div className="text-gray-400 text-sm">Priority: {level.priority}</div>
                  </div>
                  <button
                    onClick={() => revokeMutation.mutate(level.level_id)}
                    disabled={revokeMutation.isPending}
                    className="px-3 py-1 bg-red-600 hover:bg-red-700 text-white text-sm rounded disabled:opacity-50"
                  >
                    Revoke
                  </button>
                </div>
              ))}
              {accessLevels.length === 0 && (
                <div className="text-gray-400 text-center py-8">No assigned access levels</div>
              )}
            </div>
          </div>
        </div>

        <div className="p-6 border-t border-slate-700 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}

function DoorsModal({ cardHolder, onClose }: any) {
  const { data: doors = [] } = useQuery<Door[]>({
    queryKey: ['cardHolderDoors', cardHolder.id],
    queryFn: () => apiClient.getCardHolderDoors(cardHolder.id),
  });

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
      <div className="bg-slate-800 rounded-lg max-w-3xl w-full max-h-[80vh] overflow-y-auto">
        <div className="p-6 border-b border-slate-700 flex justify-between items-center">
          <div>
            <h2 className="text-xl font-bold text-white">Accessible Doors</h2>
            <p className="text-gray-400 text-sm">
              {cardHolder.first_name} {cardHolder.last_name} - {cardHolder.card_number}
            </p>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-white">
            <X className="h-6 w-6" />
          </button>
        </div>

        <div className="p-6">
          <div className="space-y-3">
            {doors.map((door: any) => (
              <div key={door.door_id} className="bg-slate-700 p-4 rounded flex items-center justify-between">
                <div className="flex items-center">
                  <DoorOpen className="h-5 w-5 text-blue-400 mr-3" />
                  <div>
                    <div className="text-white font-medium">{door.door_name}</div>
                    {door.location && <div className="text-gray-400 text-sm">{door.location}</div>}
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-gray-400 text-sm">via {door.level_name}</div>
                  {door.osdp_enabled && (
                    <span className="inline-flex px-2 py-1 text-xs font-semibold rounded bg-green-900/50 text-green-400 border border-green-500">
                      OSDP
                    </span>
                  )}
                </div>
              </div>
            ))}
            {doors.length === 0 && (
              <div className="text-gray-400 text-center py-12">
                This card holder has no door access assigned.
                <br />
                Grant access levels to enable door access.
              </div>
            )}
          </div>
        </div>

        <div className="p-6 border-t border-slate-700 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
