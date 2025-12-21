/**
 * Auth Context
 * Central authentication state manager for Chitta.
 *
 * Token Strategy:
 * - Access token: Memory (React state) - cleared on tab close
 * - Refresh token: localStorage - persists across sessions
 * - Auto-refresh: Refreshes token ~5 min before expiry (25 min mark)
 */

import { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';
import { api } from '../api/client';

const AuthContext = createContext(null);

// Constants
const REFRESH_TOKEN_KEY = 'chitta_refresh_token';
const TOKEN_REFRESH_INTERVAL = 25 * 60 * 1000; // 25 minutes (tokens expire at 30)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [accessToken, setAccessToken] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const refreshTimerRef = useRef(null);

  /**
   * Clear all auth state
   */
  const clearAuth = useCallback(() => {
    setUser(null);
    setAccessToken(null);
    api.setAccessToken(null);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
    if (refreshTimerRef.current) {
      clearTimeout(refreshTimerRef.current);
      refreshTimerRef.current = null;
    }
  }, []);

  /**
   * Schedule token refresh
   */
  const scheduleTokenRefresh = useCallback(() => {
    // Clear any existing timer
    if (refreshTimerRef.current) {
      clearTimeout(refreshTimerRef.current);
    }

    // Schedule refresh 5 minutes before expiry
    refreshTimerRef.current = setTimeout(async () => {
      const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY);
      if (!refreshToken) {
        clearAuth();
        return;
      }

      try {
        const result = await api.refreshToken(refreshToken);
        setAccessToken(result.access_token);
        api.setAccessToken(result.access_token);

        // If we got a new refresh token, save it
        if (result.refresh_token) {
          localStorage.setItem(REFRESH_TOKEN_KEY, result.refresh_token);
        }

        // Schedule next refresh
        scheduleTokenRefresh();
      } catch (error) {
        console.error('Token refresh failed:', error);
        clearAuth();
      }
    }, TOKEN_REFRESH_INTERVAL);
  }, [clearAuth]);

  /**
   * Set tokens and schedule refresh
   */
  const setTokens = useCallback((newAccessToken, refreshToken) => {
    setAccessToken(newAccessToken);
    api.setAccessToken(newAccessToken);

    if (refreshToken) {
      localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
    }

    scheduleTokenRefresh();
  }, [scheduleTokenRefresh]);

  /**
   * Login with email and password
   */
  const login = useCallback(async (email, password) => {
    const result = await api.login(email, password);

    setUser(result.user);
    setTokens(result.access_token, result.refresh_token);

    return result.user;
  }, [setTokens]);

  /**
   * Register a new user
   */
  const register = useCallback(async (email, password, displayName) => {
    const result = await api.register(email, password, displayName);

    // Auto-login after registration if tokens are returned
    if (result.access_token) {
      setUser(result.user);
      setTokens(result.access_token, result.refresh_token);
      return result.user;
    }

    // If no auto-login, just return the user
    return result;
  }, [setTokens]);

  /**
   * Logout current user
   */
  const logout = useCallback(async () => {
    const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY);

    // Try to revoke the refresh token on the server
    if (refreshToken) {
      try {
        await api.logout(refreshToken);
      } catch (error) {
        // Ignore errors - we're logging out anyway
        console.warn('Logout request failed:', error);
      }
    }

    clearAuth();
  }, [clearAuth]);

  /**
   * Check for existing session on mount
   */
  useEffect(() => {
    const initAuth = async () => {
      const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY);

      if (!refreshToken) {
        setIsLoading(false);
        return;
      }

      try {
        // Try to refresh the token
        const result = await api.refreshToken(refreshToken);
        setAccessToken(result.access_token);
        api.setAccessToken(result.access_token);

        if (result.refresh_token) {
          localStorage.setItem(REFRESH_TOKEN_KEY, result.refresh_token);
        }

        // Get user info
        const userInfo = await api.getMe();
        setUser(userInfo);

        // Schedule next refresh
        scheduleTokenRefresh();
      } catch (error) {
        console.error('Session restoration failed:', error);
        clearAuth();
      } finally {
        setIsLoading(false);
      }
    };

    initAuth();

    // Cleanup on unmount
    return () => {
      if (refreshTimerRef.current) {
        clearTimeout(refreshTimerRef.current);
      }
    };
  }, [clearAuth, scheduleTokenRefresh]);

  const value = {
    user,
    accessToken,
    isAuthenticated: !!user,
    isLoading,
    login,
    register,
    logout,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

/**
 * Hook to access auth context
 */
export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
