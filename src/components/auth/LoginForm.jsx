/**
 * Login Form Component
 * Hebrew-first login form with email/password fields.
 */

import { useState } from 'react';

export default function LoginForm({ onSubmit, onSwitchToRegister, isLoading }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!email || !password) {
      setError('נא למלא את כל השדות');
      return;
    }

    try {
      await onSubmit(email, password);
    } catch (err) {
      setError(err.message || 'שגיאה בהתחברות');
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4" dir="rtl">
      <div>
        <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
          אימייל
        </label>
        <input
          id="email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:border-blue-400
                     focus:ring-2 focus:ring-blue-100 outline-none transition-all"
          placeholder="your@email.com"
          disabled={isLoading}
          autoComplete="email"
        />
      </div>

      <div>
        <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
          סיסמה
        </label>
        <input
          id="password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:border-blue-400
                     focus:ring-2 focus:ring-blue-100 outline-none transition-all"
          placeholder="הסיסמה שלך"
          disabled={isLoading}
          autoComplete="current-password"
        />
      </div>

      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-xl text-red-600 text-sm">
          {error}
        </div>
      )}

      <button
        type="submit"
        disabled={isLoading}
        className="w-full py-3 px-4 bg-gradient-to-r from-blue-500 to-purple-500 text-white
                   font-medium rounded-xl hover:from-blue-600 hover:to-purple-600
                   focus:ring-2 focus:ring-blue-300 transition-all disabled:opacity-50
                   disabled:cursor-not-allowed"
      >
        {isLoading ? 'מתחבר...' : 'התחברות'}
      </button>

      <div className="text-center text-sm text-gray-600 pt-2">
        אין לך חשבון?{' '}
        <button
          type="button"
          onClick={onSwitchToRegister}
          className="text-blue-600 hover:text-blue-700 font-medium"
          disabled={isLoading}
        >
          הרשמה
        </button>
      </div>
    </form>
  );
}
