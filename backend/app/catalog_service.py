"""
DEARLY Unified Book Catalog Discovery Service
Integrates Google Books API and Open Library API with:
- Metadata normalization into common internal schema
- Hierarchical deduplication (ISBN-13 -> ISBN-10 -> Normalized Title/Author)
- Preservation of genuinely distinct editions
- Rate-limit aware error handling and request timeouts (5-8s)
- Provider fallback (Google Books <-> Open Library)
- In-memory response caching (TTL: 15 minutes)
- PostgreSQL persistence and recommendation eligibility
"""

import re
import time
from datetime import datetime
import logging
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, field
import httpx
from sqlalchemy.orm import Session
from sqlalchemy import or_, func

from .config import (
    GOOGLE_BOOKS_API_KEY,
    GOOGLE_BOOKS_BASE_URL,
    OPEN_LIBRARY_BASE_URL
)
from .models import Book

logger = logging.getLogger("dearly.catalog")

# In-memory query cache: key -> (timestamp, List[NormalizedBook])
_QUERY_CACHE: Dict[str, Tuple[float, List[Dict[str, Any]]]] = {}
CACHE_TTL_SECONDS = 900  # 15 minutes
MAX_CACHE_ENTRIES = 500

# Canonical genre mapping
GENRE_KEYWORDS = {
    "fantasy": "Fantasy",
    "magic": "Fantasy",
    "sci-fi": "Science Fiction",
    "science fiction": "Science Fiction",
    "space": "Science Fiction",
    "dystopian": "Speculative Fiction",
    "speculative": "Speculative Fiction",
    "mystery": "Mystery",
    "detective": "Mystery",
    "crime": "Mystery",
    "thriller": "Mystery",
    "suspense": "Mystery",
    "romance": "Romance",
    "love": "Romance",
    "historical": "Historical Fiction",
    "history": "Historical Fiction",
    "horror": "Horror",
    "gothic": "Dark Academia",
    "dark academia": "Dark Academia",
    "literary": "Literary Fiction",
    "contemporary": "Contemporary",
    "magical realism": "Magical Realism",
    "young adult": "Young Adult",
    "juvenile": "Young Adult",
    "ya": "Young Adult",
    "nonfiction": "Non-Fiction",
    "non-fiction": "Non-Fiction",
    "biography": "Non-Fiction",
    "memoir": "Non-Fiction",
    "science": "Non-Fiction",
    "psychology": "Self-Help",
    "self-help": "Self-Help",
    "habits": "Self-Help",
    "productivity": "Self-Help",
    "personal development": "Self-Help"
}

KNOWN_TROPES = [
    "Enemies to Lovers", "Found Family", "Secret Society", "Heist Crew",
    "Unreliable Narrator", "Slow Burn", "Time Travel", "Dual Timeline",
    "Morally Grey", "Amateur Sleuths", "Cozy Low-Stakes", "Grumpy and Sunshine",
    "Parallel Universes", "Magic Academy", "Second Chances", "Chosen One",
    "Forbidden Love", "Fake Dating", "Rivals to Lovers", "Reluctant Hero"
]

KNOWN_THEMES = [
    "Obsession", "Trauma and Resilience", "Power of Stories", "Colonialism and Resistance",
    "Grief and Memory", "Friendship Beyond Romance", "Artistic Ambition",
    "Scientific Curiosity", "Aging Gracefully", "Moral Courage", "Self-Sacrifice",
    "Identity", "Belonging", "Redemption", "Corruption of Power", "Isolation"
]

