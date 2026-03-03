/**
 * User Management Page
 * Manage system users, roles, and access level assignments
 */

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClientV2_1 from '../api/clientV2_1';
import { usePermission, useAuth } from '../contexts/AuthContext';
import {
  Users,
  Plus,
  Edit,
  Trash,
  X,
  Save,
  AlertCircle,
  Check,
  Key,
  Shield,
  DoorOpen,
  UserCheck,
} from 'lucide-react';
import type { User, UserCreate, UserUpdate, UserRole, PasswordChange } from '../types/v2.1';

export default function UserManagement() {
  const queryClient = useQueryClient();
  const { user: currentUser } = useAuth();
  const canCreate = usePermission('user.create');
  const canUpdate = usePermission('user.update');
  const canDelete = usePermission('user.delete');

  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showPasswordModal, setShowPasswordModal] = useState(false);
  const [showAccessLevelsModal, setShowAccessLevelsModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Fetch users
  const { data: users, isLoading } = useQuery({
    queryKey: ['users'],
    queryFn: () => apiClientV2_1.getUsers(false),
  });

  // Create user mutation
  const createMutation = useMutation({
    mutationFn: (data: UserCreate) => apiClientV2_1.createUser(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      setShowCreateModal(false);
      setSuccess('User created successfully');
      setTimeout(() => setSuccess(''), 3000);
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail || 'Failed to create user');
    },
  });

  // Update user mutation
  const updateMutation = useMutation({
    mutationFn: ({ userId, data }: { userId: number; data: UserUpdate }) =>
      apiClientV2_1.updateUser(userId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      setShowEditModal(false);
      setSuccess('User updated successfully');
      setTimeout(() => setSuccess(''), 3000);
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail || 'Failed to update user');
    },
  });

  // Delete user mutation
  const deleteMutation = useMutation({
    mutationFn: (userId: number) => apiClientV2_1.deleteUser(userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      setShowDeleteModal(false);
      setSuccess('User deleted successfully');
      setTimeout(() => setSuccess(''), 3000);
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail || 'Failed to delete user');
    },
  });

  // Change password mutation
  const passwordMutation = useMutation({
    mutationFn: ({ userId, data }: { userId: number; data: PasswordChange }) =>
      apiClientV2_1.changePassword(userId, data),
    onSuccess: () => {
      setShowPasswordModal(false);
      setSuccess('Password changed successfully');
      setTimeout(() => setSuccess(''), 3000);
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail || 'Failed to change password');
    },
  });

  const getRoleBadgeColor = (role: UserRole) => {
    switch (role) {
      case 'admin':
        return 'bg-red-900/50 text-red-400 border-red-500';
      case 'operator':
        return 'bg-blue-900/50 text-blue-400 border-blue-500';
      case 'guard':
        return 'bg-green-900/50 text-green-400 border-green-500';
      default:
        return 'bg-gray-700 text-gray-400 border-gray-600';
    }
  };

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6 flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-white">User Management</h1>
          <p className="text-gray-400 mt-1">Manage system users, roles, and permissions</p>
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
            Create User
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
          <p className="text-gray-400">Loading users...</p>
        </div>
      )}

      {/* Users Table */}
      {!isLoading && users && (
        <div className="bg-gray-800 rounded-lg overflow-hidden shadow-lg">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-700">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    User
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    Email
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    Role
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    Last Login
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-700">
                {users.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-6 py-12 text-center text-gray-400">
                      No users found.
                    </td>
                  </tr>
                ) : (
                  users.map((user) => (
                    <tr key={user.id} className="hover:bg-gray-750 transition">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div>
                          <div className="text-white font-medium flex items-center">
                            {user.username}
                            {user.id === currentUser?.id && (
                              <span className="ml-2 text-xs text-blue-400">(You)</span>
                            )}
                          </div>
                          {(user.first_name || user.last_name) && (
                            <div className="text-gray-400 text-sm">
                              {user.first_name} {user.last_name}
                            </div>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">{user.email}</td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium border ${getRoleBadgeColor(
                            user.role
                          )}`}
                        >
                          <Shield className="w-3 h-3 mr-1" />
                          {user.role}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {user.is_active ? (
                          <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-green-900/50 text-green-400">
                            Active
                          </span>
                        ) : (
                          <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-gray-700 text-gray-400">
                            Inactive
                          </span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                        {user.last_login_at ? new Date(user.last_login_at * 1000).toLocaleString() : 'Never'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <div className="flex space-x-2">
                          <button
                            onClick={() => {
                              setSelectedUser(user);
                              setError('');
                              setShowAccessLevelsModal(true);
                            }}
                            className="p-2 rounded-lg text-purple-400 hover:text-purple-300 hover:bg-purple-900/30 transition"
                            title="Manage Access Levels"
                          >
                            <DoorOpen className="w-5 h-5" />
                          </button>
                          {canUpdate && (
                            <>
                              <button
                                onClick={() => {
                                  setSelectedUser(user);
                                  setError('');
                                  setShowPasswordModal(true);
                                }}
                                className="p-2 rounded-lg text-orange-400 hover:text-orange-300 hover:bg-orange-900/30 transition"
                                title="Change Password"
                              >
                                <Key className="w-5 h-5" />
                              </button>
                              <button
                                onClick={() => {
                                  setSelectedUser(user);
                                  setError('');
                                  setShowEditModal(true);
                                }}
                                className="p-2 rounded-lg text-yellow-400 hover:text-yellow-300 hover:bg-yellow-900/30 transition"
                                title="Edit User"
                              >
                                <Edit className="w-5 h-5" />
                              </button>
                            </>
                          )}
                          {canDelete && user.id !== currentUser?.id && (
                            <button
                              onClick={() => {
                                setSelectedUser(user);
                                setError('');
                                setShowDeleteModal(true);
                              }}
                              className="p-2 rounded-lg text-red-400 hover:text-red-300 hover:bg-red-900/30 transition"
                              title="Delete User"
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

      {/* Modals */}
      {showCreateModal && <CreateUserModal onClose={() => setShowCreateModal(false)} onSubmit={createMutation} />}
      {showEditModal && selectedUser && (
        <EditUserModal user={selectedUser} onClose={() => setShowEditModal(false)} onSubmit={updateMutation} />
      )}
      {showPasswordModal && selectedUser && (
        <PasswordModal
          user={selectedUser}
          currentUserId={currentUser?.id}
          onClose={() => setShowPasswordModal(false)}
          onSubmit={passwordMutation}
        />
      )}
      {showAccessLevelsModal && selectedUser && (
        <UserAccessLevelsModal user={selectedUser} onClose={() => setShowAccessLevelsModal(false)} />
      )}
      {showDeleteModal && selectedUser && (
        <DeleteUserModal
          user={selectedUser}
          onClose={() => setShowDeleteModal(false)}
          onConfirm={() => deleteMutation.mutate(selectedUser.id)}
          isLoading={deleteMutation.isPending}
        />
      )}
    </div>
  );
}

// Create User Modal
function CreateUserModal({ onClose, onSubmit }: any) {
  const [formData, setFormData] = useState<UserCreate>({
    username: '',
    email: '',
    password: '',
    first_name: '',
    last_name: '',
    role: 'user',
    phone: '',
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit.mutate(formData);
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-800 rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-gray-700 flex justify-between items-center sticky top-0 bg-gray-800">
          <h2 className="text-2xl font-bold text-white">Create User</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-white">
            <X className="w-6 h-6" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-gray-300 text-sm font-medium mb-2">Username *</label>
              <input
                type="text"
                required
                value={formData.username}
                onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-blue-500"
                placeholder="johndoe"
              />
            </div>

            <div>
              <label className="block text-gray-300 text-sm font-medium mb-2">Email *</label>
              <input
                type="email"
                required
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-blue-500"
                placeholder="john@example.com"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-gray-300 text-sm font-medium mb-2">First Name</label>
              <input
                type="text"
                value={formData.first_name}
                onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-blue-500"
                placeholder="John"
              />
            </div>

            <div>
              <label className="block text-gray-300 text-sm font-medium mb-2">Last Name</label>
              <input
                type="text"
                value={formData.last_name}
                onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-blue-500"
                placeholder="Doe"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-gray-300 text-sm font-medium mb-2">Role *</label>
              <select
                value={formData.role}
                onChange={(e) => setFormData({ ...formData, role: e.target.value as UserRole })}
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-blue-500"
              >
                <option value="user">User (View Only)</option>
                <option value="guard">Guard (Control)</option>
                <option value="operator">Operator (Control + Reports)</option>
                <option value="admin">Admin (Full Access)</option>
              </select>
            </div>

            <div>
              <label className="block text-gray-300 text-sm font-medium mb-2">Phone</label>
              <input
                type="tel"
                value={formData.phone}
                onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-blue-500"
                placeholder="+1-555-0100"
              />
            </div>
          </div>

          <div>
            <label className="block text-gray-300 text-sm font-medium mb-2">Password *</label>
            <input
              type="password"
              required
              minLength={8}
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-blue-500"
              placeholder="Minimum 8 characters"
            />
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
                  Create User
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// Edit User Modal
function EditUserModal({ user, onClose, onSubmit }: any) {
  const [formData, setFormData] = useState<UserUpdate>({
    email: user.email,
    first_name: user.first_name || '',
    last_name: user.last_name || '',
    role: user.role,
    phone: user.phone || '',
    is_active: user.is_active,
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit.mutate({ userId: user.id, data: formData });
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-800 rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-gray-700 flex justify-between items-center sticky top-0 bg-gray-800">
          <h2 className="text-2xl font-bold text-white">Edit User - {user.username}</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-white">
            <X className="w-6 h-6" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-gray-300 text-sm font-medium mb-2">Username</label>
            <input
              type="text"
              value={user.username}
              disabled
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-gray-400 cursor-not-allowed"
            />
          </div>

          <div>
            <label className="block text-gray-300 text-sm font-medium mb-2">Email *</label>
            <input
              type="email"
              required
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-gray-300 text-sm font-medium mb-2">First Name</label>
              <input
                type="text"
                value={formData.first_name}
                onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-gray-300 text-sm font-medium mb-2">Last Name</label>
              <input
                type="text"
                value={formData.last_name}
                onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-gray-300 text-sm font-medium mb-2">Role *</label>
              <select
                value={formData.role}
                onChange={(e) => setFormData({ ...formData, role: e.target.value as UserRole })}
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-blue-500"
              >
                <option value="user">User (View Only)</option>
                <option value="guard">Guard (Control)</option>
                <option value="operator">Operator (Control + Reports)</option>
                <option value="admin">Admin (Full Access)</option>
              </select>
            </div>

            <div>
              <label className="block text-gray-300 text-sm font-medium mb-2">Phone</label>
              <input
                type="tel"
                value={formData.phone}
                onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-blue-500"
              />
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
              <span>Account Active</span>
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

// Password Change Modal
function PasswordModal({ user, currentUserId, onClose, onSubmit }: any) {
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');

  const isCurrentUser = user.id === currentUserId;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (newPassword.length < 8) {
      setError('Password must be at least 8 characters');
      return;
    }

    if (newPassword !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    onSubmit.mutate({
      userId: user.id,
      data: { current_password: currentPassword, new_password: newPassword },
    });
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-800 rounded-lg shadow-xl max-w-md w-full">
        <div className="p-6 border-b border-gray-700 flex justify-between items-center">
          <h2 className="text-2xl font-bold text-white">Change Password</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-white">
            <X className="w-6 h-6" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div className="bg-blue-900/30 border border-blue-500 rounded-lg p-3 text-sm text-blue-200">
            Changing password for: <span className="font-semibold">{user.username}</span>
          </div>

          {error && (
            <div className="bg-red-900/50 border border-red-500 rounded-lg p-3 text-sm text-red-200">{error}</div>
          )}

          {isCurrentUser && (
            <div>
              <label className="block text-gray-300 text-sm font-medium mb-2">Current Password *</label>
              <input
                type="password"
                required
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-blue-500"
              />
            </div>
          )}

          <div>
            <label className="block text-gray-300 text-sm font-medium mb-2">New Password *</label>
            <input
              type="password"
              required
              minLength={8}
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-blue-500"
              placeholder="Minimum 8 characters"
            />
          </div>

          <div>
            <label className="block text-gray-300 text-sm font-medium mb-2">Confirm New Password *</label>
            <input
              type="password"
              required
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-blue-500"
            />
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
              className="px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition disabled:opacity-50 flex items-center"
            >
              {onSubmit.isPending ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Changing...
                </>
              ) : (
                <>
                  <Key className="w-4 h-4 mr-2" />
                  Change Password
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// User Access Levels Modal
function UserAccessLevelsModal({ user, onClose }: any) {
  const { data: accessLevels } = useQuery({
    queryKey: ['user-access-levels', user.id],
    queryFn: () => apiClientV2_1.getUserAccessLevels(user.id),
  });

  const { data: userDoors } = useQuery({
    queryKey: ['user-doors', user.id],
    queryFn: () => apiClientV2_1.getUserDoors(user.id),
  });

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-800 rounded-lg shadow-xl max-w-3xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-gray-700 flex justify-between items-center sticky top-0 bg-gray-800">
          <h2 className="text-2xl font-bold text-white">Access Levels - {user.username}</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-white">
            <X className="w-6 h-6" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          {/* Access Levels */}
          <div>
            <h3 className="text-lg font-semibold text-white mb-3 flex items-center">
              <UserCheck className="w-5 h-5 mr-2" />
              Assigned Access Levels
            </h3>
            {accessLevels && accessLevels.length > 0 ? (
              <div className="space-y-2">
                {accessLevels.map((level: any) => (
                  <div key={level.id} className="bg-gray-700 rounded-lg p-4 flex justify-between items-center">
                    <div>
                      <p className="text-white font-medium">{level.name}</p>
                      {level.description && <p className="text-gray-400 text-sm">{level.description}</p>}
                    </div>
                    <span className="text-blue-400 font-semibold">Priority: {level.priority}</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-400 text-sm">No access levels assigned</p>
            )}
          </div>

          {/* Accessible Doors */}
          <div>
            <h3 className="text-lg font-semibold text-white mb-3 flex items-center">
              <DoorOpen className="w-5 h-5 mr-2" />
              Accessible Doors
            </h3>
            {userDoors && userDoors.length > 0 ? (
              <div className="grid grid-cols-2 gap-3">
                {userDoors.map((door: any) => (
                  <div key={door.door_id} className="bg-gray-700 rounded-lg p-3">
                    <p className="text-white font-medium">{door.door_name}</p>
                    {door.location && <p className="text-gray-400 text-xs">{door.location}</p>}
                    <div className="mt-2 flex space-x-2 text-xs">
                      {door.entry_allowed && (
                        <span className="bg-green-900/50 text-green-400 px-2 py-0.5 rounded">Entry</span>
                      )}
                      {door.exit_allowed && (
                        <span className="bg-blue-900/50 text-blue-400 px-2 py-0.5 rounded">Exit</span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-400 text-sm">No doors accessible</p>
            )}
          </div>

          <div className="flex justify-end pt-4">
            <button onClick={onClose} className="px-4 py-2 bg-gray-700 text-gray-300 rounded-lg hover:bg-gray-600 transition">
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// Delete User Modal
function DeleteUserModal({ user, onClose, onConfirm, isLoading }: any) {
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-800 rounded-lg shadow-xl max-w-md w-full">
        <div className="p-6 border-b border-gray-700">
          <h2 className="text-2xl font-bold text-white">Confirm Delete</h2>
        </div>

        <div className="p-6">
          <p className="text-gray-300 mb-4">Are you sure you want to delete this user?</p>
          <div className="bg-gray-700 rounded-lg p-4 mb-6">
            <p className="text-white font-semibold">{user.username}</p>
            <p className="text-gray-400 text-sm">{user.email}</p>
            <p className="text-gray-400 text-sm">Role: {user.role}</p>
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
                Delete User
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
