import React, { useState, useEffect } from 'react';
import { X, Star, Bookmark, BookOpen, Clock, Calendar, Hash, ThumbsUp, ThumbsDown, Check, Trash2, ArrowRight } from 'lucide-react';
import { api } from '../api/client';
import BookCover from './BookCover';

export default function BookDetailModal({ bookId, isOpen, onClose, currentUser, onShelfChange, onSelectBook }) {
  const [book, setBook] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [shelfStatus, setShelfStatus] = useState('want_to_read');
  const [rating, setRating] = useState(0);
  const [hoverRating, setHoverRating] = useState(0);
  const [review, setReview] = useState('');
  const [likedTags, setLikedTags] = useState([]);
  const [dislikedTags, setDislikedTags] = useState([]);
  const [saveSuccess, setSaveSuccess] = useState(false);

  useEffect(() => {
    if (isOpen && bookId) {
      loadBookDetails();
    }
  }, [isOpen, bookId]);

  const loadBookDetails = async () => {
    setLoading(true);
    setSaveSuccess(false);
    try {
      const data = await api.books.get(bookId);
      setBook(data);
      if (data.user_status) {
        setShelfStatus(data.user_status);
        setRating(data.user_rating || 0);
        setReview(data.user_review || '');
      } else {
        setShelfStatus('want_to_read');
        setRating(0);
        setReview('');
      }
    } catch (err) {
      console.error('Failed to load book details:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveShelf = async () => {
    if (!currentUser) return;
    setSaving(true);
    try {
      await api.reading.addOrUpdate({
        book_id: book.id,
        status: shelfStatus,
        rating: rating > 0 ? rating : null,
        review: review.trim() || null,
        liked_elements: likedTags,
        disliked_elements: dislikedTags,
        favorite_tropes_themes: [],
      });
      setSaveSuccess(true);
      if (onShelfChange) onShelfChange();
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err) {
      alert(`Could not save reading status: ${err.message}`);
    } finally {
      setSaving(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-[#2A0F1D]/60 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-[#FCFAF6] border border-[#EAE3D9] rounded-3xl max-w-4xl w-full shadow-2xl overflow-hidden flex flex-col max-h-[90vh] relative">
        
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-5 right-5 z-10 p-2 rounded-full bg-white/80 backdrop-blur-xs text-[#7A6E65] hover:text-[#2A0F1D] shadow-xs hover:bg-white transition-colors cursor-pointer"
        >
          <X className="w-5 h-5" />
        </button>

        {loading || !book ? (
          <div className="p-16 text-center text-[#7A6E65]">
            <div className="w-10 h-10 border-4 border-[#571B37] border-t-transparent rounded-full animate-spin mx-auto mb-4" />
            <p className="text-sm">Fetching book metadata & recommendations...</p>
          </div>
        ) : (
          <div className="overflow-y-auto p-6 sm:p-8 space-y-8">
            
            {/* Top Section: Cover & Key Info */}
            <div className="grid grid-cols-1 md:grid-cols-12 gap-8 items-start">
              
              {/* Cover Column */}
              <div className="md:col-span-4 flex flex-col items-center">
                <div className="relative group w-48 sm:w-56 aspect-[2/3] rounded-2xl overflow-hidden shadow-xl border border-[#EAE3D9]/80 bg-[#EAE3D9]">
                  <BookCover
                    src={book.cover_image}
                    title={book.title}
                    author={book.author}
                    genre={book.genre}
                    className="group-hover:scale-103"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/40 via-transparent to-transparent pointer-events-none" />
                </div>

                {/* Popularity & Circulation Pill */}
                <div className="mt-4 px-3 py-1.5 rounded-full bg-[#EAE3D9]/60 border border-[#EAE3D9] text-[11px] font-semibold text-[#571B37] flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-[#C48332]" />
                  Circulation Index: {book.popularity_score ? Math.round(book.popularity_score) : 50}/100
                </div>
              </div>

              {/* Information Column */}
              <div className="md:col-span-8 space-y-4">
                <div>
                  <div className="flex flex-wrap items-center gap-2 mb-2">
                    <span className="px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider bg-[#571B37] text-white">
                      {book.genre}
                    </span>
                    {book.subgenre && (
                      <span className="px-3 py-1 rounded-full text-xs font-semibold bg-[#EAE3D9] text-[#571B37]">
                        {book.subgenre}
                      </span>
                    )}
                    {book.publication_year && (
                      <span className="text-xs text-[#7A6E65] flex items-center gap-1">
                        <Calendar className="w-3.5 h-3.5" />
                        {book.publication_year}
                      </span>
                    )}
                    {book.pages && (
                      <span className="text-xs text-[#7A6E65] flex items-center gap-1">
                        <BookOpen className="w-3.5 h-3.5" />
                        {book.pages} pages
                      </span>
                    )}
                  </div>

                  <h1 className="font-editorial text-3xl sm:text-4xl font-bold text-[#2A0F1D] leading-tight">
                    {book.title}
                  </h1>
                  <p className="text-base text-[#571B37] font-semibold mt-1">
                    by {book.author}
                  </p>
                </div>

                {/* Ratings ribbon */}
                <div className="flex items-center gap-4 py-2 border-y border-[#EAE3D9]">
                  <div className="flex items-center gap-1.5">
                    <Star className="w-5 h-5 fill-[#E09E4B] text-[#E09E4B]" />
                    <span className="font-bold text-sm text-[#2A0F1D]">{book.average_rating || 4.2}</span>
                    <span className="text-xs text-[#7A6E65]">/ 5</span>
                  </div>
                  <span className="text-[#D8CCC0]">•</span>
                  <div className="text-xs text-[#7A6E65]">
                    {book.ratings_count || 120} reader impressions
                  </div>
                  {book.isbn && (
                    <>
                      <span className="text-[#D8CCC0]">•</span>
                      <div className="text-xs text-[#7A6E65] font-mono">
                        ISBN: {book.isbn}
                      </div>
                    </>
                  )}
                </div>

                {/* Description */}
                <div>
                  <h3 className="text-xs font-bold uppercase tracking-wider text-[#7A6E65] mb-1.5">Synopsis</h3>
                  <p className="text-sm text-[#4A3E39] leading-relaxed">
                    {book.description}
                  </p>
                </div>

                {/* Narrative Attributes Chips */}
                <div className="space-y-3 pt-2">
                  {book.tropes && book.tropes.length > 0 && (
                    <div>
                      <span className="text-[11px] font-bold uppercase tracking-wider text-[#7A6E65] block mb-1">
                        Story Tropes
                      </span>
                      <div className="flex flex-wrap gap-1.5">
                        {book.tropes.map((t) => (
                          <span key={t} className="px-2.5 py-1 rounded-lg text-xs font-medium bg-[#2A533E]/10 text-[#1C3829] border border-[#2A533E]/20">
                            {t}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {book.themes && book.themes.length > 0 && (
                    <div>
                      <span className="text-[11px] font-bold uppercase tracking-wider text-[#7A6E65] block mb-1">
                        Themes
                      </span>
                      <div className="flex flex-wrap gap-1.5">
                        {book.themes.map((th) => (
                          <span key={th} className="px-2.5 py-1 rounded-lg text-xs font-medium bg-[#C48332]/10 text-[#8C5819] border border-[#C48332]/20">
                            {th}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className="flex flex-wrap gap-4 text-xs text-[#5A4F48] pt-1">
                    {book.writing_style && (
                      <div>
                        <span className="text-[#7A6E65]">Style:</span> <strong>{book.writing_style}</strong>
                      </div>
                    )}
                    {book.pacing && (
                      <div>
                        <span className="text-[#7A6E65]">Pacing:</span> <strong>{book.pacing}</strong>
                      </div>
                    )}
                    {book.emotional_tone && (
                      <div>
                        <span className="text-[#7A6E65]">Tone:</span> <strong>{book.emotional_tone}</strong>
                      </div>
                    )}
                  </div>
                </div>

              </div>
            </div>

            {/* Middle Section: Reader Log & Shelf Action (Only if logged in) */}
            {currentUser ? (
              <div className="bg-white border border-[#EAE3D9] rounded-2xl p-6 shadow-sm space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Bookmark className="w-5 h-5 text-[#571B37]" />
                    <h3 className="font-editorial text-xl font-bold text-[#2A0F1D]">My Reading Log</h3>
                  </div>
                  {saveSuccess && (
                    <span className="px-3 py-1 rounded-full bg-[#E8EFEA] text-[#1C3829] text-xs font-semibold flex items-center gap-1 animate-in fade-in">
                      <Check className="w-3.5 h-3.5" />
                      Shelf updated!
                    </span>
                  )}
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {/* Reading Status Selector */}
                  <div>
                    <label className="block text-xs font-bold text-[#571B37] mb-1.5 uppercase tracking-wider">
                      Reading Status
                    </label>
                    <div className="grid grid-cols-2 gap-2">
                      {[
                        { key: 'want_to_read', label: 'Want to Read' },
                        { key: 'currently_reading', label: 'Currently Reading' },
                        { key: 'completed', label: 'Completed' },
                        { key: 'abandoned', label: 'Abandoned' },
                      ].map((st) => (
                        <button
                          key={st.key}
                          type="button"
                          onClick={() => setShelfStatus(st.key)}
                          className={`p-2 rounded-xl text-xs font-semibold transition-all cursor-pointer ${
                            shelfStatus === st.key
                              ? 'bg-[#571B37] text-white shadow-xs'
                              : 'bg-[#FAF7F2] border border-[#EAE3D9] text-[#5A4F48] hover:border-[#571B37]'
                          }`}
                        >
                          {st.label}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Star Rating */}
                  <div>
                    <label className="block text-xs font-bold text-[#571B37] mb-1.5 uppercase tracking-wider">
                      My Star Rating
                    </label>
                    <div className="flex items-center gap-1.5 pt-1">
                      {[1, 2, 3, 4, 5].map((starVal) => {
                        const filled = (hoverRating || rating) >= starVal;
                        return (
                          <button
                            key={starVal}
                            type="button"
                            onMouseEnter={() => setHoverRating(starVal)}
                            onMouseLeave={() => setHoverRating(0)}
                            onClick={() => setRating(starVal)}
                            className="p-1 text-2xl transition-transform hover:scale-115 cursor-pointer"
                          >
                            <Star
                              className={`w-7 h-7 ${
                                filled
                                  ? 'fill-[#E09E4B] text-[#E09E4B]'
                                  : 'text-[#D8CCC0] hover:text-[#E09E4B]'
                              }`}
                            />
                          </button>
                        );
                      })}
                      {rating > 0 && (
                        <span className="text-xs font-bold text-[#C48332] ml-2">
                          {rating} / 5 Stars
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                {/* Written Review */}
                <div>
                  <label className="block text-xs font-bold text-[#571B37] mb-1.5 uppercase tracking-wider">
                    Reader Reflections & Review (Optional)
                  </label>
                  <textarea
                    value={review}
                    onChange={(e) => setReview(e.target.value)}
                    placeholder="What made this book memorable? What themes or character arcs stood out?"
                    rows={3}
                    className="w-full p-3 bg-[#FAF7F2] border border-[#EAE3D9] rounded-xl text-xs text-[#2A0F1D] focus:ring-2 focus:ring-[#571B37]/20 focus:border-[#571B37] outline-none"
                  />
                </div>

                <div className="flex justify-end pt-2">
                  <button
                    type="button"
                    onClick={handleSaveShelf}
                    disabled={saving}
                    className="px-6 py-2.5 rounded-xl bg-[#571B37] hover:bg-[#3D1426] text-white text-xs font-bold shadow-sm transition-all cursor-pointer"
                  >
                    {saving ? 'Updating Shelf...' : 'Save to My Shelf'}
                  </button>
                </div>
              </div>
            ) : (
              <div className="p-4 rounded-2xl bg-[#EAE3D9]/40 border border-[#EAE3D9] text-center text-xs text-[#7A6E65]">
                <p>Sign in to add this book to your reading shelf, record ratings, and feed your discovery algorithm.</p>
              </div>
            )}

            {/* Bottom Section: Similar Books */}
            {book.similar_books && book.similar_books.length > 0 && (
              <div>
                <h3 className="font-editorial text-xl font-bold text-[#2A0F1D] mb-4">
                  Readers who explored this also loved
                </h3>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                  {book.similar_books.map((sb) => (
                    <div
                      key={sb.id}
                      onClick={() => onSelectBook(sb.id)}
                      className="group cursor-pointer bg-white p-3 rounded-2xl border border-[#EAE3D9] hover:shadow-md transition-all hover:scale-102"
                    >
                      <div className="aspect-[2/3] rounded-xl overflow-hidden mb-2 bg-[#EAE3D9]">
                        <BookCover
                          src={sb.cover_image}
                          title={sb.title}
                          author={sb.author}
                          genre={sb.genre}
                          className="group-hover:scale-105"
                        />
                      </div>
                      <h4 className="font-bold text-xs text-[#2A0F1D] line-clamp-1 group-hover:text-[#571B37]">
                        {sb.title}
                      </h4>
                      <p className="text-[11px] text-[#7A6E65] line-clamp-1">
                        {sb.author}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}

          </div>
        )}

      </div>
    </div>
  );
}
