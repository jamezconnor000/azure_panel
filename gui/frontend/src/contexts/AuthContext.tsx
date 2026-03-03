/**
 * Authentication Context
 * Provides authentication state and methods throughout the app
 */

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import apiClientV2_1 from '../api/clientV2_1';
import type { UserInfo, LoginRequest } from '../types/v2.1';

interface AuthContextType {
  user: UserInfo | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: LoginRequest) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<UserInfo | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Check if user is already logged in on mount
  useEffect(() => {
    const checkAuth = async () => {
      if (apiClientV2_1.isAuthenticated()) {
        try {
          const currentUser = await apiClientV2_1.fetchCurrentUser();
          setUser(currentUser);
        } catch (error) {
          // Token is invalid, clear it
          await apiClientV2_1.logout();
          setUser(null);
        }
      }
      setIsLoading(false);
    };

    checkAuth();
  }, []);

  const login = async (credentials: LoginRequest) => {
    setIsLoading(true);
    try {
      const response = await apiClientV2_1.login(credentials);
      setUser(response.user);
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    setIsLoading(true);
    try {
      await apiClientV2_1.logout();
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  };

  const refreshUser = async () => {
    if (!apiClientV2_1.isAuthenticated()) {
      setUser(null);
      return;
    }

    try {
      const currentUser = await apiClientV2_1.fetchCurrentUser();
      setUser(currentUser);
    } catch (error) {
      setUser(null);
    }
  };

  const value = {
    user,
    isAuthenticated: !!user,
    isLoading,
    login,
    logout,
    refreshUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

// Hook to check permissions
export function usePermission(permission: string): boolean {
  const { user } = useAuth();
  if (!user) return false;

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

  const permissions = rolePermissions[user.role] || [];
  return permissions.includes(permission);
}
