import { useState } from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import {
  LayoutDashboard,
  Users,
  FileText,
  Files,
  BrainCircuit,
  Settings,
  ShieldCheck,
  UsersRound,
  Bell,
  Search,
  Menu,
  Stethoscope,
  LogOut
} from 'lucide-react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { useAuthStore } from '../store/authStore';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

const mainNavItems = [
  { icon: LayoutDashboard, label: 'Dashboard', to: '/' },
  { icon: Users, label: 'Patients', to: '/patients' },
  { icon: FileText, label: 'Cases', to: '/cases' },
  { icon: Files, label: 'Documents', to: '/documents' },
  { icon: BrainCircuit, label: 'AI Analysis', to: '/analysis' },
];

const secondaryNavItems = [
  { icon: UsersRound, label: 'Team', to: '/team' },
  { icon: ShieldCheck, label: 'Audit Logs', to: '/audit' },
  { icon: Settings, label: 'Settings', to: '/settings' },
];

export default function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const { user, logout } = useAuthStore();

  return (
    <div className="min-h-screen bg-[var(--color-page-bg)] flex flex-col md:flex-row">
      {/* Sidebar */}
      <aside
        className={cn(
          "bg-white border-r border-[var(--color-border-color)] flex flex-col transition-all duration-300",
          sidebarOpen ? "w-64" : "w-20",
          "hidden md:flex"
        )}
      >
        <div className="h-16 flex items-center justify-between px-4 border-b border-[var(--color-border-color)]">
          <div className="flex items-center gap-2 text-primary">
            <Stethoscope className="w-8 h-8 text-[var(--color-primary)]" />
            {sidebarOpen && <span className="font-bold text-xl text-[var(--color-primary-dark)] tracking-tight">MedAI</span>}
          </div>
          <button onClick={() => setSidebarOpen(!sidebarOpen)} className="p-1 hover:bg-gray-100 rounded-lg text-gray-500">
            <Menu className="w-5 h-5" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto py-4 flex flex-col gap-1 px-3">
          {mainNavItems.map((item) => (
            <NavLink
              key={item.label}
              to={item.to}
              className={({ isActive }) => cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors duration-200",
                isActive
                  ? "bg-blue-50 text-[var(--color-primary)] font-medium"
                  : "text-[var(--color-text-secondary)] hover:bg-gray-50 hover:text-gray-900"
              )}
            >
              <item.icon className="w-5 h-5 flex-shrink-0" />
              {sidebarOpen && <span>{item.label}</span>}
            </NavLink>
          ))}

          <div className="my-4 border-t border-[var(--color-border-color)] mx-3" />

          {secondaryNavItems.map((item) => (
            <NavLink
              key={item.label}
              to={item.to}
              className={({ isActive }) => cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors duration-200",
                isActive
                  ? "bg-blue-50 text-[var(--color-primary)] font-medium"
                  : "text-[var(--color-text-secondary)] hover:bg-gray-50 hover:text-gray-900"
              )}
            >
              <item.icon className="w-5 h-5 flex-shrink-0" />
              {sidebarOpen && <span>{item.label}</span>}
            </NavLink>
          ))}
        </div>

        <div className="p-4 border-t border-[var(--color-border-color)]">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0 text-[var(--color-primary)] font-bold uppercase">
              {user?.name?.substring(0, 2) || 'U'}
            </div>
            {sidebarOpen && (
              <div className="flex flex-col overflow-hidden">
                <span className="text-sm font-semibold text-gray-900 truncate">{user?.name}</span>
                <span className="text-xs text-gray-500 capitalize">{user?.role}</span>
              </div>
            )}
          </div>
          {sidebarOpen && (
            <button
              onClick={logout}
              className="w-full flex items-center justify-center gap-2 text-sm text-red-600 hover:bg-red-50 py-2 rounded-lg transition-colors"
            >
              <LogOut className="w-4 h-4" />
              Logout
            </button>
          )}
          {!sidebarOpen && (
            <button
              onClick={logout}
              className="w-full flex items-center justify-center text-red-600 hover:bg-red-50 py-2 rounded-lg transition-colors"
              title="Logout"
            >
              <LogOut className="w-5 h-5" />
            </button>
          )}
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 flex flex-col min-w-0">
        {/* Top Header */}
        <header className="h-16 bg-white border-b border-[var(--color-border-color)] flex items-center justify-between px-6 sticky top-0 z-10">
          {/* Mobile menu toggle */}
          <button className="md:hidden p-2 -ml-2 text-gray-500 hover:bg-gray-100 rounded-lg">
            <Menu className="w-5 h-5" />
          </button>

          <div className="flex-1 flex items-center">
            <div className="max-w-md w-full relative hidden md:block">
              <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
              <input
                type="text"
                placeholder="Search patients, cases, documents..."
                className="w-full pl-10 pr-4 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)] focus:border-transparent transition-all"
              />
            </div>
          </div>

          <div className="flex items-center gap-4">
            <button className="relative p-2 text-gray-400 hover:text-gray-600 transition-colors">
              <Bell className="w-5 h-5" />
              <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-[var(--color-danger)] rounded-full border-2 border-white"></span>
            </button>
          </div>
        </header>

        {/* Page content */}
        <div className="flex-1 overflow-auto p-6">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
