import { Outlet, Link, useLocation } from 'react-router-dom';
import { Activity, LayoutDashboard, Cpu, Power, DoorOpen, Users, Shield, LogOut, User, CreditCard, Network } from 'lucide-react';
import { useAuth, usePermission } from '../contexts/AuthContext';

export default function Layout() {
  const location = useLocation();
  const { user, logout } = useAuth();
  const canReadDoors = usePermission('door.read');
  const canReadUsers = usePermission('user.read');
  const canReadAccessLevels = usePermission('access_level.read');
  const canReadCardHolders = usePermission('card_holder.read');

  const navigation = [
    { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard, show: true },
    { name: 'Hardware Tree', href: '/hardware-tree', icon: Network, show: true },
    { name: 'Readers', href: '/readers', icon: Cpu, show: true },
    { name: 'I/O Control', href: '/io-control', icon: Power, show: true },
    { name: 'Door Management', href: '/doors', icon: DoorOpen, show: canReadDoors },
    { name: 'User Management', href: '/users', icon: Users, show: canReadUsers },
    { name: 'Access Levels', href: '/access-levels', icon: Shield, show: canReadAccessLevels },
    { name: 'Card Holders', href: '/card-holders', icon: CreditCard, show: canReadCardHolders },
  ];

  const isActive = (path: string) => location.pathname === path;

  const getRoleBadgeColor = (role: string) => {
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
    <div className="min-h-screen bg-slate-900">
      {/* Header */}
      <header className="bg-slate-800 border-b border-slate-700 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <Activity className="h-8 w-8 text-blue-500" />
              <span className="ml-3 text-xl font-bold text-white">
                AetherAccess Control Panel
              </span>
              <span className="ml-3 text-xs text-gray-400">v2.1</span>
            </div>

            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                <span className="text-sm text-slate-300">System Online</span>
              </div>

              {/* User menu */}
              {user && (
                <div className="flex items-center space-x-3 border-l border-gray-700 pl-4">
                  <div className="flex items-center space-x-2">
                    <User className="h-5 w-5 text-gray-400" />
                    <div className="text-right">
                      <p className="text-sm font-medium text-white">{user.username}</p>
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border ${getRoleBadgeColor(
                          user.role
                        )}`}
                      >
                        {user.role}
                      </span>
                    </div>
                  </div>
                  <button
                    onClick={() => logout()}
                    className="p-2 rounded-lg text-gray-400 hover:text-white hover:bg-slate-700 transition"
                    title="Logout"
                  >
                    <LogOut className="h-5 w-5" />
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      <div className="flex">
        {/* Sidebar */}
        <aside className="w-64 bg-slate-800 border-r border-slate-700 min-h-[calc(100vh-4rem)]">
          <nav className="px-4 py-6 space-y-1">
            {navigation
              .filter((item) => item.show)
              .map((item) => {
                const Icon = item.icon;
                const active = isActive(item.href);

                return (
                  <Link
                    key={item.name}
                    to={item.href}
                    className={`
                      flex items-center px-4 py-3 text-sm font-medium rounded-lg transition-colors
                      ${
                        active
                          ? 'bg-blue-600 text-white'
                          : 'text-slate-300 hover:bg-slate-700 hover:text-white'
                      }
                    `}
                  >
                    <Icon className="h-5 w-5 mr-3" />
                    {item.name}
                  </Link>
                );
              })}
          </nav>

          {/* Sidebar Footer */}
          <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-slate-700 bg-slate-800">
            <div className="text-xs text-gray-400 text-center">
              <p>AetherAccess v2.1</p>
              <p className="mt-1">© 2025 Enterprise Access Control</p>
            </div>
          </div>
        </aside>

        {/* Main content */}
        <main className="flex-1 p-8 bg-gray-900">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
