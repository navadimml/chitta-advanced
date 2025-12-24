import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Search,
  User,
  Lightbulb,
  Eye,
  Sparkles,
  AlertCircle,
  ChevronRight,
  RefreshCw,
} from 'lucide-react';

import { api } from '../../api/client';

/**
 * Child Browser Component
 *
 * Lists all children with search/filter and summary stats.
 * Clicking a child navigates to the detail view.
 */
export default function ChildBrowser() {
  const navigate = useNavigate();
  const [children, setChildren] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState('');
  const [total, setTotal] = useState(0);

  useEffect(() => {
    loadChildren();
  }, []);

  async function loadChildren() {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getDashboardChildren(search);
      setChildren(data.children || []);
      setTotal(data.total || 0);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  function handleSearch(e) {
    e.preventDefault();
    loadChildren();
  }

  function handleChildClick(childId) {
    navigate(`/dashboard/children/${childId}`);
  }

  return (
    <div className="p-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Children</h1>
          <p className="text-gray-500">{total} children in the system</p>
        </div>
        <button
          onClick={loadChildren}
          className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 transition"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh
        </button>
      </div>

      {/* Search */}
      <form onSubmit={handleSearch} className="mb-6">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            placeholder="Search by child name..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-3 bg-white border border-gray-200 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
          />
        </div>
      </form>

      {/* Error State */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 text-red-700">
          Error loading children: {error}
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600" />
        </div>
      )}

      {/* Children List */}
      {!loading && !error && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
          {children.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              <User className="w-12 h-12 mx-auto mb-4 text-gray-300" />
              <p>No children found</p>
            </div>
          ) : (
            <div className="divide-y divide-gray-100">
              {children.map((child) => (
                <ChildRow
                  key={child.child_id}
                  child={child}
                  onClick={() => handleChildClick(child.child_id)}
                />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

/**
 * Child Row Component
 */
function ChildRow({ child, onClick }) {
  return (
    <button
      onClick={onClick}
      className="w-full flex items-center justify-between p-4 hover:bg-gray-50 transition text-left"
    >
      <div className="flex items-center gap-4">
        {/* Avatar */}
        <div className="w-12 h-12 rounded-full bg-gradient-to-br from-indigo-500 to-purple-500 flex items-center justify-center text-white font-bold text-lg">
          {child.child_name ? child.child_name[0] : '?'}
        </div>

        {/* Info */}
        <div>
          <div className="font-medium text-gray-900" dir="rtl">
            {child.child_name || 'Unnamed Child'}
          </div>
          <div className="text-sm text-gray-500">
            ID: {child.child_id.slice(0, 8)}...
            {child.child_age_months && (
              <span className="ml-2">
                Age: {Math.floor(child.child_age_months / 12)}y {Math.round(child.child_age_months % 12)}m
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="flex items-center gap-6">
        <StatBadge
          icon={<Eye className="w-4 h-4" />}
          value={child.observation_count}
          label="Observations"
          color="text-blue-600 bg-blue-50"
        />
        <StatBadge
          icon={<Lightbulb className="w-4 h-4" />}
          value={child.curiosity_count}
          label="Curiosities"
          color="text-amber-600 bg-amber-50"
        />
        <StatBadge
          icon={<Sparkles className="w-4 h-4" />}
          value={child.pattern_count}
          label="Patterns"
          color="text-purple-600 bg-purple-50"
        />
        {child.unresolved_flags > 0 && (
          <StatBadge
            icon={<AlertCircle className="w-4 h-4" />}
            value={child.unresolved_flags}
            label="Flags"
            color="text-red-600 bg-red-50"
          />
        )}
        {child.has_crystal && (
          <div className="px-2 py-1 bg-emerald-50 text-emerald-600 rounded text-xs font-medium">
            Crystal
          </div>
        )}
        <ChevronRight className="w-5 h-5 text-gray-400" />
      </div>
    </button>
  );
}

/**
 * Stat Badge Component
 */
function StatBadge({ icon, value, label, color }) {
  return (
    <div className={`flex items-center gap-1.5 px-2 py-1 rounded ${color}`} title={label}>
      {icon}
      <span className="font-medium">{value}</span>
    </div>
  );
}
