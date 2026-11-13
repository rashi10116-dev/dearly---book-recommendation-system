import React, { useState } from 'react';
import { Sparkles, Check, ChevronRight, ChevronLeft, Sliders, HeartHandshake, ShieldAlert, BookOpen, X, Plus } from 'lucide-react';
import { api } from '../api/client';

const GENRES = [
  'Fantasy', 'Dark Academia', 'Science Fiction', 'Mystery', 'Literary Fiction',
  'Romance', 'Historical Fiction', 'Magical Realism', 'Speculative Fiction', 'Horror', 'Contemporary'
];

const TROPES = [
  'Enemies to Lovers', 'Found Family', 'Secret Society', 'Heist Crew',
  'Unreliable Narrator', 'Slow Burn', 'Time Travel', 'Dual Timeline',
  'Morally Grey', 'Amateur Sleuths', 'Cozy Low-Stakes', 'Grumpy and Sunshine',
  'Parallel Universes', 'Magic Academy', 'Second Chances'
];

const THEMES = [
  'Obsession', 'Trauma and Resilience', 'Power of Stories', 'Colonialism and Resistance',
  'Grief and Memory', 'Friendship Beyond Romance', 'Artistic Ambition',
  'Scientific Curiosity', 'Aging Gracefully', 'Moral Courage', 'Self-Sacrifice'
];

const STYLES = ['Lyrical', 'Atmospheric', 'Fast-Paced', 'Witty', 'Philosophical', 'Gritty'];
const PACING = ['Fast', 'Moderate', 'Slow Burn'];
const TONES = ['Cozy', 'Bittersweet', 'Tense', 'Whimsical', 'Dark', 'Heartbreaking', 'Uplifting', 'Thought-Provoking'];
const LENGTHS = ['Short (<300 pages)', 'Medium (300-450 pages)', 'Long (450+ pages)', 'No preference'];
const DIFFICULTIES = ['Light & Breezy', 'Balanced', 'Challenging & Dense'];

const DISLIKED_OPTIONS = [
  'Love Triangles', 'Cliffhangers', 'Gore & Violence', 'Cynical Endings',
  'Miscommunication Trope', 'Insta-Love', 'Overly Slow Exposition'
];

