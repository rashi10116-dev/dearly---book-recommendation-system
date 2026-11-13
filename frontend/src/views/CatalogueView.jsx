import React, { useState, useEffect, useRef } from 'react';
import { Search, Star, Plus, Check, BookOpen, X, ChevronLeft, ChevronRight, Globe, Sparkles, ArrowLeft, Calendar, User, Compass } from 'lucide-react';
import { api } from '../api/client';
import BookCover from '../components/BookCover';

export default function CatalogueView({ onSelectBook, currentUser, onShelfChange }) {
  // Discovery State
  const [discoverySections, setDiscoverySections] = useState([]);
  const [discoveryLoading, setDiscoveryLoading] = useState(true);
  const [expandedSection, setExpandedSection] = useState(null);
  const [sectionBooks, setSectionBooks] = useState([]);
  const [sectionLoading, setSectionLoading] = useState(false);
  const [sectionPage, setSectionPage] = useState(1);
  const [sectionTotal, setSectionTotal] = useState(0);

  // Search & Filter State
  const [books, setBooks] = useState([]);
  const [genres, setGenres] = useState([]);
  const [tropes, setTropes] = useState([]);
  const [searchLoading, setSearchLoading] = useState(false);

  const [search, setSearch] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [selectedGenre, setSelectedGenre] = useState('');
  const [selectedTrope, setSelectedTrope] = useState('');
  const [selectedPacing, setSelectedPacing] = useState('');
  const [authorFilter, setAuthorFilter] = useState('');
  const [yearMinFilter, setYearMinFilter] = useState('');
  const [yearMaxFilter, setYearMaxFilter] = useState('');
  const [sortBy, setSortBy] = useState('popularity');
  const [page, setPage] = useState(1);
  const pageSize = 24;

  const [addedIds, setAddedIds] = useState(new Set());
  const debounceTimerRef = useRef(null);

  // Determine active view mode
  const isSearchingOrFiltering = Boolean(
    debouncedSearch || selectedGenre || selectedTrope || selectedPacing || authorFilter || yearMinFilter || yearMaxFilter
  );
  const isViewingExpandedSection = Boolean(expandedSection && !isSearchingOrFiltering);

  // Debounce search input by 350ms to prevent excessive API requests
  useEffect(() => {
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }
    debounceTimerRef.current = setTimeout(() => {
      setDebouncedSearch(search.trim());
      setPage(1);
    }, 350);

    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
    };
  }, [search]);

  // Initial load: Fetch Discovery Sections and Filter metadata
  useEffect(() => {
    loadDiscoveryCatalogue();
    loadFiltersData();
  }, []);

  // Fetch search/filtered books when active
  useEffect(() => {
    if (isSearchingOrFiltering) {
      fetchFilteredBooks();
    }
  }, [debouncedSearch, selectedGenre, selectedTrope, selectedPacing, authorFilter, yearMinFilter, yearMaxFilter, sortBy, page]);

  // Fetch expanded section books when active
  useEffect(() => {
    if (isViewingExpandedSection && expandedSection) {
      fetchExpandedSectionBooks();
    }
  }, [expandedSection, sectionPage, sortBy, authorFilter, yearMinFilter, yearMaxFilter]);

  const loadDiscoveryCatalogue = async () => {
    setDiscoveryLoading(true);
    try {
      const data = await api.books.discovery();
      setDiscoverySections(data.sections || []);
    } catch (err) {
      console.error('Failed to load discovery catalogue:', err);
    } finally {
      setDiscoveryLoading(false);
    }
  };

  const loadFiltersData = async () => {
    try {
      const [gData, tData] = await Promise.all([
        api.books.genres(),
        api.books.tropes(),
      ]);
      setGenres(gData);
      setTropes(tData);
    } catch (err) {
      console.error('Failed to load filter metadata:', err);
    }
  };

  const fetchFilteredBooks = async () => {
    setSearchLoading(true);
    try {
      const data = await api.books.list({
        q: debouncedSearch || undefined,
        genre: selectedGenre || undefined,
        trope: selectedTrope || undefined,
        pacing: selectedPacing || undefined,
        author: authorFilter || undefined,
        year_min: yearMinFilter ? parseInt(yearMinFilter, 10) : undefined,
        year_max: yearMaxFilter ? parseInt(yearMaxFilter, 10) : undefined,
        sort_by: sortBy,
        limit: pageSize,
        offset: (page - 1) * pageSize,
      });
      setBooks(data);
    } catch (err) {
      console.error('Failed to fetch filtered books:', err);
    } finally {
      setSearchLoading(false);
    }
  };

  const fetchExpandedSectionBooks = async () => {
    if (!expandedSection) return;
    setSectionLoading(true);
    try {
      const data = await api.books.discoverySection(expandedSection.id, {
        page: sectionPage,
        limit: 18,
        sort_by: sortBy,
        author: authorFilter || undefined,
        year_min: yearMinFilter ? parseInt(yearMinFilter, 10) : undefined,
        year_max: yearMaxFilter ? parseInt(yearMaxFilter, 10) : undefined,
      });
      setSectionBooks(data.books || []);
      setSectionTotal(data.total_available || 0);
    } catch (err) {
      console.error(`Failed to load section ${expandedSection.id}:`, err);
    } finally {
      setSectionLoading(false);
    }
  };

  const handleQuickAdd = async (e, bookId) => {
    e.stopPropagation();
    if (!currentUser) return;
    try {
      await api.reading.addOrUpdate({
        book_id: bookId,
        status: 'want_to_read',
      });
      setAddedIds((prev) => new Set([...prev, bookId]));
      if (onShelfChange) onShelfChange();
    } catch (err) {
      alert(`Could not add to shelf: ${err.message}`);
    }
  };

  const resetAllFilters = () => {
    setSearch('');
    setDebouncedSearch('');
    setSelectedGenre('');
    setSelectedTrope('');
    setSelectedPacing('');
    setAuthorFilter('');
    setYearMinFilter('');
    setYearMaxFilter('');
    setSortBy('popularity');
    setPage(1);
    setExpandedSection(null);
  };

  const renderSourceChip = (sourceProvider) => {
    const prov = (sourceProvider || '').toLowerCase();
    if (prov.includes('google_books') && prov.includes('open_library')) {
      return (
        <span className="text-[9px] font-bold px-1.5 py-0.5 rounded-md bg-[#2A533E]/15 text-[#1C3829] border border-[#2A533E]/20">
          Dual API Verified
        </span>
      );
    }
    if (prov.includes('google_books')) {
      return (
        <span className="text-[9px] font-bold px-1.5 py-0.5 rounded-md bg-[#571B37]/10 text-[#571B37] border border-[#571B37]/15">
          Google Books
        </span>
      );
    }
    if (prov.includes('open_library')) {
      return (
        <span className="text-[9px] font-bold px-1.5 py-0.5 rounded-md bg-[#C48332]/15 text-[#925514] border border-[#C48332]/25">
          Open Library
        </span>
      );
    }
    return (
      <span className="text-[9px] font-bold px-1.5 py-0.5 rounded-md bg-[#EAE3D9] text-[#7A6E65]">
        Curated Classic
      </span>
    );
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 pb-24">
      
      {/* Top Header */}
      <div className="border-b border-[#EAE3D9] pb-6 flex flex-col sm:flex-row sm:items-end justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-[#571B37] mb-1">
            <Globe className="w-3.5 h-3.5 text-[#C48332]" />
            Google Books & Open Library Catalog
          </div>
          <h1 className="font-editorial text-4xl font-bold text-[#2A0F1D]">Explore the Catalogue</h1>
          <p className="text-xs sm:text-sm text-[#7A6E65] mt-1 max-w-2xl">
            Live discovery backed by real-time Google Books and Open Library integrations. Discover books across 12 curated sections or search dynamically.
          </p>
        </div>

        {debouncedSearch && (
          <div className="text-xs text-[#571B37] bg-white px-3 py-1.5 rounded-full border border-[#EAE3D9] shadow-xs flex items-center gap-1.5 self-start sm:self-auto">
            <Sparkles className="w-3.5 h-3.5 text-[#C48332]" />
            Real-time API search for "{debouncedSearch}"
          </div>
        )}
      </div>

      {/* Search & Filter Controls Ribbon */}
      <div className="bg-white p-5 rounded-3xl border border-[#EAE3D9] shadow-xs space-y-4">
        
        {/* Search Bar + Sort */}
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-[#A89C94] absolute left-3.5 top-3.5" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by title, author, ISBN, or keywords across Google Books & Open Library..."
              className="w-full pl-10 pr-10 py-2.5 bg-[#FAF7F2] border border-[#EAE3D9] rounded-2xl text-xs sm:text-sm text-[#2A0F1D] focus:ring-2 focus:ring-[#571B37]/20 focus:border-[#571B37] outline-none"
            />
            {search && (
              <button
                onClick={() => setSearch('')}
                className="absolute right-3.5 top-3.5 text-[#A89C94] hover:text-[#2A0F1D] cursor-pointer"
                title="Clear search"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-[#7A6E65] whitespace-nowrap">Sort by:</span>
            <select
              value={sortBy}
              onChange={(e) => {
                setSortBy(e.target.value);
                setPage(1);
                setSectionPage(1);
              }}
              className="px-3 py-2.5 bg-[#FAF7F2] border border-[#EAE3D9] rounded-2xl text-xs font-semibold text-[#2A0F1D] outline-none cursor-pointer"
            >
              <option value="popularity">Mainstream Popularity</option>
              <option value="rating">Highest Rated</option>
              <option value="year">Publication Year</option>
              <option value="title">Title (A-Z)</option>
            </select>
          </div>
        </div>

        {/* Genre Filter Pills */}
        <div className="flex items-center gap-2 overflow-x-auto pb-1 pt-1">
          <button
            onClick={() => {
              setSelectedGenre('');
              setPage(1);
            }}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition-all cursor-pointer ${
              !selectedGenre
                ? 'bg-[#571B37] text-white shadow-xs'
                : 'bg-[#FAF7F2] border border-[#EAE3D9] text-[#695D56] hover:text-[#2A0F1D]'
            }`}
          >
            All Genres
          </button>
          {genres.map((g) => (
            <button
              key={g.name}
              onClick={() => {
                setSelectedGenre(selectedGenre === g.name ? '' : g.name);
                setPage(1);
              }}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition-all cursor-pointer flex items-center gap-1.5 ${
                selectedGenre === g.name
                  ? 'bg-[#571B37] text-white shadow-xs'
                  : 'bg-[#FAF7F2] border border-[#EAE3D9] text-[#695D56] hover:text-[#2A0F1D]'
              }`}
            >
              <span>{g.name}</span>
              <span className={`text-[10px] px-1.5 py-0.2 rounded-full ${
                selectedGenre === g.name ? 'bg-white/20 text-white' : 'bg-[#EAE3D9] text-[#7A6E65]'
              }`}>
                {g.count}
              </span>
            </button>
          ))}
        </div>

        {/* Secondary filters: Author, Year Range, Trope, Pacing */}
        <div className="flex flex-wrap items-center gap-3 pt-2 border-t border-[#EAE3D9]/60 text-xs">
          
          {/* Author filter */}
          <div className="flex items-center gap-1.5">
            <User className="w-3.5 h-3.5 text-[#7A6E65]" />
            <span className="font-semibold text-[#7A6E65]">Author:</span>
            <input
              type="text"
              value={authorFilter}
              onChange={(e) => {
                setAuthorFilter(e.target.value);
                setPage(1);
                setSectionPage(1);
              }}
              placeholder="e.g. Brandon Sanderson"
              className="px-2.5 py-1 bg-[#FAF7F2] border border-[#EAE3D9] rounded-xl text-xs text-[#2A0F1D] outline-none w-36"
            />
          </div>

          {/* Year Range */}
          <div className="flex items-center gap-1.5">
            <Calendar className="w-3.5 h-3.5 text-[#7A6E65]" />
            <span className="font-semibold text-[#7A6E65]">Years:</span>
            <input
              type="number"
              value={yearMinFilter}
              onChange={(e) => {
                setYearMinFilter(e.target.value);
                setPage(1);
              }}
              placeholder="From"
              className="px-2 py-1 bg-[#FAF7F2] border border-[#EAE3D9] rounded-xl text-xs text-[#2A0F1D] outline-none w-16"
            />
            <span className="text-[#A89C94]">-</span>
            <input
              type="number"
              value={yearMaxFilter}
              onChange={(e) => {
                setYearMaxFilter(e.target.value);
                setPage(1);
              }}
              placeholder="To"
              className="px-2 py-1 bg-[#FAF7F2] border border-[#EAE3D9] rounded-xl text-xs text-[#2A0F1D] outline-none w-16"
            />
          </div>

          {/* Trope filter */}
          <div className="flex items-center gap-1.5">
            <span className="font-semibold text-[#7A6E65]">Trope:</span>
            <select
              value={selectedTrope}
              onChange={(e) => {
                setSelectedTrope(e.target.value);
                setPage(1);
              }}
              className="px-2.5 py-1 bg-[#FAF7F2] border border-[#EAE3D9] rounded-xl text-xs text-[#2A0F1D] outline-none"
            >
              <option value="">Any Trope</option>
              {tropes.map((t) => (
                <option key={t.name} value={t.name}>{t.name} ({t.count})</option>
              ))}
            </select>
          </div>

          {/* Pacing filter */}
          <div className="flex items-center gap-1.5">
            <span className="font-semibold text-[#7A6E65]">Pacing:</span>
            <select
              value={selectedPacing}
              onChange={(e) => {
                setSelectedPacing(e.target.value);
                setPage(1);
              }}
              className="px-2.5 py-1 bg-[#FAF7F2] border border-[#EAE3D9] rounded-xl text-xs text-[#2A0F1D] outline-none"
            >
              <option value="">Any Pacing</option>
              <option value="Fast">Fast</option>
              <option value="Moderate">Moderate</option>
              <option value="Slow Burn">Slow Burn</option>
            </select>
          </div>

          {(isSearchingOrFiltering || expandedSection) && (
            <button
              onClick={resetAllFilters}
              className="ml-auto text-xs font-semibold text-[#9B2C2C] hover:underline cursor-pointer"
            >
              Clear All Filters
            </button>
          )}
        </div>

      </div>

      {/* =========================================================================
          VIEW 1: ACTIVE SEARCH & FILTER MODE
          ========================================================================= */}
      {isSearchingOrFiltering ? (
        <div className="space-y-6">
          <div className="flex items-center justify-between border-b border-[#EAE3D9] pb-3">
            <div>
              <h2 className="font-editorial text-2xl font-bold text-[#2A0F1D]">Search & Filter Results</h2>
              <p className="text-xs text-[#7A6E65]">
                {debouncedSearch ? `Showing matching results for "${debouncedSearch}"` : 'Showing filtered catalog titles'}
              </p>
            </div>
            <button
              onClick={resetAllFilters}
              className="text-xs font-bold text-[#571B37] hover:underline flex items-center gap-1"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              Back to Discovery Overview
            </button>
          </div>

          {searchLoading ? (
            <div className="p-20 text-center text-[#7A6E65] space-y-3">
              <div className="w-8 h-8 border-3 border-[#571B37] border-t-transparent rounded-full animate-spin mx-auto" />
              <p className="text-xs">
                {debouncedSearch ? 'Searching Google Books & Open Library live...' : 'Loading titles...'}
              </p>
            </div>
          ) : books.length === 0 ? (
            <div className="p-16 text-center text-[#7A6E65] bg-white rounded-3xl border border-[#EAE3D9] space-y-3">
              <BookOpen className="w-10 h-10 text-[#C48332] mx-auto opacity-70" />
              <h3 className="font-editorial text-xl font-bold text-[#2A0F1D]">No Books Found</h3>
              <p className="text-xs max-w-sm mx-auto">
                No titles matched your specific query across Google Books, Open Library, or local storage. Try broadening your keywords.
              </p>
              <button
                onClick={resetAllFilters}
                className="px-4 py-2 rounded-xl bg-[#571B37] text-white text-xs font-semibold cursor-pointer"
              >
                Reset Filters
              </button>
            </div>
          ) : (
            <div className="space-y-8">
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-5">
                {books.map((b) => (
                  <CatalogueBookCard
                    key={b.id}
                    book={b}
                    isAdded={addedIds.has(b.id)}
                    currentUser={currentUser}
                    onSelectBook={onSelectBook}
                    onQuickAdd={handleQuickAdd}
                    renderSourceChip={renderSourceChip}
                  />
                ))}
              </div>

              {/* Pagination */}
              <div className="flex items-center justify-between border-t border-[#EAE3D9] pt-6">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className={`px-4 py-2 rounded-xl text-xs font-semibold flex items-center gap-1.5 border transition-all ${
                    page === 1
                      ? 'border-[#EAE3D9] text-[#A89C94] cursor-not-allowed'
                      : 'bg-white border-[#EAE3D9] text-[#571B37] hover:bg-[#FAF7F2] cursor-pointer'
                  }`}
                >
                  <ChevronLeft className="w-4 h-4" />
                  Previous
                </button>

                <span className="text-xs font-semibold text-[#7A6E65]">
                  Page {page} {books.length === pageSize ? '' : `(${books.length} items)`}
                </span>

                <button
                  onClick={() => setPage((p) => p + 1)}
                  disabled={books.length < pageSize}
                  className={`px-4 py-2 rounded-xl text-xs font-semibold flex items-center gap-1.5 border transition-all ${
                    books.length < pageSize
                      ? 'border-[#EAE3D9] text-[#A89C94] cursor-not-allowed'
                      : 'bg-white border-[#EAE3D9] text-[#571B37] hover:bg-[#FAF7F2] cursor-pointer'
                  }`}
                >
                  Next
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}
        </div>
      ) : isViewingExpandedSection ? (

      /* =========================================================================
          VIEW 2: EXPANDED SECTION VIEW ("VIEW ALL")
          ========================================================================= */
        <div className="space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#EAE3D9] pb-4">
            <div>
              <button
                onClick={() => setExpandedSection(null)}
                className="text-xs font-bold text-[#571B37] hover:underline flex items-center gap-1.5 mb-2 cursor-pointer"
              >
                <ArrowLeft className="w-3.5 h-3.5" />
                Back to Discovery Overview
              </button>
              <h2 className="font-editorial text-3xl font-bold text-[#2A0F1D]">{expandedSection.title}</h2>
              <p className="text-xs sm:text-sm text-[#7A6E65] mt-1">{expandedSection.description}</p>
            </div>

            <div className="text-xs font-semibold px-3 py-1.5 rounded-full bg-[#FAF7F2] border border-[#EAE3D9] text-[#571B37] self-start sm:self-auto">
              Total Catalogued: {sectionTotal} titles
            </div>
          </div>

          {sectionLoading ? (
            <div className="p-20 text-center text-[#7A6E65] space-y-3">
              <div className="w-8 h-8 border-3 border-[#571B37] border-t-transparent rounded-full animate-spin mx-auto" />
              <p className="text-xs">Loading titles for {expandedSection.title}...</p>
            </div>
          ) : sectionBooks.length === 0 ? (
            <div className="p-16 text-center text-[#7A6E65] bg-white rounded-3xl border border-[#EAE3D9] space-y-3">
              <BookOpen className="w-10 h-10 text-[#C48332] mx-auto opacity-70" />
              <h3 className="font-editorial text-xl font-bold text-[#2A0F1D]">No Books in this Section</h3>
              <p className="text-xs max-w-sm mx-auto">
                No titles matching your active author or year filter were found.
              </p>
              <button
                onClick={() => {
                  setAuthorFilter('');
                  setYearMinFilter('');
                  setYearMaxFilter('');
                }}
                className="px-4 py-2 rounded-xl bg-[#571B37] text-white text-xs font-semibold cursor-pointer"
              >
                Clear Section Filters
              </button>
            </div>
          ) : (
            <div className="space-y-8">
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-5">
                {sectionBooks.map((b) => (
                  <CatalogueBookCard
                    key={b.id}
                    book={b}
                    isAdded={addedIds.has(b.id)}
                    currentUser={currentUser}
                    onSelectBook={onSelectBook}
                    onQuickAdd={handleQuickAdd}
                    renderSourceChip={renderSourceChip}
                  />
                ))}
              </div>

              {/* Pagination */}
              <div className="flex items-center justify-between border-t border-[#EAE3D9] pt-6">
                <button
                  onClick={() => setSectionPage((p) => Math.max(1, p - 1))}
                  disabled={sectionPage === 1}
                  className={`px-4 py-2 rounded-xl text-xs font-semibold flex items-center gap-1.5 border transition-all ${
                    sectionPage === 1
                      ? 'border-[#EAE3D9] text-[#A89C94] cursor-not-allowed'
                      : 'bg-white border-[#EAE3D9] text-[#571B37] hover:bg-[#FAF7F2] cursor-pointer'
                  }`}
                >
                  <ChevronLeft className="w-4 h-4" />
                  Previous
                </button>

                <span className="text-xs font-semibold text-[#7A6E65]">
                  Page {sectionPage} of {Math.max(1, Math.ceil(sectionTotal / 18))} ({sectionBooks.length} items)
                </span>

                <button
                  onClick={() => setSectionPage((p) => p + 1)}
                  disabled={sectionPage * 18 >= sectionTotal && sectionBooks.length < 18}
                  className={`px-4 py-2 rounded-xl text-xs font-semibold flex items-center gap-1.5 border transition-all ${
                    sectionPage * 18 >= sectionTotal && sectionBooks.length < 18
                      ? 'border-[#EAE3D9] text-[#A89C94] cursor-not-allowed'
                      : 'bg-white border-[#EAE3D9] text-[#571B37] hover:bg-[#FAF7F2] cursor-pointer'
                  }`}
                >
                  Next
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}
        </div>
      ) : (

      /* =========================================================================
          VIEW 3: INITIAL DISCOVERY OVERVIEW (12 SECTIONS)
          ========================================================================= */
        <div className="space-y-12">
          {discoveryLoading ? (
            <div className="p-20 text-center text-[#7A6E65] space-y-3">
              <div className="w-10 h-10 border-4 border-[#571B37] border-t-transparent rounded-full animate-spin mx-auto" />
              <h3 className="font-editorial text-2xl font-bold text-[#2A0F1D]">Loading API Discovery Catalogue...</h3>
              <p className="text-xs max-w-md mx-auto">
                Populating 12 real-time discovery sections across Google Books and Open Library.
              </p>
            </div>
          ) : discoverySections.length === 0 ? (
            <div className="p-16 text-center text-[#7A6E65] bg-white rounded-3xl border border-[#EAE3D9] space-y-3">
              <BookOpen className="w-10 h-10 text-[#C48332] mx-auto opacity-70" />
              <h3 className="font-editorial text-xl font-bold text-[#2A0F1D]">No Discovery Titles Available</h3>
              <p className="text-xs">Use the search bar above to query Google Books and Open Library directly.</p>
            </div>
          ) : (
            discoverySections.map((section) => (
              <section key={section.id} className="space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-2 border-b border-[#EAE3D9] pb-3">
                  <div>
                    <h2 className="font-editorial text-2xl font-bold text-[#2A0F1D] flex items-center gap-2">
                      {section.title}
                    </h2>
                    <p className="text-xs text-[#7A6E65] mt-0.5">{section.description}</p>
                  </div>

                  <button
                    onClick={() => {
                      setExpandedSection(section);
                      setSectionPage(1);
                    }}
                    className="text-xs font-bold text-[#571B37] hover:underline flex items-center gap-1 self-start sm:self-auto cursor-pointer"
                  >
                    View All ({section.total_available})
                    <ChevronRight className="w-3.5 h-3.5" />
                  </button>
                </div>

                {/* Section Books Grid */}
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-5">
                  {section.books.map((b) => (
                    <CatalogueBookCard
                      key={b.id}
                      book={b}
                      isAdded={addedIds.has(b.id)}
                      currentUser={currentUser}
                      onSelectBook={onSelectBook}
                      onQuickAdd={handleQuickAdd}
                      renderSourceChip={renderSourceChip}
                    />
                  ))}
                </div>
              </section>
            ))
          )}
        </div>
      )}

    </div>
  );
}

// Reusable Book Card Component for Catalogue
function CatalogueBookCard({ book, isAdded, currentUser, onSelectBook, onQuickAdd, renderSourceChip }) {
  return (
    <div
      onClick={() => onSelectBook(book.id)}
      className="group cursor-pointer bg-white rounded-2xl border border-[#EAE3D9] p-3 flex flex-col justify-between hover:shadow-xl transition-all hover:-translate-y-1 relative"
    >
      <div>
        {/* Cover image & Rating badge */}
        <div className="relative aspect-[2/3] rounded-xl overflow-hidden mb-2.5 bg-[#EAE3D9]">
          <BookCover
            src={book.cover_image}
            title={book.title}
            author={book.author}
            genre={book.genre}
            className="group-hover:scale-105"
          />
          <div className="absolute bottom-1.5 right-1.5 px-1.5 py-0.5 rounded-md bg-black/60 backdrop-blur-xs text-white text-[10px] font-bold flex items-center gap-0.5 shadow-xs">
            <Star className="w-2.5 h-2.5 fill-[#E09E4B] text-[#E09E4B]" />
            {book.average_rating || 4.0}
          </div>
        </div>

        {/* Source Provider Chip & Genre */}
        <div className="flex items-center justify-between gap-1 mb-1">
          <span className="text-[10px] font-bold uppercase tracking-wider text-[#571B37] truncate">
            {book.genre || 'Fiction'}
          </span>
          {renderSourceChip(book.source_provider)}
        </div>

        {/* Title & Author */}
        <h4 className="font-editorial font-bold text-sm text-[#2A0F1D] line-clamp-1 leading-snug group-hover:text-[#571B37] transition-colors">
          {book.title}
        </h4>
        <p className="text-[11px] text-[#7A6E65] line-clamp-1 mt-0.5">
          {book.author}
        </p>
      </div>

      {/* Card Action */}
      {currentUser && (
        <button
          type="button"
          onClick={(e) => onQuickAdd(e, book.id)}
          disabled={isAdded}
          className={`w-full mt-3 py-1 px-2 rounded-lg text-[11px] font-semibold flex items-center justify-center gap-1 transition-all cursor-pointer ${
            isAdded
              ? 'bg-[#E8EFEA] text-[#1C3829]'
              : 'bg-[#FAF7F2] hover:bg-[#571B37] hover:text-white text-[#571B37] border border-[#EAE3D9]'
          }`}
        >
          {isAdded ? (
            <>
              <Check className="w-3 h-3" />
              Added
            </>
          ) : (
            <>
              <Plus className="w-3 h-3" />
              Shelf
            </>
          )}
        </button>
      )}
    </div>
  );
}