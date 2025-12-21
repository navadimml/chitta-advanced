/**
 * Family Context
 * Manages family and children state for the authenticated user.
 *
 * Key responsibilities:
 * - Auto-fetches family on mount (creates if needed on backend)
 * - Tracks active child (persisted to localStorage)
 * - Provides methods to add children and switch between them
 */

import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { api } from '../api/client';

const FamilyContext = createContext(null);

// LocalStorage key for persisting active child
const ACTIVE_CHILD_KEY = 'chitta_active_child';

export function FamilyProvider({ children }) {
  const [family, setFamily] = useState(null);
  const [childrenList, setChildrenList] = useState([]);
  const [activeChildId, setActiveChildId] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  /**
   * Fetch family data from backend.
   * Auto-creates family + child placeholder for new users.
   */
  const fetchFamily = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      const data = await api.getMyFamily();
      console.log('👨‍👩‍👧 Family data fetched:', data.children.map(c => ({ id: c.id.slice(0,8), name: c.name })));

      setFamily(data.family);
      setChildrenList(data.children);

      // Restore active child from localStorage or pick first
      const savedChildId = localStorage.getItem(ACTIVE_CHILD_KEY);
      const childIds = data.children.map(c => c.id);

      if (savedChildId && childIds.includes(savedChildId)) {
        setActiveChildId(savedChildId);
      } else if (childIds.length > 0) {
        const firstChildId = childIds[0];
        setActiveChildId(firstChildId);
        localStorage.setItem(ACTIVE_CHILD_KEY, firstChildId);
      }

    } catch (err) {
      console.error('Failed to fetch family:', err);
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Add a new child placeholder to the family.
   * Switches to the new child automatically.
   */
  const addChild = useCallback(async () => {
    if (!family) {
      throw new Error('No family loaded');
    }

    try {
      const result = await api.addChild(family.id);
      const newChildId = result.child_id;

      // Refresh family data to get updated children list
      await fetchFamily();

      // Switch to the new child
      setActiveChildId(newChildId);
      localStorage.setItem(ACTIVE_CHILD_KEY, newChildId);

      return newChildId;
    } catch (err) {
      console.error('Failed to add child:', err);
      throw err;
    }
  }, [family, fetchFamily]);

  /**
   * Switch to a different child.
   */
  const switchChild = useCallback((childId) => {
    const childExists = childrenList.some(c => c.id === childId);
    if (!childExists) {
      console.error('Child not found:', childId);
      return;
    }

    setActiveChildId(childId);
    localStorage.setItem(ACTIVE_CHILD_KEY, childId);
  }, [childrenList]);

  /**
   * Get the active child object.
   */
  const activeChild = childrenList.find(c => c.id === activeChildId) || null;

  /**
   * Check if user has multiple children.
   */
  const hasMultipleChildren = childrenList.length > 1;

  // Fetch family on mount
  useEffect(() => {
    fetchFamily();
  }, [fetchFamily]);

  const value = {
    // Data
    family,
    children: childrenList,
    activeChildId,
    activeChild,

    // State
    isLoading,
    error,
    hasMultipleChildren,

    // Actions
    addChild,
    switchChild,
    refreshFamily: fetchFamily,
  };

  return (
    <FamilyContext.Provider value={value}>
      {children}
    </FamilyContext.Provider>
  );
}

/**
 * Hook to access family context.
 */
export function useFamily() {
  const context = useContext(FamilyContext);
  if (!context) {
    throw new Error('useFamily must be used within a FamilyProvider');
  }
  return context;
}
