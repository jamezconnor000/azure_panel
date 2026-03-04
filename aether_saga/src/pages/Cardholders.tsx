import { useEffect, useState } from 'react';
import { Plus, Search, Edit2, Trash2, MoreVertical, User } from 'lucide-react';
import { cardsApi, cardHoldersApi } from '../api/bifrost';
import type { Card, CardHolder } from '../types';

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
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="glass rounded-xl w-full max-w-lg mx-4">
        <div className="px-6 py-4 border-b border-white/10">
          <h2 className="text-lg font-semibold text-white">
            {cardholder ? 'Edit Cardholder' : 'Add Cardholder'}
          </h2>
        </div>
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-gray-400 mb-1">First Name *</label>
              <input
                type="text"
                required
                className="w-full bg-aether-darker border border-white/10 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-aether-primary"
                value={formData.first_name || ''}
                onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Last Name *</label>
              <input
                type="text"
                required
                className="w-full bg-aether-darker border border-white/10 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-aether-primary"
                value={formData.last_name || ''}
                onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
              />
            </div>
          </div>

          <div>
            <label className="block text-sm text-gray-400 mb-1">Card Number *</label>
            <input
              type="text"
              required
              className="w-full bg-aether-darker border border-white/10 rounded-lg px-4 py-2 text-white font-mono focus:outline-none focus:border-aether-primary"
              value={formData.card_number || ''}
              onChange={(e) => setFormData({ ...formData, card_number: e.target.value })}
              disabled={!!cardholder}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-gray-400 mb-1">Email</label>
              <input
                type="email"
                className="w-full bg-aether-darker border border-white/10 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-aether-primary"
                value={formData.email || ''}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Phone</label>
              <input
                type="tel"
                className="w-full bg-aether-darker border border-white/10 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-aether-primary"
                value={formData.phone || ''}
                onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-gray-400 mb-1">Department</label>
              <input
                type="text"
                className="w-full bg-aether-darker border border-white/10 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-aether-primary"
                value={formData.department || ''}
                onChange={(e) => setFormData({ ...formData, department: e.target.value })}
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Employee ID</label>
              <input
                type="text"
                className="w-full bg-aether-darker border border-white/10 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-aether-primary"
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
              className="rounded border-white/10 bg-aether-darker text-aether-primary focus:ring-aether-primary"
            />
            <label htmlFor="is_active" className="text-sm text-gray-300">Active</label>
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
              {cardholder ? 'Save Changes' : 'Add Cardholder'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export function Cardholders() {
  const [cardholders, setCardholders] = useState<CardHolder[]>([]);
  const [cards, setCards] = useState<Card[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [modalOpen, setModalOpen] = useState(false);
  const [selectedCardholder, setSelectedCardholder] = useState<CardHolder | null>(null);

  const fetchData = async () => {
    try {
      setLoading(true);
      // Try to get cardholders first, fall back to cards
      try {
        const data = await cardHoldersApi.list(true);
        setCardholders(data);
      } catch {
        // Fall back to cards API
        const data = await cardsApi.list(1000, 0);
        // Convert cards to cardholder-like format
        setCards(data.cards || []);
      }
      setError(null);
    } catch (err) {
      setError('Failed to load cardholders');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleSave = async (data: Partial<CardHolder>) => {
    try {
      if (selectedCardholder) {
        await cardHoldersApi.update(selectedCardholder.id, data);
      } else {
        await cardHoldersApi.create(data);
      }
      setModalOpen(false);
      setSelectedCardholder(null);
      fetchData();
    } catch (err) {
      console.error('Failed to save cardholder:', err);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this cardholder?')) return;
    try {
      await cardHoldersApi.delete(id);
      fetchData();
    } catch (err) {
      console.error('Failed to delete cardholder:', err);
    }
  };

  const filteredCardholders = cardholders.filter((ch) => {
    const searchLower = search.toLowerCase();
    return (
      ch.first_name?.toLowerCase().includes(searchLower) ||
      ch.last_name?.toLowerCase().includes(searchLower) ||
      ch.card_number?.toLowerCase().includes(searchLower) ||
      ch.email?.toLowerCase().includes(searchLower)
    );
  });

  const filteredCards = cards.filter((card) => {
    const searchLower = search.toLowerCase();
    return (
      card.card_number?.toLowerCase().includes(searchLower) ||
      card.holder_name?.toLowerCase().includes(searchLower)
    );
  });

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-2 border-aether-primary border-t-transparent"></div>
      </div>
    );
  }

  const displayCards = cardholders.length > 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">Cardholders</h1>
          <p className="text-gray-400">Manage access credentials and personnel</p>
        </div>
        <button
          onClick={() => {
            setSelectedCardholder(null);
            setModalOpen(true);
          }}
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-aether-primary text-aether-darker font-medium hover:bg-aether-primary/90"
        >
          <Plus size={20} />
          Add Cardholder
        </button>
      </div>

      {/* Search */}
      <div className="glass rounded-xl p-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
          <input
            type="text"
            placeholder="Search cardholders..."
            className="w-full bg-aether-darker border border-white/10 rounded-lg pl-10 pr-4 py-2 text-white focus:outline-none focus:border-aether-primary"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </div>

      {error && (
        <div className="glass rounded-xl p-4 border border-aether-danger/30">
          <p className="text-aether-danger">{error}</p>
        </div>
      )}

      {/* Table */}
      <div className="glass rounded-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="text-left text-gray-400 text-sm border-b border-white/10">
                <th className="py-3 px-4 font-medium">Name</th>
                <th className="py-3 px-4 font-medium">Card Number</th>
                <th className="py-3 px-4 font-medium">Department</th>
                <th className="py-3 px-4 font-medium">Status</th>
                <th className="py-3 px-4 font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {displayCards ? (
                filteredCardholders.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="py-8 text-center text-gray-400">
                      No cardholders found
                    </td>
                  </tr>
                ) : (
                  filteredCardholders.map((ch) => (
                    <tr key={ch.id} className="border-b border-white/5 hover:bg-white/5">
                      <td className="py-3 px-4">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 rounded-full bg-aether-primary/20 flex items-center justify-center">
                            <User size={20} className="text-aether-primary" />
                          </div>
                          <div>
                            <p className="text-white font-medium">{ch.first_name} {ch.last_name}</p>
                            <p className="text-gray-400 text-sm">{ch.email || '-'}</p>
                          </div>
                        </div>
                      </td>
                      <td className="py-3 px-4 font-mono text-gray-300">{ch.card_number}</td>
                      <td className="py-3 px-4 text-gray-300">{ch.department || '-'}</td>
                      <td className="py-3 px-4">
                        <span className={`px-2 py-1 rounded-full text-xs ${ch.is_active ? 'bg-aether-success/20 text-aether-success' : 'bg-aether-danger/20 text-aether-danger'}`}>
                          {ch.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => {
                              setSelectedCardholder(ch);
                              setModalOpen(true);
                            }}
                            className="p-2 rounded-lg hover:bg-white/10 text-gray-400 hover:text-white"
                          >
                            <Edit2 size={16} />
                          </button>
                          <button
                            onClick={() => handleDelete(ch.id)}
                            className="p-2 rounded-lg hover:bg-white/10 text-gray-400 hover:text-aether-danger"
                          >
                            <Trash2 size={16} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                )
              ) : (
                // Fall back to cards display
                filteredCards.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="py-8 text-center text-gray-400">
                      No cards found
                    </td>
                  </tr>
                ) : (
                  filteredCards.map((card) => (
                    <tr key={card.card_number} className="border-b border-white/5 hover:bg-white/5">
                      <td className="py-3 px-4">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 rounded-full bg-aether-primary/20 flex items-center justify-center">
                            <User size={20} className="text-aether-primary" />
                          </div>
                          <div>
                            <p className="text-white font-medium">{card.holder_name || 'Unknown'}</p>
                          </div>
                        </div>
                      </td>
                      <td className="py-3 px-4 font-mono text-gray-300">{card.card_number}</td>
                      <td className="py-3 px-4 text-gray-300">-</td>
                      <td className="py-3 px-4">
                        <span className={`px-2 py-1 rounded-full text-xs ${card.is_active ? 'bg-aether-success/20 text-aether-success' : 'bg-aether-danger/20 text-aether-danger'}`}>
                          {card.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        <button className="p-2 rounded-lg hover:bg-white/10 text-gray-400">
                          <MoreVertical size={16} />
                        </button>
                      </td>
                    </tr>
                  ))
                )
              )}
            </tbody>
          </table>
        </div>
      </div>

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