export default function OnboardingModal({ isOpen, onClose, onComplete, initialPreferences = null }) {
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);

  // Form states
  const [displayName, setDisplayName] = useState(initialPreferences?.display_name || '');
  const [favoriteGenres, setFavoriteGenres] = useState(initialPreferences?.favorite_genres || ['Fantasy', 'Dark Academia', 'Mystery']);
  const [favoriteTropes, setFavoriteTropes] = useState(initialPreferences?.favorite_tropes || ['Found Family', 'Secret Society']);
  const [favoriteThemes, setFavoriteThemes] = useState(initialPreferences?.favorite_themes || ['Obsession', 'Trauma and Resilience']);
  const [preferredStyle, setPreferredStyle] = useState(initialPreferences?.preferred_writing_style || 'Lyrical');
  const [preferredPacing, setPreferredPacing] = useState(initialPreferences?.preferred_pacing || 'Moderate');
  const [preferredTone, setPreferredTone] = useState(initialPreferences?.preferred_emotional_tone || 'Bittersweet');
  const [preferredLength, setPreferredLength] = useState(initialPreferences?.preferred_book_length || 'Medium (300-450 pages)');
  const [favoriteAuthors, setFavoriteAuthors] = useState(
    initialPreferences?.favorite_authors?.join(', ') || 'Donna Tartt, Leigh Bardugo'
  );
  const [dislikedElements, setDislikedElements] = useState(initialPreferences?.disliked_elements || []);
  const [readingDifficulty, setReadingDifficulty] = useState(initialPreferences?.reading_difficulty || 'Balanced');

  if (!isOpen) return null;

  const toggleGenre = (g) => {
    if (favoriteGenres.includes(g)) {
      setFavoriteGenres(favoriteGenres.filter((item) => item !== g));
    } else {
      if (favoriteGenres.length >= 3) {
        // replace earliest
        setFavoriteGenres([...favoriteGenres.slice(1), g]);
      } else {
        setFavoriteGenres([...favoriteGenres, g]);
      }
    }
  };

  const toggleItem = (list, setList, item) => {
    if (list.includes(item)) {
      setList(list.filter((x) => x !== item));
    } else {
      setList([...list, item]);
    }
  };

  const handleSave = async () => {
    setLoading(true);
    try {
      const authorsList = favoriteAuthors
        .split(',')
        .map((a) => a.trim())
        .filter((a) => a.length > 0);

      const payload = {
        display_name: displayName.trim() || 'Reader',
        favorite_genres: favoriteGenres,
        favorite_tropes: favoriteTropes,
        favorite_themes: favoriteThemes,
        preferred_writing_style: preferredStyle,
        preferred_pacing: preferredPacing,
        preferred_emotional_tone: preferredTone,
        preferred_book_length: preferredLength,
        favorite_authors: authorsList,
        disliked_elements: dislikedElements,
        reading_difficulty: readingDifficulty,
      };

      const saved = await api.preferences.save(payload);
      // Automatically refit or trigger recommendations
      onComplete(saved);
      onClose();
    } catch (err) {
      alert(`Could not save preferences: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-[#2A0F1D]/60 backdrop-blur-md animate-in fade-in duration-200">
      <div className="bg-[#FAF7F2] border border-[#EAE3D9] rounded-3xl max-w-2xl w-full shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        
        {/* Header / Progress bar */}
        <div className="p-6 pb-4 border-b border-[#EAE3D9] bg-white">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="w-8 h-8 rounded-xl bg-[#571B37] text-white flex items-center justify-center text-xs font-bold">
                {step}/4
              </span>
              <div>
                <h2 className="font-editorial text-xl font-bold text-[#2A0F1D]">Personalize Your Reader Taste</h2>
                <p className="text-xs text-[#7A6E65]">Step {step} of 4: {
                  step === 1 ? 'Your Core Genres & Identity' :
                  step === 2 ? 'Story Tropes & Themes' :
                  step === 3 ? 'Writing Style & Atmosphere' :
                  'Guardrails & Favorite Authors'
                }</p>
              </div>
            </div>
            <div className="text-right">
              <span className="text-[11px] font-semibold text-[#C48332] uppercase tracking-wider">
                {Math.round((step / 4) * 100)}% Complete
              </span>
            </div>
          </div>

          <div className="w-full bg-[#EAE3D9] h-1.5 rounded-full mt-4 overflow-hidden">
            <div
              className="bg-gradient-to-r from-[#571B37] to-[#C48332] h-full transition-all duration-300"
              style={{ width: `${(step / 4) * 100}%` }}
            />
          </div>
        </div>

        {/* Modal Body */}
        <div className="p-8 overflow-y-auto flex-1 space-y-6">

          {/* STEP 1: Name & Top 3 Genres */}
          {step === 1 && (
            <div className="space-y-6">
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-[#571B37] mb-2">
                  What should we call you?
                </label>
                <input
                  type="text"
                  value={displayName}
                  onChange={(e) => setDisplayName(e.target.value)}
                  placeholder="e.g. Aria, Julian, The Literary Botanist"
                  className="w-full px-4 py-3 bg-white border border-[#EAE3D9] rounded-2xl text-sm font-medium text-[#2A0F1D] focus:ring-2 focus:ring-[#571B37]/20 focus:border-[#571B37] outline-none"
                />
              </div>

              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="block text-xs font-bold uppercase tracking-wider text-[#571B37]">
                    Select Your Top Three Favorite Genres
                  </label>
                  <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-[#EAE3D9] text-[#571B37]">
                    {favoriteGenres.length} / 3 selected
                  </span>
                </div>
                <p className="text-xs text-[#7A6E65] mb-3">
                  These anchor your primary <em>Your Taste</em> mixes on your dashboard.
                </p>

                <div className="flex flex-wrap gap-2">
                  {GENRES.map((g) => {
                    const isSelected = favoriteGenres.includes(g);
                    return (
                      <button
                        key={g}
                        type="button"
                        onClick={() => toggleGenre(g)}
                        className={`px-4 py-2.5 rounded-2xl text-xs font-semibold transition-all flex items-center gap-1.5 cursor-pointer ${
                          isSelected
                            ? 'bg-[#571B37] text-white shadow-sm ring-2 ring-[#571B37]/30 scale-102'
                            : 'bg-white border border-[#EAE3D9] text-[#5A4F48] hover:border-[#571B37] hover:text-[#2A0F1D]'
                        }`}
                      >
                        {isSelected && <Check className="w-3.5 h-3.5 text-[#E09E4B]" />}
                        {g}
                      </button>
                    );
                  })}
                </div>
              </div>
            </div>
          )}

          {/* STEP 2: Tropes & Themes */}
          {step === 2 && (
            <div className="space-y-6">
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-[#571B37] mb-2">
                  Favorite Story Tropes
                </label>
                <p className="text-xs text-[#7A6E65] mb-3">
                  The plot devices and narrative patterns you actively seek out.
                </p>
                <div className="flex flex-wrap gap-2">
                  {TROPES.map((t) => {
                    const isSelected = favoriteTropes.includes(t);
                    return (
                      <button
                        key={t}
                        type="button"
                        onClick={() => toggleItem(favoriteTropes, setFavoriteTropes, t)}
                        className={`px-3.5 py-2 rounded-xl text-xs font-medium transition-all flex items-center gap-1.5 cursor-pointer ${
                          isSelected
                            ? 'bg-[#2A533E] text-white shadow-sm'
                            : 'bg-white border border-[#EAE3D9] text-[#5A4F48] hover:bg-[#F5EFEB]'
                        }`}
                      >
                        {isSelected && <Check className="w-3 h-3 text-[#A3E635]" />}
                        {t}
                      </button>
                    );
                  })}
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-[#571B37] mb-2">
                  Resonant Themes
                </label>
                <p className="text-xs text-[#7A6E65] mb-3">
                  The deeper emotional or philosophical questions you care about.
                </p>
                <div className="flex flex-wrap gap-2">
                  {THEMES.map((th) => {
                    const isSelected = favoriteThemes.includes(th);
                    return (
                      <button
                        key={th}
                        type="button"
                        onClick={() => toggleItem(favoriteThemes, setFavoriteThemes, th)}
                        className={`px-3.5 py-2 rounded-xl text-xs font-medium transition-all flex items-center gap-1.5 cursor-pointer ${
                          isSelected
                            ? 'bg-[#C48332] text-white shadow-sm'
                            : 'bg-white border border-[#EAE3D9] text-[#5A4F48] hover:bg-[#F5EFEB]'
                        }`}
                      >
                        {isSelected && <Check className="w-3 h-3 text-white" />}
                        {th}
                      </button>
                    );
                  })}
                </div>
              </div>
            </div>
          )}

          {/* STEP 3: Style, Pacing, Tone, Length */}
          {step === 3 && (
            <div className="space-y-6">
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-[#571B37] mb-2">
                  Preferred Writing Style
                </label>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                  {STYLES.map((s) => (
                    <button
                      key={s}
                      type="button"
                      onClick={() => setPreferredStyle(s)}
                      className={`p-3 rounded-2xl text-xs font-semibold text-center transition-all cursor-pointer ${
                        preferredStyle === s
                          ? 'bg-[#571B37] text-white shadow-sm'
                          : 'bg-white border border-[#EAE3D9] text-[#5A4F48] hover:border-[#571B37]'
                      }`}
                    >
                      {s}
                    </button>
                  ))}
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-[#571B37] mb-2">
                    Preferred Pacing
                  </label>
                  <div className="space-y-1.5">
                    {PACING.map((p) => (
                      <button
                        key={p}
                        type="button"
                        onClick={() => setPreferredPacing(p)}
                        className={`w-full p-2.5 rounded-xl text-xs font-medium text-left px-3 transition-all cursor-pointer ${
                          preferredPacing === p
                            ? 'bg-[#571B37] text-white'
                            : 'bg-white border border-[#EAE3D9] text-[#5A4F48] hover:bg-[#F5EFEB]'
                        }`}
                      >
                        {p}
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-[#571B37] mb-2">
                    Emotional Tone
                  </label>
                  <select
                    value={preferredTone}
                    onChange={(e) => setPreferredTone(e.target.value)}
                    className="w-full px-3 py-2.5 bg-white border border-[#EAE3D9] rounded-xl text-xs text-[#2A0F1D] outline-none"
                  >
                    {TONES.map((t) => (
                      <option key={t} value={t}>{t}</option>
                    ))}
                  </select>

                  <label className="block text-xs font-bold uppercase tracking-wider text-[#571B37] mt-4 mb-2">
                    Book Length Preference
                  </label>
                  <select
                    value={preferredLength}
                    onChange={(e) => setPreferredLength(e.target.value)}
                    className="w-full px-3 py-2.5 bg-white border border-[#EAE3D9] rounded-xl text-xs text-[#2A0F1D] outline-none"
                  >
                    {LENGTHS.map((l) => (
                      <option key={l} value={l}>{l}</option>
                    ))}
                  </select>
                </div>
              </div>
            </div>
          )}

          {/* STEP 4: Disliked Elements & Favorite Authors */}
          {step === 4 && (
            <div className="space-y-6">
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <ShieldAlert className="w-4 h-4 text-[#9B2C2C]" />
                  <label className="block text-xs font-bold uppercase tracking-wider text-[#571B37]">
                    Disliked Elements to Downweight or Avoid
                  </label>
                </div>
                <p className="text-xs text-[#7A6E65] mb-3">
                  We penalize books with these elements in your recommendations.
                </p>
                <div className="flex flex-wrap gap-2">
                  {DISLIKED_OPTIONS.map((item) => {
                    const isSelected = dislikedElements.includes(item);
                    return (
                      <button
                        key={item}
                        type="button"
                        onClick={() => toggleItem(dislikedElements, setDislikedElements, item)}
                        className={`px-3 py-2 rounded-xl text-xs font-medium transition-all cursor-pointer inline-flex items-center gap-1.5 ${
                          isSelected
                            ? 'bg-[#9B2C2C] text-white shadow-xs'
                            : 'bg-white border border-[#EAE3D9] text-[#7A6E65] hover:border-[#9B2C2C]'
                        }`}
                      >
                        {isSelected ? <X className="w-3.5 h-3.5" /> : <Plus className="w-3.5 h-3.5" />}
                        {item}
                      </button>
                    );
                  })}
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-[#571B37] mb-2">
                  Favorite Authors (if known)
                </label>
                <p className="text-xs text-[#7A6E65] mb-2">
                  Comma-separated list (e.g., Donna Tartt, Kazuo Ishiguro, Emily Henry)
                </p>
                <input
                  type="text"
                  value={favoriteAuthors}
                  onChange={(e) => setFavoriteAuthors(e.target.value)}
                  placeholder="Donna Tartt, Leigh Bardugo, Richard Osman"
                  className="w-full px-4 py-3 bg-white border border-[#EAE3D9] rounded-2xl text-sm font-medium text-[#2A0F1D] outline-none focus:border-[#571B37]"
                />
              </div>

              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-[#571B37] mb-2">
                  Reading Difficulty
                </label>
                <div className="grid grid-cols-3 gap-2">
                  {DIFFICULTIES.map((d) => (
                    <button
                      key={d}
                      type="button"
                      onClick={() => setReadingDifficulty(d)}
                      className={`p-2.5 rounded-xl text-xs font-medium text-center transition-all cursor-pointer ${
                        readingDifficulty === d
                          ? 'bg-[#571B37] text-white'
                          : 'bg-white border border-[#EAE3D9] text-[#5A4F48] hover:bg-[#F5EFEB]'
                      }`}
                    >
                      {d}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

        </div>

        {/* Footer Actions */}
        <div className="p-6 border-t border-[#EAE3D9] bg-white flex items-center justify-between">
          {step > 1 ? (
            <button
              type="button"
              onClick={() => setStep(step - 1)}
              className="flex items-center gap-1.5 px-4 py-2.5 rounded-xl border border-[#EAE3D9] text-xs font-semibold text-[#571B37] hover:bg-[#F5EFEB] cursor-pointer"
            >
              <ChevronLeft className="w-4 h-4" />
              Previous
            </button>
          ) : (
            <div />
          )}

          {step < 4 ? (
            <button
              type="button"
              onClick={() => setStep(step + 1)}
              className="flex items-center gap-1.5 px-6 py-2.5 rounded-xl bg-[#571B37] hover:bg-[#3D1426] text-white text-xs font-semibold shadow-md transition-all cursor-pointer"
            >
              Next Step
              <ChevronRight className="w-4 h-4" />
            </button>
          ) : (
            <button
              type="button"
              onClick={handleSave}
              disabled={loading}
              className="flex items-center gap-2 px-6 py-2.5 rounded-xl bg-gradient-to-r from-[#571B37] to-[#C48332] hover:opacity-95 text-white text-xs font-bold shadow-lg transition-all cursor-pointer"
            >
              <Sparkles className="w-4 h-4 text-[#FFE8C2]" />
              {loading ? 'Generating Taste Mixes...' : 'Generate My Taste Mixes'}
            </button>
          )}
        </div>

      </div>
    </div>
  );
}
