/**
 * ChildSwitcher - Header component for switching between children
 *
 * Shows:
 * - Active child name (or placeholder if no name yet)
 * - Dropdown to switch between children
 * - "הוסף ילד" option to add a new child
 */

import React, { useState } from 'react';
import { ChevronDown, Plus, User } from 'lucide-react';
import { useFamily } from '../../contexts/FamilyContext';

export default function ChildSwitcher() {
  const {
    children,
    activeChild,
    activeChildId,
    addChild,
    switchChild,
    hasMultipleChildren
  } = useFamily();

  const [isOpen, setIsOpen] = useState(false);
  const [isAdding, setIsAdding] = useState(false);

  const handleAddChild = async () => {
    setIsAdding(true);
    try {
      await addChild();
      setIsOpen(false);
    } catch (error) {
      console.error('Failed to add child:', error);
    } finally {
      setIsAdding(false);
    }
  };

  const handleSwitchChild = (childId) => {
    switchChild(childId);
    setIsOpen(false);
    // React's key={activeChildId} on AuthenticatedApp handles state reset
  };

  // Get display name for a child
  const getChildDisplayName = (child) => {
    if (child?.name) return child.name;
    return 'ילד/ה חדש/ה';
  };

  return (
    <div className="relative">
      {/* Trigger Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-1.5 rounded-lg hover:bg-gray-100 transition"
      >
        <div className="w-6 h-6 bg-gradient-to-br from-purple-400 to-indigo-500 rounded-full flex items-center justify-center">
          <User className="w-3.5 h-3.5 text-white" />
        </div>
        <span className="text-sm font-medium text-gray-700">
          {getChildDisplayName(activeChild)}
        </span>
        <ChevronDown className={`w-4 h-4 text-gray-500 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {/* Dropdown */}
      {isOpen && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 z-40"
            onClick={() => setIsOpen(false)}
          />

          {/* Menu */}
          <div className="absolute left-0 top-full mt-1 bg-white rounded-xl shadow-lg border border-gray-200 py-2 min-w-[200px] z-50">
            {/* Children List */}
            {children.map((child) => (
              <button
                key={child.id}
                onClick={() => handleSwitchChild(child.id)}
                className={`w-full px-4 py-2 flex items-center gap-3 hover:bg-gray-50 transition ${
                  child.id === activeChildId ? 'bg-indigo-50' : ''
                }`}
              >
                <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                  child.id === activeChildId
                    ? 'bg-gradient-to-br from-purple-400 to-indigo-500'
                    : 'bg-gray-200'
                }`}>
                  <User className={`w-4 h-4 ${child.id === activeChildId ? 'text-white' : 'text-gray-500'}`} />
                </div>
                <div className="text-right flex-1">
                  <p className={`text-sm font-medium ${child.id === activeChildId ? 'text-indigo-700' : 'text-gray-700'}`}>
                    {getChildDisplayName(child)}
                  </p>
                  {child.age_months && (
                    <p className="text-xs text-gray-500">
                      {Math.floor(child.age_months / 12)} שנים
                    </p>
                  )}
                </div>
                {child.id === activeChildId && (
                  <div className="w-2 h-2 bg-indigo-500 rounded-full" />
                )}
              </button>
            ))}

            {/* Divider */}
            <div className="border-t border-gray-100 my-2" />

            {/* Add Child Button */}
            <button
              onClick={handleAddChild}
              disabled={isAdding}
              className="w-full px-4 py-2 flex items-center gap-3 hover:bg-gray-50 transition text-indigo-600"
            >
              <div className="w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center">
                {isAdding ? (
                  <div className="w-4 h-4 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
                ) : (
                  <Plus className="w-4 h-4 text-indigo-500" />
                )}
              </div>
              <span className="text-sm font-medium">
                {isAdding ? 'מוסיף...' : 'הוסף ילד/ה'}
              </span>
            </button>
          </div>
        </>
      )}
    </div>
  );
}