def clean_isbn(raw_isbn: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    """Clean and return (isbn_10, isbn_13)."""
    if not raw_isbn:
        return None, None
    digits = re.sub(r"[^0-9Xx]", "", str(raw_isbn))
    isbn_10 = digits if len(digits) == 10 else None
    isbn_13 = digits if len(digits) == 13 else None
    return isbn_10, isbn_13

def normalize_title(title: str) -> str:
    """Normalize title for fuzzy deduplication."""
    if not title:
        return ""
    # Remove subtitles
    base = re.split(r"[:\-\–]", title)[0]
    # Remove non-alphanumeric except spaces
    cleaned = re.sub(r"[^\w\s]", "", base.lower())
    # Remove leading common articles
    cleaned = re.sub(r"^(the|a|an)\s+", "", cleaned.strip())
    return " ".join(cleaned.split())

def normalize_author(author: str) -> str:
    """Normalize author name."""
    if not author:
        return ""
    cleaned = re.sub(r"[^\w\s]", "", author.lower())
    return " ".join(cleaned.split())

def map_genre_from_categories(categories: List[str], description: str = "") -> Tuple[str, Optional[str]]:
    """Infer standard genre and subgenre from provider categories/subjects."""
    text_corpus = " ".join(categories).lower() + " " + (description[:300].lower() if description else "")
    
    matched_genre = None
    subgenre = None

    for kw, canonical in GENRE_KEYWORDS.items():
        if kw in text_corpus:
            matched_genre = canonical
            break

    if not matched_genre:
        if categories:
            first = categories[0].split("/")[0].strip()
            matched_genre = first if first else "Fiction"
        else:
            matched_genre = "Fiction"

    # Secondary genre / subgenre
    for kw, canonical in GENRE_KEYWORDS.items():
        if kw in text_corpus and canonical != matched_genre:
            subgenre = canonical
            break

    return matched_genre, subgenre

def extract_detected_narratives(text_corpus: str) -> Tuple[List[str], List[str]]:
    """Detect mentioned tropes/themes without fabricating unsupported claims."""
    lowered = text_corpus.lower()
    matched_tropes = [t for t in KNOWN_TROPES if t.lower() in lowered]
    matched_themes = [th for th in KNOWN_THEMES if th.lower() in lowered]
    return matched_tropes, matched_themes


DEFAULT_HEADERS = {
    "User-Agent": "DEARLY-BookDiscovery/2.0 (Book Recommender Platform; mailto:contact@dearly.app)",
    "Accept": "application/json"
}


class BookCatalogService:
    def __init__(self):
        self.timeout = 8.0 # 8 seconds timeout per provider request

    def _get_from_cache(self, cache_key: str) -> Optional[List[Dict[str, Any]]]:
        if cache_key in _QUERY_CACHE:
            ts, items = _QUERY_CACHE[cache_key]
            if time.time() - ts < CACHE_TTL_SECONDS and len(items) > 0:
                return items
            else:
                del _QUERY_CACHE[cache_key]
        return None

    def _set_cache(self, cache_key: str, items: List[Dict[str, Any]]):
        if not items:
            return  # Do not cache empty error results
        if len(_QUERY_CACHE) > MAX_CACHE_ENTRIES:
            oldest_key = min(_QUERY_CACHE.keys(), key=lambda k: _QUERY_CACHE[k][0])
            del _QUERY_CACHE[oldest_key]
        _QUERY_CACHE[cache_key] = (time.time(), items)

    async def fetch_google_books(
        self,
        query: str,
        limit: int = 20,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Fetch and normalize books from Google Books API."""
        clean_q = query.strip()
        clean_isbn = clean_q.replace("-", "").replace(" ", "")
        if re.match(r"^(97[89])?\d{9}[\dX]$", clean_isbn, re.IGNORECASE):
            formatted_q = f"isbn:{clean_isbn}"
        else:
            formatted_q = clean_q

        params = {
            "q": formatted_q,
            "startIndex": offset,
            "maxResults": min(limit, 40),
            "printType": "books"
        }
        if GOOGLE_BOOKS_API_KEY:
            params["key"] = GOOGLE_BOOKS_API_KEY

        url = f"{GOOGLE_BOOKS_BASE_URL}/volumes"
        books: List[Dict[str, Any]] = []

        try:
            async with httpx.AsyncClient(timeout=self.timeout, headers=DEFAULT_HEADERS) as client:
                resp = await client.get(url, params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    items = data.get("items", [])
                    for item in items:
                        v_info = item.get("volumeInfo", {})
                        norm = self._normalize_google_book(item["id"], v_info)
                        if norm:
                            books.append(norm)
                elif resp.status_code == 429:
                    logger.warning("Google Books API rate limit exceeded (HTTP 429).")
                else:
                    logger.warning(f"Google Books API returned status {resp.status_code}: {resp.text[:200]}")
        except Exception as e:
            logger.warning(f"Google Books API request failed: {e}")

        return books

    def _normalize_google_book(self, volume_id: str, v_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        title = v_info.get("title", "").strip()
        authors = v_info.get("authors", [])
        author_str = ", ".join(authors) if authors else "Unknown Author"

        if not title:
            return None

        subtitle = v_info.get("subtitle")
        full_title = f"{title}: {subtitle}" if subtitle else title

        desc = v_info.get("description", "")
        publisher = v_info.get("publisher")
        page_count = v_info.get("pageCount")
        
        # Parse publication year
        pub_date = str(v_info.get("publishedDate", ""))
        pub_year = None
        year_match = re.search(r"\b(19\d\d|20\d\d)\b", pub_date)
        if year_match:
            pub_year = int(year_match.group(1))

        # Industry identifiers (ISBN)
        isbn_10 = None
        isbn_13 = None
        for ident in v_info.get("industryIdentifiers", []):
            i_type = ident.get("type")
            i_val = ident.get("identifier")
            if i_type == "ISBN_10":
                isbn_10 = i_val
            elif i_type == "ISBN_13":
                isbn_13 = i_val

        # Legitimate cover image (force HTTPS)
        image_links = v_info.get("imageLinks", {})
        cover_url = image_links.get("thumbnail") or image_links.get("smallThumbnail")
        if cover_url:
            cover_url = cover_url.replace("http://", "https://")

        raw_categories = v_info.get("categories", [])
        genre, subgenre = map_genre_from_categories(raw_categories, desc)
        tropes, themes = extract_detected_narratives(" ".join(raw_categories) + " " + desc)

        avg_rating = float(v_info.get("averageRating", 4.0))
        ratings_cnt = int(v_info.get("ratingsCount", 50))
        info_link = v_info.get("infoLink")

        # Length category
        length_cat = "Medium (300-450 pages)"
        if page_count and page_count < 300:
            length_cat = "Short (<300 pages)"
        elif page_count and page_count >= 450:
            length_cat = "Long (450+ pages)"

        return {
            "title": full_title,
            "raw_title": title,
            "author": author_str,
            "description": desc,
            "genre": genre,
            "subgenre": subgenre,
            "tropes": tropes,
            "themes": themes,
            "writing_style": None, # Genuine provider data: not fabricated
            "pacing": None,
            "emotional_tone": None,
            "book_length_category": length_cat,
            "pages": page_count,
            "publication_year": pub_year,
            "cover_image": cover_url,
            "isbn": isbn_13 or isbn_10,
            "isbn_10": isbn_10,
            "isbn_13": isbn_13,
            "publisher": publisher,
            "categories": raw_categories,
            "source_provider": "google_books",
            "external_id": volume_id,
            "external_url": info_link,
            "retrieved_at": datetime.utcnow(),
            "popularity_score": min(95.0, max(30.0, float(ratings_cnt * 2 if ratings_cnt < 50 else 75.0))),
            "average_rating": avg_rating,
            "ratings_count": ratings_cnt
        }

    async def fetch_open_library(
        self,
        query: str,
        limit: int = 20,
        page: int = 1
    ) -> List[Dict[str, Any]]:
        """Fetch and normalize books from Open Library API."""
        clean_q = query.strip()
        clean_isbn = clean_q.replace("-", "").replace(" ", "")
        is_isbn = bool(re.match(r"^(97[89])?\d{9}[\dX]$", clean_isbn, re.IGNORECASE))

        # Explicitly request rich fields to ensure ISBN, subjects, pages, and covers are returned
        fields_str = "key,title,author_name,first_publish_year,isbn,cover_i,subject,number_of_pages_median,publisher,ratings_average,ratings_count,first_sentence"

        # Guard against Open Library search API 422 errors:
        # Open Library rejects queries < 3 characters or stopwords like 'the' with 422
        if is_isbn:
            params = {
                "isbn": clean_isbn,
                "fields": fields_str,
                "page": page,
                "limit": min(limit, 40)
            }
        elif len(clean_q) < 3 or clean_q.lower() in {"the", "a", "an", "and", "or", "of", "to", "in"}:
            return []
        else:
            params = {
                "q": clean_q,
                "fields": fields_str,
                "page": page,
                "limit": min(limit, 40)
            }

        url = f"{OPEN_LIBRARY_BASE_URL}/search.json"
        books: List[Dict[str, Any]] = []

        try:
            async with httpx.AsyncClient(timeout=self.timeout, headers=DEFAULT_HEADERS) as client:
                resp = await client.get(url, params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    docs = data.get("docs", [])
                    for doc in docs:
                        norm = self._normalize_open_library_doc(doc, searched_isbn=clean_isbn if is_isbn else None)
                        if norm:
                            books.append(norm)
                elif resp.status_code == 429:
                    logger.warning("Open Library API rate limit exceeded (HTTP 429).")
                else:
                    logger.warning(f"Open Library API returned status {resp.status_code}: {resp.text[:200]}")
        except Exception as e:
            logger.warning(f"Open Library API request failed: {e}")

        return books

    def _normalize_open_library_doc(self, doc: Dict[str, Any], searched_isbn: Optional[str] = None) -> Optional[Dict[str, Any]]:
        title = doc.get("title", "").strip()
        authors = doc.get("author_name", [])
        author_str = ", ".join(authors) if authors else "Unknown Author"

        if not title:
            return None

        # Publication year
        pub_year = doc.get("first_publish_year")
        if not pub_year and doc.get("publish_year"):
            pub_year = min(doc["publish_year"])

        # ISBN
        isbns = doc.get("isbn", [])
        isbn_10 = None
        isbn_13 = None
        for i_val in isbns:
            clean_i10, clean_i13 = clean_isbn(i_val)
            if clean_i10 and not isbn_10:
                isbn_10 = clean_i10
            if clean_i13 and not isbn_13:
                isbn_13 = clean_i13
            if isbn_10 and isbn_13:
                break

        if searched_isbn:
            if not isbn_13 and len(searched_isbn) == 13:
                isbn_13 = searched_isbn
            if not isbn_10 and len(searched_isbn) == 10:
                isbn_10 = searched_isbn

        # Legitimate cover image
        cover_id = doc.get("cover_i")
        cover_url = None
        if cover_id:
            cover_url = f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg"
        elif isbn_13 or isbn_10:
            cover_url = f"https://covers.openlibrary.org/b/isbn/{isbn_13 or isbn_10}-L.jpg"

        # Publisher & pages
        publishers = doc.get("publisher", [])
        publisher = publishers[0] if publishers else None
        pages = doc.get("number_of_pages_median")

        # Subjects / categories
        raw_subjects = doc.get("subject", [])[:10]
        first_sentence = doc.get("first_sentence")
        desc = ""
        if isinstance(first_sentence, list) and first_sentence:
            desc = first_sentence[0]
        elif isinstance(first_sentence, str):
            desc = first_sentence

        genre, subgenre = map_genre_from_categories(raw_subjects, desc)
        tropes, themes = extract_detected_narratives(" ".join(raw_subjects) + " " + desc)

        length_cat = "Medium (300-450 pages)"
        if pages and pages < 300:
            length_cat = "Short (<300 pages)"
        elif pages and pages >= 450:
            length_cat = "Long (450+ pages)"

        work_key = doc.get("key", "").replace("/works/", "")
        raw_key = doc.get("key", "")
        external_url = f"https://openlibrary.org{raw_key}" if raw_key else None

        return {
            "title": title,
            "raw_title": title,
            "author": author_str,
            "description": desc,
            "genre": genre,
            "subgenre": subgenre,
            "tropes": tropes,
            "themes": themes,
            "writing_style": None,
            "pacing": None,
            "emotional_tone": None,
            "book_length_category": length_cat,
            "pages": pages,
            "publication_year": pub_year,
            "cover_image": cover_url,
            "isbn": isbn_13 or isbn_10,
            "isbn_10": isbn_10,
            "isbn_13": isbn_13,
            "publisher": publisher,
            "categories": raw_subjects,
            "source_provider": "open_library",
            "external_id": work_key,
            "external_url": external_url,
            "retrieved_at": datetime.utcnow(),
            "popularity_score": 50.0,
            "average_rating": float(doc.get("ratings_average", 4.0)),
            "ratings_count": int(doc.get("ratings_count", 30))
        }

    def deduplicate_and_merge(
        self,
        books_a: List[Dict[str, Any]],
        books_b: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Deduplicate across providers:
        1. Exact ISBN-13 match
        2. Exact ISBN-10 match
        3. Normalized title and author match (while preserving genuinely distinct editions)
        """
        all_candidates = books_a + books_b
        merged_books: List[Dict[str, Any]] = []

        isbn13_index: Dict[str, int] = {}
        isbn10_index: Dict[str, int] = {}
        title_author_index: Dict[Tuple[str, str], List[int]] = {}

        for cand in all_candidates:
            i13 = cand.get("isbn_13")
            i10 = cand.get("isbn_10")
            norm_t = normalize_title(cand["title"])
            norm_a = normalize_author(cand["author"])

            match_idx = None

            # 1. Check ISBN-13
            if i13 and i13 in isbn13_index:
                match_idx = isbn13_index[i13]
            # 2. Check ISBN-10
            elif i10 and i10 in isbn10_index:
                match_idx = isbn10_index[i10]
            # 3. Check Normalized Title + Author
            elif (norm_t, norm_a) in title_author_index:
                for existing_idx in title_author_index[(norm_t, norm_a)]:
                    existing = merged_books[existing_idx]
                    # Check if genuinely distinct edition
                    y1 = existing.get("publication_year")
                    y2 = cand.get("publication_year")
                    is_distinct_edition = False
                    if y1 and y2 and abs(y1 - y2) >= 5:
                        is_distinct_edition = True
                    # Different subtitle format (e.g. Illustrated, Graphic Novel)
                    t1_low = existing["title"].lower()
                    t2_low = cand["title"].lower()
                    if ("illustrated" in t1_low) != ("illustrated" in t2_low):
                        is_distinct_edition = True
                    if ("graphic novel" in t1_low) != ("graphic novel" in t2_low):
                        is_distinct_edition = True

                    if not is_distinct_edition:
                        match_idx = existing_idx
                        break

            if match_idx is not None:
                # Merge into existing item
                self._merge_book_records(merged_books[match_idx], cand)
            else:
                new_idx = len(merged_books)
                merged_books.append(cand)
                if i13:
                    isbn13_index[i13] = new_idx
                if i10:
                    isbn10_index[i10] = new_idx
                if (norm_t, norm_a) not in title_author_index:
                    title_author_index[(norm_t, norm_a)] = []
                title_author_index[(norm_t, norm_a)].append(new_idx)

        return merged_books

    def _merge_book_records(self, base: Dict[str, Any], incoming: Dict[str, Any]):
        """Combine richer fields into base record."""
        # Provider marking
        base["source_provider"] = f"{base['source_provider']}+{incoming['source_provider']}"
        
        # Prefer longer/detailed description
        if not base.get("description") or (incoming.get("description") and len(incoming["description"]) > len(base["description"])):
            base["description"] = incoming["description"]

        # Legitimate cover image
        if not base.get("cover_image") and incoming.get("cover_image"):
            base["cover_image"] = incoming["cover_image"]

        # Missing ISBNs
        if not base.get("isbn_10") and incoming.get("isbn_10"):
            base["isbn_10"] = incoming["isbn_10"]
        if not base.get("isbn_13") and incoming.get("isbn_13"):
            base["isbn_13"] = incoming["isbn_13"]
        if not base.get("isbn"):
            base["isbn"] = incoming.get("isbn")

        # Missing pages or publisher
        if not base.get("pages") and incoming.get("pages"):
            base["pages"] = incoming["pages"]
        if not base.get("publisher") and incoming.get("publisher"):
            base["publisher"] = incoming["publisher"]
        if not base.get("publication_year") and incoming.get("publication_year"):
            base["publication_year"] = incoming["publication_year"]

        # External URL
        if not base.get("external_url") and incoming.get("external_url"):
            base["external_url"] = incoming["external_url"]

        # Combine categories
        cats = list(set(base.get("categories", []) + incoming.get("categories", [])))
        base["categories"] = cats

    async def search_catalog(
        self,
        query: str,
        limit: int = 24,
        offset: int = 0,
        genre: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], Dict[str, str]]:
        """
        Unified search querying Google Books and Open Library in parallel.
        Supports searching by title, author, ISBN, keyword, or genre/subject.
        Falls back gracefully if one or both providers are unavailable.
        """
        clean_q = (query or "").strip()
        effective_genre = genre.strip() if genre and genre.lower() != "all" else None

        if not clean_q and not effective_genre:
            return [], {"google_books": "skipped", "open_library": "skipped"}

        cache_key = f"q={clean_q.lower()}|g={effective_genre or ''}|l={limit}|o={offset}"
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached, {"google_books": "cached", "open_library": "cached"}

        provider_status = {"google_books": "ok", "open_library": "ok"}
        page = (offset // limit) + 1

        # Formulate query strings
        if clean_q and effective_genre:
            gb_query = f"{clean_q} subject:{effective_genre}"
            ol_query = f"{clean_q} {effective_genre}"
        elif clean_q:
            gb_query = clean_q
            ol_query = clean_q
        else: # effective_genre only
            gb_query = f"subject:{effective_genre}"
            ol_query = effective_genre

        # Parallel fetch from both providers
        gbooks_task = self.fetch_google_books(query=gb_query, limit=limit, offset=offset)
        ol_task = self.fetch_open_library(query=ol_query, limit=limit, page=page)

        import asyncio
        results = await asyncio.gather(gbooks_task, ol_task, return_exceptions=True)

        gbooks_res = results[0] if not isinstance(results[0], Exception) else []
        if isinstance(results[0], Exception):
            provider_status["google_books"] = "error"
        elif not gbooks_res:
            provider_status["google_books"] = "empty_or_limited"

        ol_res = results[1] if not isinstance(results[1], Exception) else []
        if isinstance(results[1], Exception):
            provider_status["open_library"] = "error"
        elif not ol_res:
            provider_status["open_library"] = "empty_or_limited"

        # Deduplicate and merge across both providers
        combined = self.deduplicate_and_merge(gbooks_res, ol_res)

        # Optional genre filter if specific genre requested and not already matching
        if effective_genre:
            for b in combined:
                if b.get("genre") in ["Fiction", "General", None]:
                    b["genre"] = effective_genre
            filtered = [b for b in combined if effective_genre.lower() in (b.get("genre") or "").lower() or effective_genre.lower() in " ".join(b.get("categories", [])).lower()]
            if filtered:
                combined = filtered

        # Cache valid results
        if combined:
            self._set_cache(cache_key, combined)

        return combined, provider_status

    def persist_or_get_book(self, db: Session, book_dict: Dict[str, Any]) -> Book:
        """
        Check if book already exists in PostgreSQL (by ISBN, external_id, or title+author).
        If not, create and save it so it has a real DB ID and is eligible for recommendations.
        """
        isbn = book_dict.get("isbn")
        isbn_13 = book_dict.get("isbn_13")
        isbn_10 = book_dict.get("isbn_10")
        external_id = book_dict.get("external_id")
        title = book_dict.get("title", "").strip()
        author = book_dict.get("author", "").strip()

        existing = None
        # Check by ISBN
        if isbn_13:
            existing = db.query(Book).filter(Book.isbn_13 == isbn_13).first()
        if not existing and isbn_10:
            existing = db.query(Book).filter(Book.isbn_10 == isbn_10).first()
        if not existing and isbn:
            existing = db.query(Book).filter(Book.isbn == isbn).first()
        if not existing and external_id:
            existing = db.query(Book).filter(Book.external_id == external_id).first()
        if not existing and title and author:
            existing = db.query(Book).filter(
                func.lower(Book.title) == title.lower(),
                func.lower(Book.author) == author.lower()
            ).first()

        if existing:
            # Update missing or generic attributes with richer incoming metadata
            if existing.genre in ["Fiction", "General", None] and book_dict.get("genre") not in ["Fiction", "General", None]:
                existing.genre = book_dict["genre"]
            if not existing.categories and book_dict.get("categories"):
                existing.categories = str(book_dict["categories"])
            if not existing.cover_image and book_dict.get("cover_image"):
                existing.cover_image = book_dict["cover_image"]
            if not existing.description and book_dict.get("description"):
                existing.description = book_dict["description"]
            if not existing.isbn_13 and book_dict.get("isbn_13"):
                existing.isbn_13 = book_dict["isbn_13"]
            if not existing.isbn_10 and book_dict.get("isbn_10"):
                existing.isbn_10 = book_dict["isbn_10"]
            if not existing.isbn and book_dict.get("isbn"):
                existing.isbn = book_dict["isbn"]
            if not existing.external_url and book_dict.get("external_url"):
                existing.external_url = book_dict["external_url"]
            if not existing.retrieved_at and book_dict.get("retrieved_at"):
                existing.retrieved_at = datetime.utcnow()
            db.commit()
            return existing

        # Create new Book record in PostgreSQL
        new_book = Book(
            title=title,
            author=author,
            description=book_dict.get("description", ""),
            genre=book_dict.get("genre") or "General",
            subgenre=book_dict.get("subgenre"),
            writing_style=book_dict.get("writing_style"),
            pacing=book_dict.get("pacing"),
            emotional_tone=book_dict.get("emotional_tone"),
            book_length_category=book_dict.get("book_length_category", "Medium (300-450 pages)"),
            pages=book_dict.get("pages"),
            publication_year=book_dict.get("publication_year"),
            cover_image=book_dict.get("cover_image"),
            isbn=isbn,
            isbn_10=isbn_10,
            isbn_13=isbn_13,
            publisher=book_dict.get("publisher"),
            categories=str(book_dict.get("categories", [])),
            source_provider=book_dict.get("source_provider", "api_import"),
            external_id=external_id,
            external_url=book_dict.get("external_url"),
            retrieved_at=datetime.utcnow(),
            popularity_score=book_dict.get("popularity_score", 50.0),
            average_rating=book_dict.get("average_rating", 4.0),
            ratings_count=book_dict.get("ratings_count", 50)
        )
        new_book.set_list("tropes", book_dict.get("tropes", []))
        new_book.set_list("themes", book_dict.get("themes", []))

        db.add(new_book)
        db.commit()
        db.refresh(new_book)
        return new_book

catalog_service = BookCatalogService()

