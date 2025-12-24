import React, { useState, useEffect } from 'react';
import { Routes, Route, NavLink, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  Users,
  Lightbulb,
  Clock,
  Grid,
  Sparkles,
  MessageSquare,
  FileText,
  BarChart3,
  LogOut,
  ChevronLeft,
  AlertCircle,
  Search,
} from 'lucide-react';

import { api } from '../../api/client';
import ChildBrowser from './ChildBrowser';
import ChildDetail from './ChildDetail';

/**
 * Main Dashboard Component
 *
 * Team-internal dashboard for expert reviewers to:
 * - Browse all children
 * - View curiosities, understanding, patterns
 * - Add clinical notes and flags
 * - Analyze aggregate data
 */
export default function Dashboard({ onLogout }) {
  const navigate = useNavigate();
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Sidebar */}
      <aside
        className={`bg-slate-800 text-white transition-all duration-300 ${
          sidebarCollapsed ? 'w-16' : 'w-64'
        } flex flex-col`}
      >
        {/* Logo/Header */}
        <div className="h-16 flex items-center justify-between px-4 border-b border-slate-700">
          {!sidebarCollapsed && (
            <span className="text-xl font-bold text-indigo-400">Chitta Dashboard</span>
          )}
          <button
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            className="p-2 hover:bg-slate-700 rounded-lg transition"
          >
            <ChevronLeft
              className={`w-5 h-5 transition-transform ${
                sidebarCollapsed ? 'rotate-180' : ''
              }`}
            />
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 py-4">
          <NavItem
            to="/dashboard"
            icon={<LayoutDashboard className="w-5 h-5" />}
            label="Overview"
            collapsed={sidebarCollapsed}
            end
          />
          <NavItem
            to="/dashboard/children"
            icon={<Users className="w-5 h-5" />}
            label="Children"
            collapsed={sidebarCollapsed}
          />
          <NavItem
            to="/dashboard/analytics"
            icon={<BarChart3 className="w-5 h-5" />}
            label="Analytics"
            collapsed={sidebarCollapsed}
          />

          <div className="my-4 border-t border-slate-700" />

          {!sidebarCollapsed && (
            <div className="px-4 py-2 text-xs uppercase text-slate-400 font-semibold">
              Quick Access
            </div>
          )}

          <NavItem
            to="/dashboard/flags"
            icon={<AlertCircle className="w-5 h-5" />}
            label="Unresolved Flags"
            collapsed={sidebarCollapsed}
          />
        </nav>

        {/* Footer */}
        <div className="p-4 border-t border-slate-700">
          <button
            onClick={() => navigate('/')}
            className={`w-full flex items-center gap-3 px-3 py-2 text-slate-300 hover:bg-slate-700 rounded-lg transition ${
              sidebarCollapsed ? 'justify-center' : ''
            }`}
          >
            <ChevronLeft className="w-5 h-5" />
            {!sidebarCollapsed && <span>Back to App</span>}
          </button>
          <button
            onClick={onLogout}
            className={`w-full flex items-center gap-3 px-3 py-2 mt-2 text-red-400 hover:bg-slate-700 rounded-lg transition ${
              sidebarCollapsed ? 'justify-center' : ''
            }`}
          >
            <LogOut className="w-5 h-5" />
            {!sidebarCollapsed && <span>Logout</span>}
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        <Routes>
          <Route index element={<DashboardOverview />} />
          <Route path="children" element={<ChildBrowser />} />
          <Route path="children/:childId/*" element={<ChildDetail />} />
          <Route path="analytics" element={<AnalyticsPlaceholder />} />
          <Route path="flags" element={<FlagsPlaceholder />} />
        </Routes>
      </main>
    </div>
  );
}

/**
 * Navigation Item Component
 */
function NavItem({ to, icon, label, collapsed, end = false }) {
  return (
    <NavLink
      to={to}
      end={end}
      className={({ isActive }) =>
        `flex items-center gap-3 px-4 py-3 mx-2 rounded-lg transition ${
          isActive
            ? 'bg-indigo-600 text-white'
            : 'text-slate-300 hover:bg-slate-700'
        } ${collapsed ? 'justify-center' : ''}`
      }
      title={collapsed ? label : undefined}
    >
      {icon}
      {!collapsed && <span>{label}</span>}
    </NavLink>
  );
}

/**
 * Dashboard Overview (Home)
 */
function DashboardOverview() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function loadStats() {
      try {
        const data = await api.getDashboardAnalytics();
        setStats(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    loadStats();
  }, []);

  if (loading) {
    return (
      <div className="p-8 flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
          Error loading dashboard: {error}
        </div>
      </div>
    );
  }

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Dashboard Overview</h1>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatCard
          icon={<Users className="w-6 h-6 text-indigo-600" />}
          label="Total Children"
          value={stats?.total_children || 0}
        />
        <StatCard
          icon={<Lightbulb className="w-6 h-6 text-amber-600" />}
          label="Total Curiosities"
          value={stats?.total_curiosities || 0}
        />
        <StatCard
          icon={<Grid className="w-6 h-6 text-emerald-600" />}
          label="Total Observations"
          value={stats?.total_observations || 0}
        />
        <StatCard
          icon={<AlertCircle className="w-6 h-6 text-red-600" />}
          label="Unresolved Flags"
          value={stats?.total_unresolved_flags || 0}
        />
      </div>

      {/* More stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <StatCard
          icon={<Sparkles className="w-6 h-6 text-purple-600" />}
          label="Patterns Detected"
          value={stats?.total_patterns || 0}
        />
        <StatCard
          icon={<FileText className="w-6 h-6 text-blue-600" />}
          label="Children with Crystal"
          value={stats?.children_with_crystal || 0}
        />
        <StatCard
          icon={<BarChart3 className="w-6 h-6 text-teal-600" />}
          label="Avg Observations/Child"
          value={stats?.avg_observations_per_child || 0}
        />
      </div>
    </div>
  );
}

/**
 * Stat Card Component
 */
function StatCard({ icon, label, value }) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
      <div className="flex items-center gap-4">
        <div className="p-3 bg-gray-50 rounded-lg">{icon}</div>
        <div>
          <div className="text-2xl font-bold text-gray-900">{value}</div>
          <div className="text-sm text-gray-500">{label}</div>
        </div>
      </div>
    </div>
  );
}

/**
 * Placeholder components for routes not yet implemented
 */
function AnalyticsPlaceholder() {
  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold text-gray-900 mb-4">Analytics</h1>
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-8 text-center text-gray-500">
        <BarChart3 className="w-12 h-12 mx-auto mb-4 text-gray-300" />
        <p>Analytics dashboard coming soon...</p>
      </div>
    </div>
  );
}

function FlagsPlaceholder() {
  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold text-gray-900 mb-4">Unresolved Flags</h1>
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-8 text-center text-gray-500">
        <AlertCircle className="w-12 h-12 mx-auto mb-4 text-gray-300" />
        <p>Flag management coming soon...</p>
      </div>
    </div>
  );
}
