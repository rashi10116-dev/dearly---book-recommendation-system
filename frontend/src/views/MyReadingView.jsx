import React, { useState, useEffect } from 'react';
import { BookmarkCheck, BookOpen, Clock, CheckCircle2, XCircle, Star, Plus, Trash2, Edit3, Search, Filter } from 'lucide-react';
import { api } from '../api/client';
import BookCover from '../components/BookCover';

export default function MyReadingView({ onSelectBook, onShelfChange }) {
  const [entries, setEntries] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('all');
  const [search, setSearch] = useState('');
  const [ratingFilter, setRatingFilter] = useState('');

  // Quick Add Modal state
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [searchCatalogQuery, setSearchCatalogQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searchingCatalog, setSearchingCatalog] = useState(false);

  useEffect(() => {
    loadReadingData();
  }, [statusFilter, search, ratingFilter]);

  const loadReadingData = async () => {
    setLoading(true);
    try {
      const [entriesData, statsData] = await Promise.all([
        api.reading.list({
          status: statusFilter !== 'all' ? statusFilter : undefined,
          q: search || undefined,
          rating: ratingFilter ? parseFloat(ratingFilter) : undefined,
        }),
        api.reading.stats(),
      ]);
      setEntries(entriesData);
      setStats(statsData);
    } catch (err) {
      console.error('Failed to load reading entries:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (entryId, bookTitle) => {
    if (!window.confirm(`Remove "${bookTitle}" from your reading history?`)) return;
    try {
      await api.reading.delete(entryId);
      await loadReadingData();
      if (onShelfChange) onShelfChange();
    } catch (err) {
      alert(`Could not delete reading entry: ${err.message}`);
    }
  };

  const handleSearchCatalog = async (q) => {
    setSearchCatalogQuery(q);
    if (!q.trim()) {
      setSearchResults([]);
      return;
    }
    setSearchingCatalog(true);
    try {
      const results = await api.books.list({ q, limit: 6 });
      setSearchResults(results);
    } catch (err) {
      console.error('Catalog search failed:', err);
    } finally {
      setSearchingCatalog(false);
    }
  };

  const handleQuickAddBook = async (bookId, status) => {
    try {
      await api.reading.addOrUpdate({
        book_id: bookId,
        status,
        rating: 5.0,
      });
      setIsAddModalOpen(false);
      setSearchCatalogQuery('');
      setSearchResults([]);
      await loadReadingData();
      if (onShelfChange) onShelfChange();
    } catch (err) {
      alert(`Could not add book: ${err.message}`);
    }
  };

  const STATUS_BADGES = {
    want_to_read: { label: 'Want to Read', color: 'bg-[#FAF7F2] text-[#571B37] border-[#EAE3D9]' },
    currently_reading: { label: 'Currently Reading', color: 'bg-[#C48332]/10 text-[#8C5819] border-[#C48332]/30' },
    completed: { label: 'Completed', color: 'bg-[#2A533E]/10 text-[#1C3829] border-[#2A533E]/30' },
    abandoned: { label: 'Abandoned', color: 'bg-[#9B2C2C]/10 text-[#9B2C2C] border-[#9B2C2C]/30' },
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 pb-24">
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#EAE3D9] pb-6">
        <div>
          <h1 className="font-editorial text-4xl font-bold text-[#2A0F1D]">My Reading Log</h1>
          <p className="text-xs sm:text-sm text-[#7A6E65] mt-1">
            Track your reading journeys, record ratings, and feed your discovery algorithm.
          </p>
        </div>

        <button
          onClick={() => setIsAddModalOpen(true)}
          className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-[#571B37] hover:bg-[#3D1426] text-white text-xs font-bold shadow-md transition-all cursor-pointer self-start sm:self-auto"
        >
          <Plus className="w-4 h-4 text-[#E09E4B]" />
          Log a Book
        </button>
      </div>

      {/* Stats Overview Bar */}
      {stats && (
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
          <div className="p-4 rounded-2xl bg-white border border-[#EAE3D9] text-center">
            <span className="text-[11px] font-bold uppercase tracking-wider text-[#7A6E65] block mb-1">
              Total Books
            </span>
            <span className="text-2xl font-bold font-editorial text-[#2A0F1D]">{stats.total}</span>
          </div>

          <div className="p-4 rounded-2xl bg-white border border-[#EAE3D9] text-center">
            <span className="text-[11px] font-bold uppercase tracking-wider text-[#7A6E65] block mb-1">
              Completed
            </span>
            <span className="text-2xl font-bold font-editorial text-[#2A533E]">{stats.completed}</span>
          </div>

          <div className="p-4 rounded-2xl bg-white border border-[#EAE3D9] text-center">
            <span className="text-[11px] font-bold uppercase tracking-wider text-[#7A6E65] block mb-1">
              In Progress
            </span>
            <span className="text-2xl font-bold font-editorial text-[#C48332]">{stats.currently_reading}</span>
          </div>

          <div className="p-4 rounded-2xl bg-white border border-[#EAE3D9] text-center">
            <span className="text-[11px] font-bold uppercase tracking-wider text-[#7A6E65] block mb-1">
              Want to Read
            </span>
            <span className="text-2xl font-bold font-editorial text-[#571B37]">{stats.want_to_read}</span>
          </div>

          <div className="col-span-2 sm:col-span-1 p-4 rounded-2xl bg-white border border-[#EAE3D9] text-center">
            <span className="text-[11px] font-bold uppercase tracking-wider text-[#7A6E65] block mb-1">
              Avg Rating
            </span>
            <span className="text-2xl font-bold font-editorial text-[#E09E4B] flex items-center justify-center gap-1">
              <Star className="w-5 h-5 fill-[#E09E4B]" />
              {stats.average_rating > 0 ? stats.average_rating : '—'}
            </span>
          </div>
        </div>
      )}

      {/* Filter Tabs & Search */}
      <div className="bg-white p-4 rounded-3xl border border-[#EAE3D9] flex flex-col md:flex-row gap-4 justify-between items-center">
        
        {/* Status Tabs */}
        <div className="flex bg-[#EAE3D9]/60 p-1 rounded-2xl border border-[#EAE3D9] w-full md:w-auto overflow-x-auto">
          {[
            { key: 'all', label: 'All Books' },
            { key: 'currently_reading', label: 'Reading' },
            { key: 'completed', label: 'Completed' },
            { key: 'want_to_read', label: 'Want to Read' },
            { key: 'abandoned', label: 'Abandoned' },
          ].map((tab) => (
            <button
              key={tab.key}
              onClick={() => setStatusFilter(tab.key)}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition-all cursor-pointer ${
                statusFilter === tab.key
                  ? 'bg-white text-[#3D1426] shadow-xs'
                  : 'text-[#695D56] hover:text-[#2A0F1D]'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Search & Rating Filter */}
        <div className="flex items-center gap-3 w-full md:w-auto">
          <div className="relative flex-1 md:w-64">
            <Search className="w-3.5 h-3.5 text-[#A89C94] absolute left-3 top-3" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Filter bookshelf..."
              className="w-full pl-9 pr-3 py-2 bg-[#FAF7F2] border border-[#EAE3D9] rounded-xl text-xs text-[#2A0F1D] outline-none"
            />
          </div>

          <select
            value={ratingFilter}
            onChange={(e) => setRatingFilter(e.target.value)}
            className="px-3 py-2 bg-[#FAF7F2] border border-[#EAE3D9] rounded-xl text-xs text-[#2A0F1D] outline-none cursor-pointer"
          >
            <option value="">All Ratings</option>
            <option value="5">5 Stars</option>
            <option value="4">4+ Stars</option>
            <option value="3">3+ Stars</option>
          </select>
        </div>

      </div>

      {/* Reading Entries List */}
      {loading ? (
        <div className="p-16 text-center text-[#7A6E65]">
          <div className="w-8 h-8 border-3 border-[#571B37] border-t-transparent rounded-full animate-spin mx-auto mb-3" />
          <p className="text-xs">Loading your bookshelf...</p>
        </div>
      ) : entries.length === 0 ? (
        <div className="p-16 text-center text-[#7A6E65] bg-white rounded-3xl border border-[#EAE3D9] space-y-3">
          <BookmarkCheck className="w-12 h-12 text-[#C48332] mx-auto opacity-70" />
          <h3 className="font-editorial text-2xl font-bold text-[#2A0F1D]">Your Bookshelf is Quiet</h3>
          <p className="text-xs max-w-sm mx-auto">
            {statusFilter !== 'all'
              ? `You don't have any books marked as '${statusFilter.replace('_', ' ')}' yet.`
              : 'Add your current or past reads to start training your personalized discovery engine.'}
          </p>
          <button
            onClick={() => setIsAddModalOpen(true)}
            className="px-5 py-2.5 rounded-xl bg-[#571B37] text-white text-xs font-semibold cursor-pointer"
          >
            Add Your First Book
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {entries.map((entry) => {
            const b = entry.book;
            const badge = STATUS_BADGES[entry.status] || STATUS_BADGES.want_to_read;
            return (
              <div
                key={entry.id}
                className="bg-white rounded-2xl border border-[#EAE3D9] p-5 shadow-xs hover:shadow-md transition-all flex flex-col sm:flex-row gap-5 items-start sm:items-center justify-between"
              >
                {/* Book & Cover */}
                <div
                  onClick={() => onSelectBook(b.id)}
                  className="flex items-center gap-4 cursor-pointer group flex-1"
                >
                  <div className="w-16 h-24 rounded-xl shadow-xs border border-[#EAE3D9] overflow-hidden group-hover:scale-105 transition-transform shrink-0">
                    <BookCover
                      src={b.cover_image}
                      title={b.title}
                      author={b.author}
                      genre={b.genre}
                    />
                  </div>
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider border ${badge.color}`}>
                        {badge.label}
                      </span>
                      <span className="text-xs text-[#7A6E65]">{b.genre}</span>
                    </div>

                    <h4 className="font-editorial font-bold text-lg text-[#2A0F1D] group-hover:text-[#571B37] leading-snug">
                      {b.title}
                    </h4>
                    <p className="text-xs text-[#7A6E65]">by {b.author}</p>

                    {/* User Rating */}
                    {entry.rating ? (
                      <div className="flex items-center gap-1 pt-1">
                        {[1, 2, 3, 4, 5].map((s) => (
                          <Star
                            key={s}
                            className={`w-3.5 h-3.5 ${
                              s <= entry.rating
                                ? 'fill-[#E09E4B] text-[#E09E4B]'
                                : 'text-[#D8CCC0]'
                            }`}
                          />
                        ))}
                        <span className="text-xs font-bold text-[#C48332] ml-1">{entry.rating} / 5</span>
                      </div>
                    ) : (
                      <span className="text-[11px] text-[#A89C94] italic block pt-0.5">Not rated yet</span>
                    )}

                    {/* Review Snippet */}
                    {entry.review && (
                      <p className="text-xs text-[#4A3E39] italic pt-1 line-clamp-1 max-w-xl">
                        "{entry.review}"
                      </p>
                    )}
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-2 self-end sm:self-center">
                  <button
                    onClick={() => onSelectBook(b.id)}
                    className="p-2 rounded-xl text-[#571B37] hover:bg-[#FAF7F2] border border-[#EAE3D9] text-xs font-semibold flex items-center gap-1 cursor-pointer"
                    title="Edit shelf status or rating"
                  >
                    <Edit3 className="w-3.5 h-3.5" />
                    <span className="hidden sm:inline">Edit</span>
                  </button>

                  <button
                    onClick={() => handleDelete(entry.id, b.title)}
                    className="p-2 rounded-xl text-[#9B2C2C] hover:bg-[#FDF2F2] border border-[#F8B4B4] transition-colors cursor-pointer"
                    title="Remove from reading history"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Quick Add Book Modal */}
      {isAddModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-[#2A0F1D]/50 backdrop-blur-sm animate-in fade-in">
          <div className="bg-[#FCFAF6] border border-[#EAE3D9] rounded-3xl max-w-lg w-full p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-[#EAE3D9] pb-3">
              <h3 className="font-editorial text-xl font-bold text-[#2A0F1D]">Log a Book to Shelf</h3>
              <button
                onClick={() => setIsAddModalOpen(false)}
                className="text-xs text-[#7A6E65] hover:text-[#2A0F1D]"
              >
                Cancel
              </button>
            </div>

            <div className="relative">
              <Search className="w-4 h-4 text-[#A89C94] absolute left-3.5 top-3" />
              <input
                type="text"
                value={searchCatalogQuery}
                onChange={(e) => handleSearchCatalog(e.target.value)}
                placeholder="Search catalog to add (e.g. Donna Tartt, Babel)..."
                className="w-full pl-10 pr-4 py-2.5 bg-white border border-[#EAE3D9] rounded-xl text-xs text-[#2A0F1D] outline-none"
                autoFocus
              />
            </div>

            {searchingCatalog && (
              <p className="text-xs text-[#7A6E65] text-center py-2">Searching catalogue...</p>
            )}

            <div className="space-y-2 max-h-64 overflow-y-auto">
              {searchResults.map((b) => (
                <div
                  key={b.id}
                  className="p-3 bg-white rounded-xl border border-[#EAE3D9] flex items-center justify-between gap-3"
                >
                  <div className="flex items-center gap-2.5">
                    <img
                      src={b.cover_image}
                      alt={b.title}
                      className="w-10 h-14 object-cover rounded-md"
                    />
                    <div>
                      <h5 className="font-bold text-xs text-[#2A0F1D] line-clamp-1">{b.title}</h5>
                      <p className="text-[11px] text-[#7A6E65]">{b.author}</p>
                    </div>
                  </div>

                  <div className="flex items-center gap-1.5 shrink-0">
                    <button
                      onClick={() => handleQuickAddBook(b.id, 'completed')}
                      className="px-2.5 py-1 bg-[#2A533E] text-white text-[10px] font-bold rounded-lg cursor-pointer"
                    >
                      Completed
                    </button>
                    <button
                      onClick={() => handleQuickAddBook(b.id, 'want_to_read')}
                      className="px-2.5 py-1 bg-[#571B37] text-white text-[10px] font-bold rounded-lg cursor-pointer"
                    >
                      Want to Read
                    </button>
                  </div>
                </div>
              ))}
            </div>

          </div>
        </div>
      )}

    </div>
  );
}
