/**
 * Register Form Component
 * Hebrew-first registration form with validation.
 */

import { useState } from 'react';

export default function RegisterForm({ onSubmit, onSwitchToLogin, isLoading }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!email || !password || !confirmPassword || !displayName) {
      setError('נא למלא את כל השדות');
      return;
    }

    if (password.length < 8) {
      setError('הסיסמה חייבת להכיל לפחות 8 תווים');
      return;
    }

    if (password !== confirmPassword) {
      setError('הסיסמאות אינן תואמות');
      return;
    }

    try {
      await onSubmit(email, password, displayName);
    } catch (err) {
      setError(err.message || 'שגיאה בהרשמה');
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4" dir="rtl">
      <div>
        <label htmlFor="displayName" className="block text-sm font-medium text-gray-700 mb-1">
          שם
        </label>
        <input
          id="displayName"
          type="text"
          value={displayName}
          onChange={(e) => setDisplayName(e.target.value)}
          className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:border-blue-400
                     focus:ring-2 focus:ring-blue-100 outline-none transition-all"
          placeholder="השם שלך"
          disabled={isLoading}
          autoComplete="name"
        />
      </div>

      <div>
        <label htmlFor="registerEmail" className="block text-sm font-medium text-gray-700 mb-1">
          אימייל
        </label>
        <input
          id="registerEmail"
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
        <label htmlFor="registerPassword" className="block text-sm font-medium text-gray-700 mb-1">
          סיסמה
        </label>
        <input
          id="registerPassword"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:border-blue-400
                     focus:ring-2 focus:ring-blue-100 outline-none transition-all"
          placeholder="לפחות 8 תווים"
          disabled={isLoading}
          autoComplete="new-password"
        />
      </div>

      <div>
        <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700 mb-1">
          אימות סיסמה
        </label>
        <input
          id="confirmPassword"
          type="password"
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
          className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:border-blue-400
                     focus:ring-2 focus:ring-blue-100 outline-none transition-all"
          placeholder="הקלד שוב את הסיסמה"
          disabled={isLoading}
          autoComplete="new-password"
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
        {isLoading ? 'נרשם...' : 'הרשמה'}
      </button>

      <div className="text-center text-sm text-gray-600 pt-2">
        יש לך כבר חשבון?{' '}
        <button
          type="button"
          onClick={onSwitchToLogin}
          className="text-blue-600 hover:text-blue-700 font-medium"
          disabled={isLoading}
        >
          התחברות
        </button>
      </div>
    </form>
  );
}
