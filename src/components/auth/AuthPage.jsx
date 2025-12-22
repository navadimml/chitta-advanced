/**
 * Auth Page Component
 * Container that switches between login and register forms.
 * Features Chitta branding with gradient background.
 */

import { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import LoginForm from './LoginForm';
import RegisterForm from './RegisterForm';

export default function AuthPage() {
  const [mode, setMode] = useState('login'); // 'login' or 'register'
  const [isLoading, setIsLoading] = useState(false);
  const { login, register } = useAuth();

  const handleLogin = async (email, password) => {
    setIsLoading(true);
    try {
      await login(email, password);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRegister = async (email, password, displayName, parentType) => {
    setIsLoading(true);
    try {
      await register(email, password, displayName, parentType);
      // Registration successful - switch to login mode
      setMode('login');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo and Branding */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-20 h-20 bg-white rounded-2xl shadow-lg mb-4">
            <span className="text-4xl">
              <svg viewBox="0 0 100 100" className="w-12 h-12">
                <defs>
                  <linearGradient id="logoGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor="#3B82F6" />
                    <stop offset="100%" stopColor="#8B5CF6" />
                  </linearGradient>
                </defs>
                <circle cx="50" cy="50" r="45" fill="url(#logoGradient)" />
                <text x="50" y="62" textAnchor="middle" fill="white" fontSize="36" fontFamily="sans-serif">C</text>
              </svg>
            </span>
          </div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            Chitta
          </h1>
          <p className="text-gray-600 mt-2" dir="rtl">
            מלווה אותך בהתפתחות הילד
          </p>
        </div>

        {/* Form Card */}
        <div className="bg-white rounded-2xl shadow-xl p-6 animate-slideUp">
          <h2 className="text-xl font-semibold text-gray-800 text-center mb-6" dir="rtl">
            {mode === 'login' ? 'התחברות' : 'הרשמה'}
          </h2>

          {mode === 'login' ? (
            <LoginForm
              onSubmit={handleLogin}
              onSwitchToRegister={() => setMode('register')}
              isLoading={isLoading}
            />
          ) : (
            <RegisterForm
              onSubmit={handleRegister}
              onSwitchToLogin={() => setMode('login')}
              isLoading={isLoading}
            />
          )}
        </div>

        {/* Footer */}
        <p className="text-center text-gray-500 text-sm mt-6">
          Chitta &copy; 2025
        </p>
      </div>
    </div>
  );
}
