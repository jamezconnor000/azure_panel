import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Layout } from './components/Layout';
import { FrostParticles } from './components/FrostParticles';
import {
  UnifiedDashboard,
  People,
  Events,
  Settings,
  Login,
} from './pages';
import { useAuth } from './hooks/useAuth';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

// DEMO MODE - Set to true to bypass authentication
const DEMO_MODE = true;

function ProtectedRoutes() {
  const { isAuthenticated, isLoading, login, logout, error } = useAuth();

  if (isLoading && !DEMO_MODE) {
    return (
      <div className="min-h-screen bg-aether-darker flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-2 border-aether-primary border-t-transparent"></div>
      </div>
    );
  }

  if (!isAuthenticated && !DEMO_MODE) {
    return <Login onLogin={login} error={error} />;
  }

  return (
    <Layout onLogout={logout}>
      <Routes>
        <Route path="/" element={<UnifiedDashboard />} />
        <Route path="/people" element={<People />} />
        <Route path="/events" element={<Events />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Layout>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <FrostParticles />
      <BrowserRouter>
        <ProtectedRoutes />
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
