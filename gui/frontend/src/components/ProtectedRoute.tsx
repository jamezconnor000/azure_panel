/**
 * Protected Route Component
 * Redirects to login if user is not authenticated
 */

import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredPermission?: string;
}

export function ProtectedRoute({ children, requiredPermission }: ProtectedRouteProps) {
  const { isAuthenticated, isLoading, user } = useAuth();

  // Show loading state while checking auth
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-900">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-400">Loading...</p>
        </div>
      </div>
    );
  }

  // Redirect to login if not authenticated
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  // Check permission if required
  if (requiredPermission && user) {
    const rolePermissions: Record<string, string[]> = {
      admin: [
        'user.create', 'user.read', 'user.update', 'user.delete',
        'door.create', 'door.read', 'door.update', 'door.delete',
        'access_level.create', 'access_level.read', 'access_level.update', 'access_level.delete',
        'door.control', 'door.configure', 'system.configure',
        'audit.read', 'reports.generate'
      ],
      operator: [
        'user.read', 'door.read', 'access_level.read',
        'door.control', 'audit.read', 'reports.generate'
      ],
      guard: [
        'door.read', 'door.control', 'audit.read'
      ],
      user: [
        'door.read'
      ]
    };

    const hasPermission = rolePermissions[user.role]?.includes(requiredPermission) || false;

    if (!hasPermission) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-900">
          <div className="bg-gray-800 p-8 rounded-lg shadow-lg max-w-md">
            <h2 className="text-2xl font-bold text-red-500 mb-4">Access Denied</h2>
            <p className="text-gray-300">
              You don't have permission to access this page.
            </p>
            <p className="text-gray-400 mt-2">
              Required permission: <code className="text-blue-400">{requiredPermission}</code>
            </p>
            <p className="text-gray-400 mt-1">
              Your role: <code className="text-green-400">{user.role}</code>
            </p>
          </div>
        </div>
      );
    }
  }

  return <>{children}</>;
}
