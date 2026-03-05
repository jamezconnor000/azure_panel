/**
 * Layout - Situ8-style navigation with Norse accents
 */

import { Link, Outlet, useLocation } from 'react-router-dom';
import { LogOut, Menu, X, BookOpen } from 'lucide-react';
import { RunicShield, RunicPerson, RunicActivity, RunicSettings } from './RunicIcons';
import { useState } from 'react';
import { FamiliarChat, FamiliarButton } from './FamiliarChat';

interface NavItem {
  path: string;
  label: string;
  icon: React.ReactNode;
  rune: string;
}

const navItems: NavItem[] = [
  { path: '/', label: 'Command Center', icon: <RunicShield size={18} />, rune: 'ᛉ' },
  { path: '/people', label: 'People', icon: <RunicPerson size={18} />, rune: 'ᛗ' },
  { path: '/events', label: 'Events', icon: <RunicActivity size={18} />, rune: 'ᚱ' },
  { path: '/chronicle', label: 'Chronicle', icon: <BookOpen size={18} />, rune: 'ᛋ' },
  { path: '/settings', label: 'Settings', icon: <RunicSettings size={18} />, rune: 'ᚲ' },
];

interface LayoutProps {
  onLogout?: () => void;
  children?: React.ReactNode;
}

export function Layout({ onLogout, children }: LayoutProps) {
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [familiarOpen, setFamiliarOpen] = useState(false);

  return (
    <div className="flex h-screen" style={{ background: '#0d1117' }}>
      {/* Mobile menu button */}
      <button
        className="lg:hidden fixed top-4 left-4 z-50 p-2 rounded-md"
        style={{ background: '#21262d', border: '1px solid #30363d', color: '#e6edf3' }}
        onClick={() => setSidebarOpen(!sidebarOpen)}
      >
        {sidebarOpen ? <X size={24} /> : <Menu size={24} />}
      </button>

      {/* Sidebar */}
      <aside
        className={`
          fixed lg:static inset-y-0 left-0 z-40
          w-64 transform transition-transform duration-300 ease-out
          ${sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
        `}
        style={{ background: '#161b22', borderRight: '1px solid #30363d' }}
      >
        {/* Logo */}
        <div className="flex items-center gap-3 px-4 py-4" style={{ borderBottom: '1px solid #30363d' }}>
          <div
            className="w-8 h-8 flex items-center justify-center rounded-md"
            style={{ background: 'rgba(139, 92, 246, 0.15)', border: '1px solid rgba(139, 92, 246, 0.3)' }}
          >
            <span style={{ color: '#8b5cf6', fontSize: '16px' }}>ᛟ</span>
          </div>
          <div>
            <h1 className="text-sm font-semibold" style={{ color: '#e6edf3' }}>
              Aether Saga
            </h1>
          </div>
        </div>

        {/* Navigation sections */}
        <nav className="py-2">
          {/* Operations section */}
          <div className="px-4 py-2">
            <span className="text-xs font-semibold uppercase tracking-wider" style={{ color: '#484f58' }}>
              Operations
            </span>
          </div>

          {navItems.slice(0, 1).map((item) => {
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                onClick={() => setSidebarOpen(false)}
                className="flex items-center gap-3 mx-2 px-3 py-2 rounded-md transition-colors"
                style={{
                  background: isActive ? 'rgba(139, 92, 246, 0.15)' : 'transparent',
                  color: isActive ? '#e6edf3' : '#7d8590',
                }}
              >
                <span style={{ color: isActive ? '#8b5cf6' : '#7d8590', opacity: 0.7 }}>
                  {item.icon}
                </span>
                <span className="text-sm font-medium">{item.label}</span>
                {isActive && (
                  <span className="ml-auto text-xs" style={{ color: '#8b5cf6', opacity: 0.5 }}>
                    {item.rune}
                  </span>
                )}
              </Link>
            );
          })}

          {/* Intelligence section */}
          <div className="px-4 py-2 mt-4">
            <span className="text-xs font-semibold uppercase tracking-wider" style={{ color: '#484f58' }}>
              Intelligence
            </span>
          </div>

          {navItems.slice(1, 4).map((item) => {
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                onClick={() => setSidebarOpen(false)}
                className="flex items-center gap-3 mx-2 px-3 py-2 rounded-md transition-colors"
                style={{
                  background: isActive ? 'rgba(139, 92, 246, 0.15)' : 'transparent',
                  color: isActive ? '#e6edf3' : '#7d8590',
                }}
              >
                <span style={{ color: isActive ? '#8b5cf6' : '#7d8590', opacity: 0.7 }}>
                  {item.icon}
                </span>
                <span className="text-sm font-medium">{item.label}</span>
                {isActive && (
                  <span className="ml-auto text-xs" style={{ color: '#8b5cf6', opacity: 0.5 }}>
                    {item.rune}
                  </span>
                )}
              </Link>
            );
          })}

          {/* System section */}
          <div className="px-4 py-2 mt-4">
            <span className="text-xs font-semibold uppercase tracking-wider" style={{ color: '#484f58' }}>
              System
            </span>
          </div>

          {navItems.slice(4).map((item) => {
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                onClick={() => setSidebarOpen(false)}
                className="flex items-center gap-3 mx-2 px-3 py-2 rounded-md transition-colors"
                style={{
                  background: isActive ? 'rgba(139, 92, 246, 0.15)' : 'transparent',
                  color: isActive ? '#e6edf3' : '#7d8590',
                }}
              >
                <span style={{ color: isActive ? '#8b5cf6' : '#7d8590', opacity: 0.7 }}>
                  {item.icon}
                </span>
                <span className="text-sm font-medium">{item.label}</span>
                {isActive && (
                  <span className="ml-auto text-xs" style={{ color: '#8b5cf6', opacity: 0.5 }}>
                    {item.rune}
                  </span>
                )}
              </Link>
            );
          })}
        </nav>

        {/* Decorative rune band */}
        <div className="absolute bottom-20 left-0 right-0 px-4">
          <div className="h-px" style={{ background: 'linear-gradient(to right, transparent, #30363d, transparent)' }} />
          <p className="text-center text-xs mt-2 tracking-widest font-cinzel" style={{ color: '#484f58', opacity: 0.5 }}>
            ᛏᚺᛖ ᛗᚨᚲᚺᛁᚾᛖᛊ ᚨᚾᛊᚹᛖᚱ
          </p>
        </div>

        {/* Logout */}
        {onLogout && (
          <div className="absolute bottom-0 left-0 right-0 p-3" style={{ borderTop: '1px solid #30363d' }}>
            <button
              onClick={onLogout}
              className="flex items-center gap-3 px-3 py-2 w-full rounded-md transition-colors"
              style={{ color: '#ef4444' }}
            >
              <LogOut size={18} />
              <span className="text-sm font-medium">Logout</span>
            </button>
          </div>
        )}
      </aside>

      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="lg:hidden fixed inset-0 z-30"
          style={{ background: 'rgba(0, 0, 0, 0.8)' }}
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Main content */}
      <main className="flex-1 overflow-auto min-h-0" style={{ background: '#0d1117' }}>
        <div className="h-full p-6 lg:p-8 overflow-auto">
          {children || <Outlet />}
        </div>
      </main>

      {/* Aether Familiar AI Assistant */}
      {familiarOpen ? (
        <FamiliarChat isOpen={familiarOpen} onClose={() => setFamiliarOpen(false)} />
      ) : (
        <FamiliarButton onClick={() => setFamiliarOpen(true)} />
      )}
    </div>
  );
}
