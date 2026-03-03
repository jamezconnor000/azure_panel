import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { useEffect } from 'react'
import { AuthProvider } from './contexts/AuthContext'
import { ProtectedRoute } from './components/ProtectedRoute'
import Layout from './components/Layout'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Readers from './pages/Readers'
import IOControl from './pages/IOControl'
import DoorManagement from './pages/DoorManagement'
import UserManagement from './pages/UserManagement'
import AccessLevels from './pages/AccessLevels'
import CardHolders from './pages/CardHolders'
import HardwareTree from './pages/HardwareTree'
import { apiClient } from './api/client'

function App() {
  useEffect(() => {
    // Connect to WebSocket for real-time updates
    apiClient.connectWebSocket();

    return () => {
      apiClient.disconnectWebSocket();
    };
  }, []);

  return (
    <AuthProvider>
      <Router>
        <Routes>
          {/* Public route */}
          <Route path="/login" element={<Login />} />

            {/* Protected routes */}
            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <Layout />
                </ProtectedRoute>
              }
            >
              <Route index element={<Navigate to="/dashboard" replace />} />
              <Route path="dashboard" element={<Dashboard />} />
              <Route path="hardware-tree" element={<HardwareTree />} />
              <Route path="readers" element={<Readers />} />
              <Route path="io-control" element={<IOControl />} />

              {/* New v2.1 routes */}
              <Route
                path="doors"
                element={
                  <ProtectedRoute requiredPermission="door.read">
                    <DoorManagement />
                  </ProtectedRoute>
                }
              />
              <Route
                path="users"
                element={
                  <ProtectedRoute requiredPermission="user.read">
                    <UserManagement />
                  </ProtectedRoute>
                }
              />
              <Route
                path="access-levels"
                element={
                  <ProtectedRoute requiredPermission="access_level.read">
                    <AccessLevels />
                  </ProtectedRoute>
                }
              />
              <Route
                path="card-holders"
                element={
                  <ProtectedRoute requiredPermission="card_holder.read">
                    <CardHolders />
                  </ProtectedRoute>
                }
              />
            </Route>
          </Routes>
        </Router>
      </AuthProvider>
  )
}

export default App
