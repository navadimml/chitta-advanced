import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, act } from '@testing-library/react';
import { AuthProvider, useAuth } from './AuthContext';
import { api } from '../api/client';

// Mock the API client
vi.mock('../api/client', () => ({
  api: {
    setAccessToken: vi.fn(),
    login: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(),
    refreshToken: vi.fn(),
    getMe: vi.fn(),
  }
}));

// Test component that uses useAuth
function TestComponent({ onAuth }) {
  const auth = useAuth();
  if (onAuth) onAuth(auth);
  return (
    <div>
      <span data-testid="loading">{auth.isLoading.toString()}</span>
      <span data-testid="authenticated">{auth.isAuthenticated.toString()}</span>
      <span data-testid="user">{auth.user?.email || 'none'}</span>
    </div>
  );
}

describe('AuthContext', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  describe('Initial state', () => {
    it('should not be authenticated when no refresh token exists', async () => {
      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('loading').textContent).toBe('false');
      });

      expect(screen.getByTestId('authenticated').textContent).toBe('false');
      expect(screen.getByTestId('user').textContent).toBe('none');
    });
  });

  describe('Session restoration', () => {
    it('should restore session from refresh token', async () => {
      localStorage.setItem('chitta_refresh_token', 'stored_refresh_token');

      api.refreshToken.mockResolvedValue({
        access_token: 'new_access_token',
        refresh_token: 'new_refresh_token'
      });

      api.getMe.mockResolvedValue({
        id: 'user_123',
        email: 'test@example.com',
        display_name: 'Test User'
      });

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('loading').textContent).toBe('false');
      });

      expect(screen.getByTestId('authenticated').textContent).toBe('true');
      expect(screen.getByTestId('user').textContent).toBe('test@example.com');
      expect(api.setAccessToken).toHaveBeenCalledWith('new_access_token');
    });

    it('should clear auth when session restoration fails', async () => {
      localStorage.setItem('chitta_refresh_token', 'invalid_token');

      api.refreshToken.mockRejectedValue(new Error('Token expired'));

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('loading').textContent).toBe('false');
      });

      expect(screen.getByTestId('authenticated').textContent).toBe('false');
      expect(localStorage.getItem('chitta_refresh_token')).toBeNull();
    });
  });

  describe('Login', () => {
    it('should login successfully', async () => {
      api.login.mockResolvedValue({
        access_token: 'access_123',
        refresh_token: 'refresh_123',
        user: { id: 'user_123', email: 'test@example.com' }
      });

      let authContext;
      render(
        <AuthProvider>
          <TestComponent onAuth={(auth) => { authContext = auth; }} />
        </AuthProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('loading').textContent).toBe('false');
      });

      await act(async () => {
        await authContext.login('test@example.com', 'password123');
      });

      expect(screen.getByTestId('authenticated').textContent).toBe('true');
      expect(screen.getByTestId('user').textContent).toBe('test@example.com');
      expect(api.setAccessToken).toHaveBeenCalledWith('access_123');
      expect(localStorage.getItem('chitta_refresh_token')).toBe('refresh_123');
    });

    it('should propagate login errors', async () => {
      api.login.mockRejectedValue(new Error('Invalid credentials'));

      let authContext;
      render(
        <AuthProvider>
          <TestComponent onAuth={(auth) => { authContext = auth; }} />
        </AuthProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('loading').textContent).toBe('false');
      });

      await expect(authContext.login('test@example.com', 'wrong'))
        .rejects.toThrow('Invalid credentials');

      expect(screen.getByTestId('authenticated').textContent).toBe('false');
    });
  });

  describe('Register', () => {
    it('should register successfully and return success', async () => {
      api.register.mockResolvedValue({
        id: 'user_123',
        email: 'new@example.com',
        display_name: 'New User'
      });

      let authContext;
      render(
        <AuthProvider>
          <TestComponent onAuth={(auth) => { authContext = auth; }} />
        </AuthProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('loading').textContent).toBe('false');
      });

      let result;
      await act(async () => {
        result = await authContext.register('new@example.com', 'password123', 'New User');
      });

      // Register returns success but doesn't auto-login
      expect(result).toEqual({ success: true });
      expect(screen.getByTestId('authenticated').textContent).toBe('false');
      expect(api.register).toHaveBeenCalledWith('new@example.com', 'password123', 'New User');
    });
  });

  describe('Logout', () => {
    it('should logout and clear auth state', async () => {
      // Setup: logged in state
      localStorage.setItem('chitta_refresh_token', 'refresh_token');

      api.refreshToken.mockResolvedValue({
        access_token: 'access_token',
      });

      api.getMe.mockResolvedValue({
        id: 'user_123',
        email: 'test@example.com'
      });

      api.logout.mockResolvedValue({});

      let authContext;
      render(
        <AuthProvider>
          <TestComponent onAuth={(auth) => { authContext = auth; }} />
        </AuthProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('authenticated').textContent).toBe('true');
      });

      await act(async () => {
        await authContext.logout();
      });

      expect(screen.getByTestId('authenticated').textContent).toBe('false');
      expect(screen.getByTestId('user').textContent).toBe('none');
      expect(api.setAccessToken).toHaveBeenLastCalledWith(null);
      expect(localStorage.getItem('chitta_refresh_token')).toBeNull();
    });
  });

  describe('useAuth hook', () => {
    it('should throw error when used outside provider', () => {
      // Suppress console.error for this test
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      expect(() => {
        render(<TestComponent />);
      }).toThrow('useAuth must be used within an AuthProvider');

      consoleSpy.mockRestore();
    });
  });
});
