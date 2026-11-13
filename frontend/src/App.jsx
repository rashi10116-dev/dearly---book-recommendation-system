import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import LandingHero from './views/LandingHero';
import RecommendationDashboard from './views/RecommendationDashboard';
import CatalogueView from './views/CatalogueView';
import MyReadingView from './views/MyReadingView';
import AuthModal from './components/AuthModal';
import OnboardingModal from './components/OnboardingModal';
import BookDetailModal from './components/BookDetailModal';
import DatasetManagerModal from './components/DatasetManagerModal';
import { api, getAuthToken, setAuthToken } from './api/client';
import { BookOpen, Sparkles, Heart } from 'lucide-react';

export default function App() {
  const [currentUser, setCurrentUser] = useState(null);
  const [activeTab, setActiveTab] = useState('landing'); // 'landing', 'dashboard', 'catalogue', 'reading'
  const [loadingInitial, setLoadingInitial] = useState(true);

  // Modal controls
  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [authModalMode, setAuthModalMode] = useState('login');
  const [onboardingModalOpen, setOnboardingModalOpen] = useState(false);
  const [preferences, setPreferences] = useState(null);
  const [datasetModalOpen, setDatasetModalOpen] = useState(false);
  const [selectedBookId, setSelectedBookId] = useState(null);

  // Check user session on startup
  useEffect(() => {
    checkCurrentUser();
  }, []);

  const checkCurrentUser = async () => {
    const token = getAuthToken();
    if (!token) {
      setLoadingInitial(false);
      return;
    }
    try {
      const user = await api.auth.getMe();
      setCurrentUser(user);
      setActiveTab('dashboard');
      // Load user preferences
      try {
        const prefs = await api.preferences.get();
        setPreferences(prefs);
      } catch {
        // No preferences yet, open onboarding
        setOnboardingModalOpen(true);
      }
    } catch {
      setAuthToken(null);
      setCurrentUser(null);
      setActiveTab('landing');
    } finally {
      setLoadingInitial(false);
    }
  };

  const handleOpenAuth = (mode = 'login') => {
    setAuthModalMode(mode);
    setAuthModalOpen(true);
  };

  const handleAuthSuccess = async (user, shouldOnboard = false) => {
    setCurrentUser(user);
    if (shouldOnboard) {
      setOnboardingModalOpen(true);
      setActiveTab('dashboard');
    } else {
      setActiveTab('dashboard');
      try {
        const prefs = await api.preferences.get();
        setPreferences(prefs);
      } catch {
        setOnboardingModalOpen(true);
      }
    }
  };

  const handleLogout = () => {
    api.auth.logout();
    setCurrentUser(null);
    setPreferences(null);
    setActiveTab('landing');
  };

  const handleOnboardingComplete = (savedPrefs) => {
    setPreferences(savedPrefs);
    if (currentUser) {
      setCurrentUser({
        ...currentUser,
        has_preferences: true,
        display_name: savedPrefs.display_name,
      });
    }
    setActiveTab('dashboard');
  };

  const handleDemoLogin = async () => {
    try {
      const data = await api.auth.login('AriaBookworm', 'Passphrase123!');
      setAuthToken(data.access_token);
      await checkCurrentUser();
    } catch {
      handleOpenAuth('register');
    }
  };

  if (loadingInitial) {
    return (
      <div className="min-h-screen bg-[#FAF7F2] flex items-center justify-center">
        <div className="text-center space-y-3">
          <div className="w-12 h-12 rounded-2xl bg-[#571B37] text-white flex items-center justify-center mx-auto shadow-md animate-pulse">
            <BookOpen className="w-6 h-6 text-[#E09E4B]" />
          </div>
          <p className="font-editorial text-xl font-bold text-[#2A0F1D]">DEARLY</p>
          <p className="text-xs text-[#7A6E65]">Preparing your discovery mixes...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col bg-[#FAF7F2] text-[#2C2523]">
      
      {/* Top Navbar */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        currentUser={currentUser}
        onOpenAuth={handleOpenAuth}
        onOpenOnboarding={() => setOnboardingModalOpen(true)}
        onOpenPreferences={() => setOnboardingModalOpen(true)}
        onOpenDataset={() => setDatasetModalOpen(true)}
        onLogout={handleLogout}
      />

      {/* Main View Router */}
      <main className="flex-1">
        {activeTab === 'landing' && (
          <LandingHero
            onGetStarted={() => handleOpenAuth('register')}
            onExploreCatalogue={() => setActiveTab('catalogue')}
            onDemoLogin={handleDemoLogin}
          />
        )}

        {activeTab === 'dashboard' && (
          <RecommendationDashboard
            currentUser={currentUser}
            onSelectBook={(id) => setSelectedBookId(id)}
            onOpenPreferences={() => setOnboardingModalOpen(true)}
            onShelfChange={() => {}}
          />
        )}

        {activeTab === 'catalogue' && (
          <CatalogueView
            currentUser={currentUser}
            onSelectBook={(id) => setSelectedBookId(id)}
            onShelfChange={() => {}}
          />
        )}

        {activeTab === 'reading' && (
          <MyReadingView
            onSelectBook={(id) => setSelectedBookId(id)}
            onShelfChange={() => {}}
          />
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-[#EAE3D9] bg-white py-12 mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-xl bg-[#571B37] text-white flex items-center justify-center shadow-xs">
              <BookOpen className="w-4 h-4 text-[#E09E4B]" />
            </div>
            <div>
              <span className="font-editorial text-lg font-bold text-[#2A0F1D]">DEARLY</span>
              <p className="text-xs text-[#7A6E65]">Don't just find a book. Find your next favorite.</p>
            </div>
          </div>

          <div className="flex items-center gap-6 text-xs text-[#695D56] font-medium">
            <button onClick={() => setActiveTab('catalogue')} className="hover:text-[#571B37]">
              Browse Catalogue
            </button>
            <button onClick={() => setDatasetModalOpen(true)} className="hover:text-[#571B37]">
              Dataset & ML Re-indexing
            </button>
            {currentUser && (
              <button onClick={() => setOnboardingModalOpen(true)} className="hover:text-[#571B37]">
                Taste Profile
              </button>
            )}
          </div>

          <p className="text-xs text-[#A89C94] text-center md:text-right">
            © 2026 DEARLY Platform • Built with FastAPI, React & Scikit-Learn
          </p>
        </div>
      </footer>

      {/* Global Modals */}
      <AuthModal
        isOpen={authModalOpen}
        onClose={() => setAuthModalOpen(false)}
        initialMode={authModalMode}
        onAuthSuccess={handleAuthSuccess}
      />

      <OnboardingModal
        isOpen={onboardingModalOpen}
        onClose={() => setOnboardingModalOpen(false)}
        onComplete={handleOnboardingComplete}
        initialPreferences={preferences}
      />

      <BookDetailModal
        bookId={selectedBookId}
        isOpen={selectedBookId !== null}
        onClose={() => setSelectedBookId(null)}
        currentUser={currentUser}
        onShelfChange={() => {}}
        onSelectBook={(id) => setSelectedBookId(id)}
      />

      <DatasetManagerModal
        isOpen={datasetModalOpen}
        onClose={() => setDatasetModalOpen(false)}
        onDatasetUpdated={() => {}}
      />

    </div>
  );
}
