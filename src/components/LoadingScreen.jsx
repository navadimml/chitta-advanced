/**
 * Loading Screen Component
 * Shown during initial auth check.
 * Features Chitta logo with pulse animation.
 */

export default function LoadingScreen() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50 flex items-center justify-center">
      <div className="text-center">
        {/* Animated Logo */}
        <div className="inline-flex items-center justify-center w-24 h-24 bg-white rounded-2xl shadow-lg mb-4 animate-pulse">
          <svg viewBox="0 0 100 100" className="w-14 h-14">
            <defs>
              <linearGradient id="loadingGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#3B82F6" />
                <stop offset="100%" stopColor="#8B5CF6" />
              </linearGradient>
            </defs>
            <circle cx="50" cy="50" r="45" fill="url(#loadingGradient)" />
            <text x="50" y="62" textAnchor="middle" fill="white" fontSize="36" fontFamily="sans-serif">C</text>
          </svg>
        </div>

        {/* Brand Name */}
        <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
          Chitta
        </h1>

        {/* Loading indicator */}
        <div className="mt-4 flex justify-center gap-1">
          <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
          <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
          <div className="w-2 h-2 bg-pink-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
        </div>
      </div>
    </div>
  );
}
