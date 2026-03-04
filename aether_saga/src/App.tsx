import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Layout } from './components/Layout';
import {
  Dashboard,
  Cardholders,
  AccessLevels,
  Doors,
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

function ProtectedRoutes() {
  const { isAuthenticated, isLoading, login, logout, error } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-aether-darker flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-2 border-aether-primary border-t-transparent"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Login onLogin={login} error={error} />;
  }

  return (
    <Layout onLogout={logout}>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/cardholders" element={<Cardholders />} />
        <Route path="/access-levels" element={<AccessLevels />} />
        <Route path="/doors" element={<Doors />} />
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
      <BrowserRouter>
        <ProtectedRoutes />
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
