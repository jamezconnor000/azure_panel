/**
 * Login Page
 * User authentication interface
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Lock, User, AlertCircle, Shield } from 'lucide-react';

export default function Login() {
  const navigate = useNavigate();
  const { login, isLoading } = useAuth();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [rememberMe, setRememberMe] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!username || !password) {
      setError('Please enter both username and password');
      return;
    }

    try {
      await login({ username, password });
      navigate('/dashboard');
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Login failed. Please check your credentials.';
      setError(errorMessage);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-900 via-blue-900 to-gray-900 p-4">
      <div className="max-w-md w-full">
        {/* Logo and Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-20 h-20 bg-blue-600 rounded-full mb-4 shadow-lg">
            <Shield className="w-12 h-12 text-white" />
          </div>
          <h1 className="text-4xl font-bold text-white mb-2">AetherAccess</h1>
          <p className="text-gray-400">Enterprise Access Control System</p>
          <p className="text-sm text-gray-500 mt-1">Version 2.1.0</p>
        </div>

        {/* Login Card */}
        <div className="bg-gray-800 rounded-lg shadow-2xl p-8 border border-gray-700">
          <h2 className="text-2xl font-bold text-white mb-6">Sign In</h2>

          {/* Error Message */}
          {error && (
            <div className="mb-6 bg-red-900/50 border border-red-500 rounded-lg p-4 flex items-start">
              <AlertCircle className="w-5 h-5 text-red-500 mt-0.5 mr-3 flex-shrink-0" />
              <p className="text-red-200 text-sm">{error}</p>
            </div>
          )}

          {/* Login Form */}
          <form onSubmit={handleSubmit}>
            {/* Username Input */}
            <div className="mb-4">
              <label className="block text-gray-300 text-sm font-medium mb-2" htmlFor="username">
                Username
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <User className="h-5 w-5 text-gray-500" />
                </div>
                <input
                  id="username"
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="block w-full pl-10 pr-3 py-3 border border-gray-600 rounded-lg
                           bg-gray-700 text-white placeholder-gray-400
                           focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
                           transition duration-150"
                  placeholder="Enter your username"
                  disabled={isLoading}
                  autoComplete="username"
                  autoFocus
                />
              </div>
            </div>

            {/* Password Input */}
            <div className="mb-6">
              <label className="block text-gray-300 text-sm font-medium mb-2" htmlFor="password">
                Password
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Lock className="h-5 w-5 text-gray-500" />
                </div>
                <input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="block w-full pl-10 pr-3 py-3 border border-gray-600 rounded-lg
                           bg-gray-700 text-white placeholder-gray-400
                           focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
                           transition duration-150"
                  placeholder="Enter your password"
                  disabled={isLoading}
                  autoComplete="current-password"
                />
              </div>
            </div>

            {/* Remember Me Checkbox */}
            <div className="mb-6 flex items-center">
              <input
                id="remember-me"
                type="checkbox"
                checked={rememberMe}
                onChange={(e) => setRememberMe(e.target.checked)}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-600 rounded
                         bg-gray-700 cursor-pointer"
                disabled={isLoading}
              />
              <label htmlFor="remember-me" className="ml-2 block text-sm text-gray-400 cursor-pointer">
                Remember me
              </label>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isLoading}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-4
                       rounded-lg transition duration-150 shadow-lg
                       focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-gray-800
                       disabled:opacity-50 disabled:cursor-not-allowed
                       flex items-center justify-center"
            >
              {isLoading ? (
                <>
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                  Signing in...
                </>
              ) : (
                'Sign In'
              )}
            </button>
          </form>

          {/* Default Credentials Hint (remove in production) */}
          <div className="mt-6 p-4 bg-yellow-900/30 border border-yellow-700/50 rounded-lg">
            <p className="text-xs text-yellow-200 font-medium mb-1">Default Credentials:</p>
            <p className="text-xs text-yellow-300">Username: <code className="bg-yellow-900/50 px-1 rounded">admin</code></p>
            <p className="text-xs text-yellow-300">Password: <code className="bg-yellow-900/50 px-1 rounded">admin123</code></p>
            <p className="text-xs text-yellow-200 mt-2">⚠️ Change default password after first login!</p>
          </div>
        </div>

        {/* Footer */}
        <div className="mt-6 text-center text-sm text-gray-500">
          <p>© 2025 AetherAccess. All rights reserved.</p>
          <p className="mt-1">Enterprise Access Control System v2.1</p>
        </div>
      </div>
    </div>
  );
}
