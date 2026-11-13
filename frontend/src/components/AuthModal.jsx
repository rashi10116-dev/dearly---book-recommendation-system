import React, { useState } from 'react';
import { X, BookOpen, KeyRound, Mail, User, Sparkles, AlertCircle } from 'lucide-react';
import { api, setAuthToken } from '../api/client';

export default function AuthModal({ isOpen, onClose, initialMode = 'login', onAuthSuccess }) {
  const [mode, setMode] = useState(initialMode); // 'login' or 'register'
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      if (mode === 'register') {
        if (!email || !username || !password) {
          throw new Error('Please fill in all fields.');
        }
        const data = await api.auth.register(email, username, password);
        setAuthToken(data.access_token);
        onAuthSuccess(data.user, true); // true = newly registered, prompt onboarding!
      } else {
        if (!username || !password) {
          throw new Error('Please enter your username/email and password.');
        }
        const data = await api.auth.login(username, password);
        setAuthToken(data.access_token);
        onAuthSuccess(data.user, !data.user.has_preferences);
      }
      onClose();
    } catch (err) {
      setError(err.message || 'Authentication failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  const fillDemoAccount = async () => {
    setError('');
    setUsername('AriaBookworm');
    setPassword('Passphrase123!');
    setMode('login');
    setLoading(true);
    try {
      const data = await api.auth.login('AriaBookworm', 'Passphrase123!');
      setAuthToken(data.access_token);
      onAuthSuccess(data.user, false);
      onClose();
    } catch {
      // If demo user does not exist yet, auto register demo user
      try {
        const regData = await api.auth.register('testreader@example.com', 'AriaBookworm', 'Passphrase123!');
        setAuthToken(regData.access_token);
        onAuthSuccess(regData.user, true);
        onClose();
      } catch (regErr) {
        setError(regErr.message || 'Demo login failed.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-[#2A0F1D]/50 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-[#FCFAF6] border border-[#EAE3D9] rounded-3xl max-w-md w-full shadow-2xl overflow-hidden relative">
        
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-5 right-5 p-2 rounded-full text-[#7A6E65] hover:text-[#2A0F1D] hover:bg-[#EAE3D9]/60 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Header */}
        <div className="p-8 pb-4 text-center">
          <div className="w-12 h-12 mx-auto rounded-2xl bg-gradient-to-br from-[#3D1426] to-[#571B37] text-white flex items-center justify-center shadow-md mb-4">
            <BookOpen className="w-6 h-6 text-[#E09E4B]" />
          </div>
          <h2 className="font-editorial text-2xl font-bold text-[#2A0F1D]">
            {mode === 'register' ? 'Join DEARLY' : 'Welcome Back'}
          </h2>
          <p className="text-xs text-[#7A6E65] mt-1">
            {mode === 'register'
              ? 'Begin your personalized reading journey.'
              : 'Sign in to access your curated taste mixes.'}
          </p>

          {/* Mode Switcher Tabs */}
          <div className="flex bg-[#EAE3D9]/60 p-1 rounded-xl mt-6 border border-[#EAE3D9]">
            <button
              type="button"
              onClick={() => { setMode('login'); setError(''); }}
              className={`flex-1 py-1.5 text-xs font-semibold rounded-lg transition-all ${
                mode === 'login' ? 'bg-white text-[#3D1426] shadow-xs' : 'text-[#7A6E65] hover:text-[#2A0F1D]'
              }`}
            >
              Sign In
            </button>
            <button
              type="button"
              onClick={() => { setMode('register'); setError(''); }}
              className={`flex-1 py-1.5 text-xs font-semibold rounded-lg transition-all ${
                mode === 'register' ? 'bg-white text-[#3D1426] shadow-xs' : 'text-[#7A6E65] hover:text-[#2A0F1D]'
              }`}
            >
              Create Account
            </button>
          </div>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="mx-8 p-3 rounded-xl bg-[#FDF2F2] border border-[#F8B4B4] text-[#9B2C2C] text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-8 pt-4 space-y-4">
          {mode === 'register' && (
            <div>
              <label className="block text-xs font-semibold text-[#571B37] mb-1.5">Email Address</label>
              <div className="relative">
                <Mail className="w-4 h-4 text-[#A89C94] absolute left-3.5 top-3" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="reader@domain.com"
                  className="w-full pl-10 pr-4 py-2.5 bg-white border border-[#EAE3D9] rounded-xl text-sm text-[#2A0F1D] focus:outline-none focus:ring-2 focus:ring-[#571B37]/20 focus:border-[#571B37]"
                  required
                />
              </div>
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold text-[#571B37] mb-1.5">
              {mode === 'register' ? 'Choose Username' : 'Username or Email'}
            </label>
            <div className="relative">
              <User className="w-4 h-4 text-[#A89C94] absolute left-3.5 top-3" />
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder={mode === 'register' ? 'e.g. LiteraryVoyager' : 'Enter username or email'}
                className="w-full pl-10 pr-4 py-2.5 bg-white border border-[#EAE3D9] rounded-xl text-sm text-[#2A0F1D] focus:outline-none focus:ring-2 focus:ring-[#571B37]/20 focus:border-[#571B37]"
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-[#571B37] mb-1.5">Password</label>
            <div className="relative">
              <KeyRound className="w-4 h-4 text-[#A89C94] absolute left-3.5 top-3" />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full pl-10 pr-4 py-2.5 bg-white border border-[#EAE3D9] rounded-xl text-sm text-[#2A0F1D] focus:outline-none focus:ring-2 focus:ring-[#571B37]/20 focus:border-[#571B37]"
                required
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 px-4 rounded-xl bg-[#571B37] hover:bg-[#3D1426] text-white font-semibold text-sm shadow-md transition-all disabled:opacity-50 cursor-pointer"
          >
            {loading ? 'Please wait...' : mode === 'register' ? 'Create Account & Personalize' : 'Sign In'}
          </button>

          {/* 1-Click Demo Account Quick Action */}
          <div className="pt-2 text-center border-t border-[#EAE3D9]/60">
            <button
              type="button"
              onClick={fillDemoAccount}
              disabled={loading}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-[#E09E4B]/15 hover:bg-[#E09E4B]/25 text-[#925514] text-xs font-semibold transition-colors cursor-pointer"
            >
              <Sparkles className="w-3.5 h-3.5 text-[#C48332]" />
              Quick 1-Click Demo Reviewer Account
            </button>
          </div>
        </form>

      </div>
    </div>
  );
}
