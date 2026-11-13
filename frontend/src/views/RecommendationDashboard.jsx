import React, { useState, useEffect } from 'react';
import { Sparkles, Shuffle, BookOpen, Feather, Star, Plus, Check, Info, Sliders, RefreshCw, BookmarkCheck, Globe, Compass } from 'lucide-react';
import { api } from '../api/client';
import BookCover from '../components/BookCover';

export default function RecommendationDashboard({
  currentUser,
  onSelectBook,
  onOpenPreferences,
  onShelfChange
}) {
  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeGenreTab, setActiveGenreTab] = useState('');
  const [selectedRationale, setSelectedRationale] = useState(null);
  const [addedBookIds, setAddedBookIds] = useState(new Set());

  useEffect(() => {
    loadRecommendations();
  }, [currentUser]);

  const loadRecommendations = async () => {
    setLoading(true);
    try {
      const data = await api.recommendations.getDashboard();
      setDashboard(data);
      const genreKeys = Object.keys(data.taste_mixes || {});
      if (genreKeys.length > 0) {
        setActiveGenreTab(genreKeys[0]);
      }
    } catch (err) {
      console.error('Failed to load recommendation dashboard:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleQuickAdd = async (e, bookId, status = 'want_to_read') => {
    e.stopPropagation();
    try {
      await api.reading.addOrUpdate({
        book_id: bookId,
        status,
        rating: null,
        review: null,
        liked_elements: [],
        disliked_elements: [],
        favorite_tropes_themes: [],
      });
      setAddedBookIds((prev) => new Set([...prev, bookId]));
      if (onShelfChange) onShelfChange();
    } catch (err) {
      alert(`Could not add to shelf: ${err.message}`);
    }
  };

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto px-4 py-20 text-center space-y-4">
        <div className="w-12 h-12 border-4 border-[#571B37] border-t-transparent rounded-full animate-spin mx-auto" />
        <h3 className="font-editorial text-2xl font-bold text-[#2A0F1D]">Synthesizing Your Taste Profile...</h3>
        <p className="text-xs text-[#7A6E65]">Fitting TF-IDF models, balancing diversity reranking, and indexing serendipitous reads.</p>
      </div>
    );
  }

  if (!dashboard) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-16 text-center space-y-4">
        <h3 className="font-editorial text-2xl font-bold text-[#2A0F1D]">No Recommendations Yet</h3>
        <p className="text-xs text-[#7A6E65]">Complete your reader onboarding to generate your personalized mixes.</p>
        <button
          onClick={onOpenPreferences}
          className="px-6 py-2.5 rounded-xl bg-[#571B37] text-white text-xs font-bold"
        >
          Set Taste Preferences
        </button>
      </div>
    );
  }

  const genreList = Object.keys(dashboard.taste_mixes || {});
  const currentGenreItems = dashboard.taste_mixes?.[activeGenreTab] || [];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-12 pb-24">
      
      {/* Top Welcome Ribbon */}
      <div className="bg-gradient-to-r from-white via-[#FCFAF6] to-white p-6 sm:p-8 rounded-3xl border border-[#EAE3D9] shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className="w-2.5 h-2.5 rounded-full bg-[#2A533E]" />
            <span className="text-xs font-semibold text-[#1C3829] uppercase tracking-wider">
              {dashboard.has_reading_history ? 'Dynamic Taste Profile Active' : 'Initial Preference Profile'}
            </span>
          </div>
          <h1 className="font-editorial text-3xl sm:text-4xl font-bold text-[#2A0F1D]">
            Welcome back, {dashboard.user_display_name}
          </h1>
          <p className="text-xs sm:text-sm text-[#7A6E65] mt-1 max-w-2xl leading-relaxed">
            {dashboard.discovery_summary}
          </p>
        </div>

        <div className="flex items-center gap-3 shrink-0">
          <button
            onClick={loadRecommendations}
            className="p-3 rounded-2xl bg-white border border-[#EAE3D9] text-[#7A6E65] hover:text-[#571B37] hover:border-[#571B37] transition-all cursor-pointer shadow-xs"
            title="Refresh recommendations"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
          <button
            onClick={onOpenPreferences}
            className="flex items-center gap-2 px-5 py-3 rounded-2xl bg-[#571B37] hover:bg-[#3D1426] text-white text-xs font-bold shadow-md transition-all cursor-pointer"
          >
            <Sliders className="w-4 h-4 text-[#E09E4B]" />
            Tune Taste Profile
          </button>
        </div>
      </div>

      {/* =========================================================================
          COLLECTION A: "Your Taste" (Top 3 Genres Tabs)
          ========================================================================= */}
      <section className="space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4 border-b border-[#EAE3D9] pb-4">
          <div>
            <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-[#571B37]">
              <Sparkles className="w-4 h-4 text-[#C48332]" />
              Collection A
            </div>
            <h2 className="font-editorial text-3xl font-bold text-[#2A0F1D] mt-0.5">Your Taste</h2>
            <p className="text-xs text-[#7A6E65]">
              Ranked within your top three genres, calibrated by your favorite tropes and feedback.
            </p>
          </div>

          {/* Genre Tabs */}
          {genreList.length > 0 && (
            <div className="flex bg-[#EAE3D9]/60 p-1 rounded-2xl border border-[#EAE3D9] overflow-x-auto">
              {genreList.map((g) => (
                <button
                  key={g}
                  onClick={() => setActiveGenreTab(g)}
                  className={`px-4 py-2 rounded-xl text-xs font-semibold whitespace-nowrap transition-all cursor-pointer ${
                    activeGenreTab === g
                      ? 'bg-white text-[#3D1426] shadow-xs'
                      : 'text-[#695D56] hover:text-[#2A0F1D]'
                  }`}
                >
                  {g}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Book Cards Grid */}
        {currentGenreItems.length === 0 ? (
          <div className="p-8 text-center text-xs text-[#7A6E65] bg-white rounded-2xl border border-[#EAE3D9]">
            No unread books remaining in {activeGenreTab}. Explore other genres or import more books!
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {currentGenreItems.map((item) => (
              <RecommendationCard
                key={item.book.id}
                item={item}
                isAdded={addedBookIds.has(item.book.id)}
                onSelect={() => onSelectBook(item.book.id)}
                onQuickAdd={(e) => handleQuickAdd(e, item.book.id)}
                onShowRationale={() => setSelectedRationale(item)}
              />
            ))}
          </div>
        )}
      </section>

      {/* =========================================================================
          COLLECTION B: "Your Unexpected Next Read" (Cross-Genre / Serendipity)
          ========================================================================= */}
      <section className="space-y-6">
        <div className="flex items-center justify-between border-b border-[#EAE3D9] pb-4">
          <div>
            <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-[#C48332]">
              <Shuffle className="w-4 h-4 text-[#C48332]" />
              Collection B • Serendipity & Anti-Popularity
            </div>
            <h2 className="font-editorial text-3xl font-bold text-[#2A0F1D] mt-0.5">Your Unexpected Next Read</h2>
            <p className="text-xs text-[#7A6E65]">
              Surprising discoveries outside your selected genres that share your core narrative DNA.
            </p>
          </div>
          <span className="text-[11px] font-semibold px-3 py-1 rounded-full bg-[#E09E4B]/15 text-[#925514] hidden sm:block">
            Cross-Genre Resonance
          </span>
        </div>

        {dashboard.unexpected_mix?.length === 0 ? (
          <div className="p-8 text-center text-xs text-[#7A6E65] bg-white rounded-2xl border border-[#EAE3D9]">
            Add more varied tropes in your Taste Profile to uncover unexpected cross-genre recommendations.
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {dashboard.unexpected_mix.map((item) => (
              <RecommendationCard
                key={item.book.id}
                item={item}
                isUnexpected
                isAdded={addedBookIds.has(item.book.id)}
                onSelect={() => onSelectBook(item.book.id)}
                onQuickAdd={(e) => handleQuickAdd(e, item.book.id)}
                onShowRationale={() => setSelectedRationale(item)}
              />
            ))}
          </div>
        )}
      </section>

      {/* =========================================================================
          COLLECTION C: "From Authors You've Read"
          ========================================================================= */}
      <section className="space-y-6">
        <div className="border-b border-[#EAE3D9] pb-4">
          <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-[#571B37]">
            <Feather className="w-4 h-4 text-[#571B37]" />
            Collection C • Author Synergy
          </div>
          <h2 className="font-editorial text-3xl font-bold text-[#2A0F1D] mt-0.5">From Authors You've Read</h2>
          <p className="text-xs text-[#7A6E65]">
            When you complete at least 2 distinct books by an author, their unread works are featured here.
          </p>
        </div>

        {dashboard.author_mix?.length === 0 ? (
          <div className="p-8 rounded-3xl bg-white border border-[#EAE3D9] text-center space-y-2">
            <BookOpen className="w-8 h-8 text-[#C48332] mx-auto opacity-70" />
            <h4 className="font-editorial text-lg font-bold text-[#2A0F1D]">Unlock Dedicated Author Mixes</h4>
            <p className="text-xs text-[#7A6E65] max-w-md mx-auto">
              Read and log at least <strong>2 books by the same author</strong> in My Reading to automatically trigger custom author shelves here.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {dashboard.author_mix.map((item) => (
              <RecommendationCard
                key={item.book.id}
                item={item}
                isAdded={addedBookIds.has(item.book.id)}
                onSelect={() => onSelectBook(item.book.id)}
                onQuickAdd={(e) => handleQuickAdd(e, item.book.id)}
                onShowRationale={() => setSelectedRationale(item)}
              />
            ))}
          </div>
        )}
      </section>

      {/* =========================================================================
          COLLECTION D: "Because You Enjoyed..."
          ========================================================================= */}
      <section className="space-y-6">
        <div className="border-b border-[#EAE3D9] pb-4">
          <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-[#1C3829]">
            <BookmarkCheck className="w-4 h-4 text-[#2A533E]" />
            Collection D • Item-to-Item Similarity
          </div>
          <h2 className="font-editorial text-3xl font-bold text-[#2A0F1D] mt-0.5">
            {dashboard.anchor_book_title
              ? `Because You Enjoyed '${dashboard.anchor_book_title}'`
              : 'Because You Enjoyed...'}
          </h2>
          <p className="text-xs text-[#7A6E65]">
            Content-linked to your positively rated reads, matching narrative pacing, tropes, and writing style.
          </p>
        </div>

        {dashboard.because_you_enjoyed_mix?.length === 0 ? (
          <div className="p-8 rounded-3xl bg-white border border-[#EAE3D9] text-center space-y-2">
            <Star className="w-8 h-8 text-[#C48332] mx-auto opacity-70" />
            <h4 className="font-editorial text-lg font-bold text-[#2A0F1D]">No High-Rated Books Logged Yet</h4>
            <p className="text-xs text-[#7A6E65] max-w-md mx-auto">
              Rate a book 4 or 5 stars in <strong>My Reading</strong> to unlock story DNA recommendations linked to that book.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {dashboard.because_you_enjoyed_mix.map((item) => (
              <RecommendationCard
                key={item.book.id}
                item={item}
                isAdded={addedBookIds.has(item.book.id)}
                onSelect={() => onSelectBook(item.book.id)}
                onQuickAdd={(e) => handleQuickAdd(e, item.book.id)}
                onShowRationale={() => setSelectedRationale(item)}
              />
            ))}
          </div>
        )}
      </section>

      {/* =========================================================================
          COLLECTION E: "Explore New Genres" (Genre Expansion)
          ========================================================================= */}
      {dashboard.explore_genres_mix && dashboard.explore_genres_mix.length > 0 && (
        <section className="space-y-6">
          <div className="flex items-center justify-between border-b border-[#EAE3D9] pb-4">
            <div>
              <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-[#3D1426]">
                <Globe className="w-4 h-4 text-[#C48332]" />
                Collection E • Horizon Expansion
              </div>
              <h2 className="font-editorial text-3xl font-bold text-[#2A0F1D] mt-0.5">Explore New Genres</h2>
              <p className="text-xs text-[#7A6E65]">
                Top-rated literary works beyond your usual shelf, selected to broaden your horizons.
              </p>
            </div>
            <span className="text-[11px] font-semibold px-3 py-1 rounded-full bg-[#571B37]/10 text-[#571B37] hidden sm:block">
              Genre Expansion
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {dashboard.explore_genres_mix.map((item) => (
              <RecommendationCard
                key={item.book.id}
                item={item}
                isAdded={addedBookIds.has(item.book.id)}
                onSelect={() => onSelectBook(item.book.id)}
                onQuickAdd={(e) => handleQuickAdd(e, item.book.id)}
                onShowRationale={() => setSelectedRationale(item)}
              />
            ))}
          </div>
        </section>
      )}

      {/* =========================================================================
          COLLECTION F: "Hidden Gems" (Understated Circulation, High Appreciation)
          ========================================================================= */}
      {dashboard.hidden_gems_mix && dashboard.hidden_gems_mix.length > 0 && (
        <section className="space-y-6">
          <div className="flex items-center justify-between border-b border-[#EAE3D9] pb-4">
            <div>
              <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-[#1C3829]">
                <Compass className="w-4 h-4 text-[#2A533E]" />
                Collection F • Undiscovered Masterpieces
              </div>
              <h2 className="font-editorial text-3xl font-bold text-[#2A0F1D] mt-0.5">Hidden Gems</h2>
              <p className="text-xs text-[#7A6E65]">
                Highly praised by discerning readers yet outside mainstream algorithmic echo chambers.
              </p>
            </div>
            <span className="text-[11px] font-semibold px-3 py-1 rounded-full bg-[#2A533E]/10 text-[#1C3829] hidden sm:block">
              Low Circulation • High Rating
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {dashboard.hidden_gems_mix.map((item) => (
              <RecommendationCard
                key={item.book.id}
                item={item}
                isAdded={addedBookIds.has(item.book.id)}
                onSelect={() => onSelectBook(item.book.id)}
                onQuickAdd={(e) => handleQuickAdd(e, item.book.id)}
                onShowRationale={() => setSelectedRationale(item)}
              />
            ))}
          </div>
        </section>
      )}

      {/* Rationale Explanation Popup Modal */}
      {selectedRationale && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-[#2A0F1D]/50 backdrop-blur-sm animate-in fade-in">
          <div className="bg-[#FAF7F2] border border-[#EAE3D9] rounded-3xl max-w-md w-full p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-[#EAE3D9] pb-3">
              <h3 className="font-editorial text-xl font-bold text-[#2A0F1D]">Recommendation Rationale</h3>
              <button
                onClick={() => setSelectedRationale(null)}
                className="text-xs text-[#7A6E65] hover:text-[#2A0F1D]"
              >
                Close
              </button>
            </div>
            
            <div>
              <h4 className="font-bold text-sm text-[#571B37]">{selectedRationale.book.title}</h4>
              <p className="text-xs text-[#7A6E65]">by {selectedRationale.book.author}</p>
            </div>

            <div className="p-4 bg-white rounded-2xl border border-[#EAE3D9] text-xs text-[#4A3E39] leading-relaxed">
              {selectedRationale.rationale}
            </div>

            {selectedRationale.matched_signals && selectedRationale.matched_signals.length > 0 && (
              <div>
                <span className="text-[11px] font-bold uppercase tracking-wider text-[#7A6E65] block mb-1">
                  Active Taste Signals
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {selectedRationale.matched_signals.map((s, idx) => (
                    <span key={idx} className="px-2.5 py-1 rounded-lg text-xs font-semibold bg-[#571B37]/10 text-[#571B37]">
                      {s}
                    </span>
                  ))}
                </div>
              </div>
            )}

            <button
              onClick={() => setSelectedRationale(null)}
              className="w-full py-2.5 rounded-xl bg-[#571B37] text-white text-xs font-bold"
            >
              Got it
            </button>
          </div>
        </div>
      )}

    </div>
  );
}

// Reusable Recommendation Card
function RecommendationCard({ item, isUnexpected = false, isAdded, onSelect, onQuickAdd, onShowRationale }) {
  const { book, rationale, novelty_note, collection_name, matched_signals } = item;

  const renderBadge = () => {
    if (collection_name?.includes("Hidden Gems") || novelty_note?.includes("Hidden")) {
      return (
        <div className="absolute top-2.5 right-2.5 px-2.5 py-1 rounded-full bg-[#1C3829]/90 backdrop-blur-xs text-white text-[10px] font-bold flex items-center gap-1 shadow-xs">
          <Star className="w-3 h-3 text-[#A3E635]" />
          Hidden Gem
        </div>
      );
    }
    if (collection_name?.includes("Explore New Genres")) {
      return (
        <div className="absolute top-2.5 right-2.5 px-2.5 py-1 rounded-full bg-[#3D1426]/90 backdrop-blur-xs text-white text-[10px] font-bold flex items-center gap-1 shadow-xs">
          <Globe className="w-3 h-3 text-[#E09E4B]" />
          Explore Genre
        </div>
      );
    }
    if (isUnexpected) {
      return (
        <div className="absolute top-2.5 right-2.5 px-2.5 py-1 rounded-full bg-[#C48332]/90 backdrop-blur-xs text-white text-[10px] font-bold flex items-center gap-1 shadow-xs">
          <Shuffle className="w-3 h-3 text-[#FAF7F2]" />
          Serendipity Pick
        </div>
      );
    }
    if (collection_name?.includes("Authors")) {
      return (
        <div className="absolute top-2.5 right-2.5 px-2.5 py-1 rounded-full bg-[#571B37]/85 backdrop-blur-xs text-white text-[10px] font-bold flex items-center gap-1 shadow-xs">
          <Feather className="w-3 h-3 text-[#E09E4B]" />
          Author Synergy
        </div>
      );
    }
    if (collection_name?.includes("Because")) {
      return (
        <div className="absolute top-2.5 right-2.5 px-2.5 py-1 rounded-full bg-[#2A533E]/90 backdrop-blur-xs text-white text-[10px] font-bold flex items-center gap-1 shadow-xs">
          <BookmarkCheck className="w-3 h-3 text-[#A3E635]" />
          Story DNA
        </div>
      );
    }
    return (
      <div className="absolute top-2.5 right-2.5 px-2.5 py-1 rounded-full bg-[#2A0F1D]/80 backdrop-blur-xs text-white text-[10px] font-bold flex items-center gap-1 shadow-xs">
        <Sparkles className="w-3 h-3 text-[#E09E4B]" />
        Curated Taste
      </div>
    );
  };

  return (
    <div
      onClick={onSelect}
      className="group cursor-pointer bg-white rounded-3xl border border-[#EAE3D9] p-4 flex flex-col justify-between shadow-xs hover:shadow-xl transition-all hover:-translate-y-1 relative"
    >
      <div>
        {/* Cover with badge */}
        <div className="relative aspect-[2/3] rounded-2xl overflow-hidden mb-3 bg-[#EAE3D9] shadow-sm">
          <BookCover
            src={book.cover_image}
            title={book.title}
            author={book.author}
            genre={book.genre}
            className="group-hover:scale-105"
          />
          {renderBadge()}
          {novelty_note && (
            <div className="absolute bottom-2.5 left-2.5 right-2.5 px-2.5 py-1 rounded-xl bg-[#C48332]/90 backdrop-blur-xs text-white text-[10px] font-bold text-center truncate">
              {novelty_note}
            </div>
          )}
        </div>

        {/* Title & Author */}
        <h4 className="font-editorial text-lg font-bold text-[#2A0F1D] leading-tight line-clamp-1 group-hover:text-[#571B37] transition-colors">
          {book.title}
        </h4>
        <p className="text-xs text-[#7A6E65] font-medium mt-0.5 line-clamp-1">
          {book.author}
        </p>

        {/* Genre & Tags */}
        <div className="flex flex-wrap gap-1.5 mt-2">
          <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded-md bg-[#FAF7F2] text-[#571B37] border border-[#EAE3D9]">
            {book.genre}
          </span>
          {book.tropes && book.tropes.length > 0 && (
            <span className="text-[10px] font-medium px-2 py-0.5 rounded-md bg-[#2A533E]/10 text-[#1C3829] line-clamp-1">
              {book.tropes[0]}
            </span>
          )}
        </div>

        {/* Concise Rationale Snippet */}
        <p className="text-[11px] text-[#695D56] italic mt-3 line-clamp-2 leading-relaxed">
          "{rationale}"
        </p>
      </div>

      {/* Card Actions */}
      <div className="pt-4 border-t border-[#EAE3D9]/60 flex items-center justify-between gap-2 mt-3">
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            onShowRationale();
          }}
          className="text-[11px] font-bold text-[#571B37] hover:underline flex items-center gap-1"
        >
          <Info className="w-3.5 h-3.5" />
          Why?
        </button>

        <button
          type="button"
          onClick={onQuickAdd}
          disabled={isAdded}
          className={`px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center gap-1 transition-all cursor-pointer ${
            isAdded
              ? 'bg-[#E8EFEA] text-[#1C3829]'
              : 'bg-[#FAF7F2] hover:bg-[#571B37] hover:text-white text-[#571B37] border border-[#EAE3D9]'
          }`}
        >
          {isAdded ? (
            <>
              <Check className="w-3.5 h-3.5" />
              On Shelf
            </>
          ) : (
            <>
              <Plus className="w-3.5 h-3.5" />
              Add to Shelf
            </>
          )}
        </button>
      </div>
    </div>
  );
}
