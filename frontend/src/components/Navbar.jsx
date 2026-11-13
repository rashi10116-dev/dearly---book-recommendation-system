import React from 'react';
import { BookOpen, Sparkles, Compass, BookmarkCheck, Database, User, LogOut, Sliders } from 'lucide-react';

export default function Navbar({
  activeTab,
  setActiveTab,
  currentUser,
  onOpenAuth,
  onOpenOnboarding,
  onOpenPreferences,
  onOpenDataset,
  onLogout,
}) {
  return (
    <header className="sticky top-0 z-40 bg-[#FAF7F2]/90 backdrop-blur-md border-b border-[#EAE3D9] transition-all">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-20">
          
          {/* Logo & Tagline */}
          <div 
            onClick={() => setActiveTab(currentUser ? 'dashboard' : 'landing')}
            className="flex items-center gap-3 cursor-pointer group"
          >
            <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-[#3D1426] to-[#571B37] text-white flex items-center justify-center shadow-md shadow-[#3D1426]/15 group-hover:scale-105 transition-transform">
              <BookOpen className="w-6 h-6 text-[#E09E4B]" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-editorial text-2xl font-bold tracking-tight text-[#2A0F1D]">DEARLY</span>
                <span className="text-[10px] uppercase tracking-widest font-semibold px-2 py-0.5 rounded-full bg-[#EAE3D9] text-[#571B37]">Beta</span>
              </div>
              <p className="text-xs text-[#7A6E65] italic hidden sm:block">Don't just find a book. Find your next favorite.</p>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="hidden md:flex items-center gap-1 bg-[#F0EBE1] p-1.5 rounded-2xl border border-[#EAE3D9]">
            {currentUser && (
              <button
                onClick={() => setActiveTab('dashboard')}
                className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all ${
                  activeTab === 'dashboard'
                    ? 'bg-white text-[#3D1426] shadow-sm font-semibold'
                    : 'text-[#695D56] hover:text-[#2A0F1D] hover:bg-white/50'
                }`}
              >
                <Sparkles className="w-4 h-4 text-[#C48332]" />
                Taste Mixes
              </button>
            )}

            <button
              onClick={() => setActiveTab('catalogue')}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all ${
                activeTab === 'catalogue'
                  ? 'bg-white text-[#3D1426] shadow-sm font-semibold'
                  : 'text-[#695D56] hover:text-[#2A0F1D] hover:bg-white/50'
              }`}
            >
              <Compass className="w-4 h-4 text-[#571B37]" />
              Catalogue
            </button>

            {currentUser && (
              <button
                onClick={() => setActiveTab('reading')}
                className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all ${
                  activeTab === 'reading'
                    ? 'bg-white text-[#3D1426] shadow-sm font-semibold'
                    : 'text-[#695D56] hover:text-[#2A0F1D] hover:bg-white/50'
                }`}
              >
                <BookmarkCheck className="w-4 h-4 text-[#1C3829]" />
                My Reading
              </button>
            )}

            <button
              onClick={onOpenDataset}
              className="flex items-center gap-2 px-3 py-2 rounded-xl text-sm font-medium text-[#695D56] hover:text-[#2A0F1D] hover:bg-white/50 transition-all"
              title="Dataset & ML Setup"
            >
              <Database className="w-4 h-4 text-[#7A6E65]" />
              <span className="hidden lg:inline">Dataset & ML</span>
            </button>
          </nav>

          {/* User Profile / Auth Actions */}
          <div className="flex items-center gap-3">
            {currentUser ? (
              <div className="flex items-center gap-2">
                <button
                  onClick={onOpenPreferences}
                  className="hidden sm:flex items-center gap-2 px-3 py-2 rounded-xl border border-[#EAE3D9] bg-white text-xs font-medium text-[#571B37] hover:bg-[#F5EFEB] transition-colors"
                  title="Edit Taste Preferences"
                >
                  <Sliders className="w-3.5 h-3.5 text-[#C48332]" />
                  Taste Profile
                </button>

                <div className="flex items-center gap-2 pl-2">
                  <div className="w-9 h-9 rounded-full bg-[#571B37] text-white flex items-center justify-center font-bold text-xs uppercase shadow-sm">
                    {currentUser.display_name ? currentUser.display_name[0] : currentUser.username[0]}
                  </div>
                  <div className="hidden sm:block text-left text-xs">
                    <p className="font-semibold text-[#2A0F1D] leading-tight">{currentUser.display_name || currentUser.username}</p>
                    <p className="text-[10px] text-[#7A6E65]">Reader</p>
                  </div>
                </div>

                <button
                  onClick={onLogout}
                  className="p-2 rounded-xl text-[#7A6E65] hover:text-[#9B2C2C] hover:bg-[#F5EFEB] transition-colors"
                  title="Sign out"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <button
                  onClick={() => onOpenAuth('login')}
                  className="px-4 py-2 text-sm font-medium text-[#571B37] hover:text-[#2A0F1D] transition-colors"
                >
                  Sign In
                </button>
                <button
                  onClick={() => onOpenAuth('register')}
                  className="px-5 py-2 rounded-xl bg-[#571B37] hover:bg-[#3D1426] text-white text-sm font-medium shadow-sm transition-all hover:scale-102"
                >
                  Get Started
                </button>
              </div>
            )}
          </div>

        </div>
      </div>
    </header>
  );
}
