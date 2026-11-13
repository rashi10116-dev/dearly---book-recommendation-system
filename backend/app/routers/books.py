from typing import List, Optional, Dict, Any
import asyncio
from fastapi import APIRouter, Depends, HTTPException, Query, Header
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, asc, func
import jwt

from ..database import get_db
from ..models import Book, ReadingEntry, User
from ..schemas import BookOut, BookDetailOut, DiscoverySectionOut, DiscoveryCatalogueOut
from ..config import SECRET_KEY, ALGORITHM
from ..recommendations import book_to_schema, recommendation_engine
from ..catalog_service import catalog_service

router = APIRouter(prefix="/books", tags=["Books"])

def get_optional_user_id(authorization: Optional[str] = Header(None)) -> Optional[int]:
    """Extract user_id from Authorization header if present, without failing."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return int(payload.get("sub"))
    except Exception:
        return None

@router.get("", response_model=List[BookOut])
async def list_books(
    q: Optional[str] = Query(None, description="Search term for title, author, or keyword"),
    genre: Optional[str] = Query(None, description="Filter by genre"),
    trope: Optional[str] = Query(None, description="Filter by trope tag"),
    pacing: Optional[str] = Query(None, description="Filter by pacing"),
    tone: Optional[str] = Query(None, description="Filter by emotional tone"),
    author: Optional[str] = Query(None, description="Filter by author"),
    year_min: Optional[int] = Query(None, description="Minimum publication year"),
    year_max: Optional[int] = Query(None, description="Maximum publication year"),
    sort_by: Optional[str] = Query("popularity", description="Sort by: popularity, rating, year, title"),
    limit: int = Query(24, ge=1, le=100),
    offset: int = Query(0, ge=0),
    use_live_api: bool = Query(True, description="Query Google Books & Open Library when searching"),
    db: Session = Depends(get_db)
):
    """
    Search and browse books.
    When a search query 'q' is given and 'use_live_api' is True, searches Google Books
    and Open Library in real-time, persists retrieved titles into PostgreSQL, and incorporates them.
    If APIs fail or are disabled, seamlessly falls back to local database search.
    """
    # Sanitize query parameters (handles direct python invocation where defaults are Query objects)
    clean_q = q.strip() if isinstance(q, str) and q.strip() else ""
    clean_genre = genre.strip() if isinstance(genre, str) and genre.strip() and genre.lower() != "all" else None
    clean_trope = trope.strip() if isinstance(trope, str) and trope.strip() else None
    clean_pacing = pacing.strip() if isinstance(pacing, str) and pacing.strip() else None
    clean_tone = tone.strip() if isinstance(tone, str) and tone.strip() else None
    clean_author = author.strip() if isinstance(author, str) and author.strip() else None
    clean_sort = sort_by.strip() if isinstance(sort_by, str) and sort_by.strip() else "popularity"

    # Check if we should invoke live discovery
    should_search_live = use_live_api and (
        (clean_q and len(clean_q) >= 2) or
        (clean_genre and db.query(Book).filter(Book.genre.ilike(f"%{clean_genre}%")).count() < offset + limit) or
        (not clean_q and not clean_genre and db.query(Book).count() < offset + limit)
    )

    if should_search_live:
        try:
            discovery_query = clean_q if clean_q else ("fiction" if not clean_genre else "")
            external_books, provider_status = await catalog_service.search_catalog(
                query=discovery_query,
                limit=limit,
                offset=offset,
                genre=clean_genre
            )
            if external_books:
                persisted_books = []
                for b_data in external_books:
                    saved_book = catalog_service.persist_or_get_book(db, b_data)
                    persisted_books.append(saved_book)
                
                # Make newly retrieved books immediately eligible for recommendations
                all_catalog = db.query(Book).all()
                recommendation_engine.fit_catalog(all_catalog)

                if clean_q:
                    return [book_to_schema(b) for b in persisted_books]
        except Exception as api_err:
            # Graceful fallback to local DB search
            pass

    # Local database search and filtering (includes all newly persisted books)
    query = db.query(Book)

    if clean_q:
        search_filter = f"%{clean_q}%"
        query = query.filter(
            or_(
                Book.title.ilike(search_filter),
                Book.author.ilike(search_filter),
                Book.description.ilike(search_filter),
                Book.genre.ilike(search_filter),
                Book.isbn.ilike(search_filter),
                Book.isbn_10.ilike(search_filter),
                Book.isbn_13.ilike(search_filter)
            )
        )

    if clean_genre:
        query = query.filter(Book.genre.ilike(f"%{clean_genre}%"))

    if clean_author:
        query = query.filter(Book.author.ilike(f"%{clean_author}%"))

    if year_min:
        query = query.filter(Book.publication_year >= year_min)

    if year_max:
        query = query.filter(Book.publication_year <= year_max)

    if clean_trope:
        query = query.filter(Book.tropes.ilike(f"%{clean_trope}%"))

    if clean_pacing:
        query = query.filter(Book.pacing.ilike(f"%{clean_pacing}%"))

    if clean_tone:
        query = query.filter(Book.emotional_tone.ilike(f"%{clean_tone}%"))

    # Sorting
    if clean_sort == "rating":
        query = query.order_by(desc(Book.average_rating))
    elif clean_sort == "year":
        query = query.order_by(desc(Book.publication_year))
    elif clean_sort == "title":
        query = query.order_by(asc(Book.title))
    else:  # popularity default
        query = query.order_by(desc(Book.popularity_score))
        query = query.order_by(desc(Book.popularity_score))

    books = query.offset(offset).limit(limit).all()
    return [book_to_schema(b) for b in books]

@router.get("/live-search")
async def live_search_catalog(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(20, ge=1, le=40),
    offset: int = Query(0, ge=0),
    genre: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Direct live search against Google Books and Open Library with provider health status,
    deduplication, and automatic persistence.
    """
    external_books, provider_status = await catalog_service.search_catalog(
        query=q.strip(),
        limit=limit,
        offset=offset,
        genre=genre
    )

    persisted_results = []
    for b_data in external_books:
        saved = catalog_service.persist_or_get_book(db, b_data)
        persisted_results.append(book_to_schema(saved))

    return {
        "query": q,
        "total_results": len(persisted_results),
        "provider_status": provider_status,
        "books": persisted_results
    }

DISCOVERY_SECTIONS = [
    {
        "id": "trending",
        "title": "Popular & Trending",
        "description": "Widely read and highly celebrated titles across the literary world.",
        "search_query": "bestseller popular fiction",
        "genre": None,
        "sort_by": "popularity"
    },
    {
        "id": "romance",
        "title": "Romance",
        "description": "Heartfelt journeys, emotional depth, and captivating chemistry.",
        "search_query": "romance love story contemporary romance",
        "genre": "Romance",
        "sort_by": "popularity"
    },
    {
        "id": "fantasy",
        "title": "Fantasy",
        "description": "Mythical realms, epic adventures, and immersive worldbuilding.",
        "search_query": "fantasy magic epic adventure",
        "genre": "Fantasy",
        "sort_by": "popularity"
    },
    {
        "id": "mystery",
        "title": "Mystery & Thriller",
        "description": "Gripping suspense, psychological puzzles, and investigative twists.",
        "search_query": "mystery thriller detective crime suspense",
        "genre": "Mystery",
        "sort_by": "popularity"
    },
    {
        "id": "scifi",
        "title": "Science Fiction",
        "description": "Futuristic concepts, space exploration, and speculative technology.",
        "search_query": "science fiction space galaxy cyberpunk",
        "genre": "Science Fiction",
        "sort_by": "popularity"
    },
    {
        "id": "literary",
        "title": "Literary Fiction",
        "description": "Character-driven narratives with profound prose and emotional nuance.",
        "search_query": "literary fiction novel acclaimed award",
        "genre": "Literary Fiction",
        "sort_by": "rating"
    },
    {
        "id": "historical",
        "title": "Historical Fiction",
        "description": "Vivid tales steeped in historical epochs, drama, and change.",
        "search_query": "historical fiction history drama novel",
        "genre": "Historical Fiction",
        "sort_by": "popularity"
    },
    {
        "id": "contemporary",
        "title": "Contemporary Fiction",
        "description": "Modern stories exploring real-life relationships, identity, and choices.",
        "search_query": "contemporary fiction modern life",
        "genre": "Contemporary",
        "sort_by": "popularity"
    },
    {
        "id": "young_adult",
        "title": "Young Adult",
        "description": "Coming-of-age journeys, high stakes, and unforgettable journeys.",
        "search_query": "young adult novel YA fiction",
        "genre": "Young Adult",
        "sort_by": "popularity"
    },
    {
        "id": "nonfiction",
        "title": "Non-Fiction",
        "description": "Insightful real-world accounts, biography, science, and history.",
        "search_query": "nonfiction biography memoir history science",
        "genre": "Non-Fiction",
        "sort_by": "rating"
    },
    {
        "id": "personal_dev",
        "title": "Personal Development",
        "description": "Mindset, habits, productivity, and philosophy for living well.",
        "search_query": "personal development self-help psychology habits",
        "genre": "Self-Help",
        "sort_by": "popularity"
    },
    {
        "id": "recent",
        "title": "Recently Published",
        "description": "New releases and fresh publications from recent years.",
        "search_query": "fiction novel 2024 2025",
        "genre": None,
        "year_min": 2023,
        "sort_by": "year"
    }
]

def query_section_books(
    db: Session,
    sec: Dict[str, Any],
    limit: int = 12,
    offset: int = 0,
    exclude_ids: Optional[set] = None,
    author: Optional[str] = None,
    year_min: Optional[int] = None,
    year_max: Optional[int] = None,
    sort_by: Optional[str] = None
) -> Tuple[List[Book], int]:
    q = db.query(Book)
    genre = sec.get("genre")
    if genre:
        q = q.filter(Book.genre.ilike(f"%{genre}%"))
    if sec.get("year_min"):
        q = q.filter(Book.publication_year >= sec["year_min"])
    if author:
        q = q.filter(Book.author.ilike(f"%{author.strip()}%"))
    if year_min:
        q = q.filter(Book.publication_year >= year_min)
    if year_max:
        q = q.filter(Book.publication_year <= year_max)
    if exclude_ids:
        q = q.filter(~Book.id.in_(exclude_ids))

    effective_sort = sort_by or sec.get("sort_by", "popularity")
    if effective_sort == "rating":
        q = q.order_by(desc(Book.average_rating), desc(Book.popularity_score))
    elif effective_sort == "year":
        q = q.order_by(desc(Book.publication_year), desc(Book.average_rating))
    elif effective_sort == "title":
        q = q.order_by(asc(Book.title))
    else:
        q = q.order_by(desc(Book.popularity_score), desc(Book.average_rating))

    total = q.count()
    books = q.offset(offset).limit(limit).all()
    return books, total

@router.get("/discovery", response_model=DiscoveryCatalogueOut)
async def get_discovery_catalogue(db: Session = Depends(get_db)):
    """
    Returns populated discovery sections (approx. 12 books per section) immediately upon loading
    Catalogue, without requiring any search query.
    If any section has fewer than 12 books in PostgreSQL, fetches in parallel from Google Books & Open Library,
    persists them, and returns fresh books. Avoids duplicating the same book across adjacent sections.
    """
    # 1. Identify sections that need discovery enrichment
    sections_needing_fetch = []
    for sec in DISCOVERY_SECTIONS:
        _, cnt = query_section_books(db, sec, limit=1)
        if cnt < 14:
            sections_needing_fetch.append(sec)

    # 2. Parallel API queries for sections needing books
    if sections_needing_fetch:
        fetch_tasks = [
            catalog_service.search_catalog(
                query=sec["search_query"],
                limit=18,
                offset=0,
                genre=sec["genre"]
            )
            for sec in sections_needing_fetch[:6]  # Batch up to 6 sections at once to avoid timeouts
        ]
        results = await asyncio.gather(*fetch_tasks, return_exceptions=True)

        new_books_persisted = False
        for res in results:
            if isinstance(res, tuple) and res[0]:
                for b_dict in res[0]:
                    try:
                        catalog_service.persist_or_get_book(db, b_dict)
                        new_books_persisted = True
                    except Exception:
                        db.rollback()

        if new_books_persisted:
            all_b = db.query(Book).all()
            recommendation_engine.fit_catalog(all_b, force=True)

    # 3. Assemble populated sections, avoiding duplicate books across adjacent sections
    used_ids: set = set()
    sections_out: List[DiscoverySectionOut] = []

    for sec in DISCOVERY_SECTIONS:
        books, total_cnt = query_section_books(db, sec, limit=12, offset=0, exclude_ids=used_ids)
        # If excluding used IDs caused too few books, fill up with any books from this section
        if len(books) < 8:
            books, total_cnt = query_section_books(db, sec, limit=12, offset=0)
        
        for b in books:
            used_ids.add(b.id)

        sections_out.append(DiscoverySectionOut(
            id=sec["id"],
            title=sec["title"],
            description=sec["description"],
            books=[book_to_schema(b) for b in books],
            total_available=total_cnt
        ))

    return DiscoveryCatalogueOut(
        sections=sections_out,
        total_sections=len(sections_out)
    )

@router.get("/discovery/{section_id}", response_model=DiscoverySectionOut)
async def get_discovery_section(
    section_id: str,
    page: int = Query(1, ge=1),
    limit: int = Query(12, ge=1, le=50),
    sort_by: Optional[str] = Query(None),
    author: Optional[str] = Query(None),
    year_min: Optional[int] = Query(None),
    year_max: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Paginated 'View All' or 'Load More' endpoint for any specific discovery section.
    Supports filtering by author, publication year range, and sorting.
    """
    sec = next((s for s in DISCOVERY_SECTIONS if s["id"] == section_id), None)
    if not sec:
        raise HTTPException(status_code=404, detail=f"Discovery section '{section_id}' not found.")

    offset = (page - 1) * limit
    books, total_cnt = query_section_books(
        db, sec, limit=limit, offset=offset,
        author=author, year_min=year_min, year_max=year_max, sort_by=sort_by
    )

    # If user is paginating beyond existing cached items and not doing a strict local filter,
    # dynamically fetch next page from APIs and persist
    if len(books) < limit and not author and not year_min and not year_max:
        try:
            external_books, _ = await catalog_service.search_catalog(
                query=sec["search_query"],
                limit=limit,
                offset=offset,
                genre=sec["genre"]
            )
            if external_books:
                for b_dict in external_books:
                    try:
                        catalog_service.persist_or_get_book(db, b_dict)
                    except Exception:
                        db.rollback()
                books, total_cnt = query_section_books(
                    db, sec, limit=limit, offset=offset,
                    author=author, year_min=year_min, year_max=year_max, sort_by=sort_by
                )
        except Exception:
            pass

    return DiscoverySectionOut(
        id=sec["id"],
        title=sec["title"],
        description=sec["description"],
        books=[book_to_schema(b) for b in books],
        total_available=total_cnt
    )

@router.get("/genres")
def get_genres(db: Session = Depends(get_db)):
    books = db.query(Book.genre).all()
    counts = {}
    for (g,) in books:
        if g:
            counts[g] = counts.get(g, 0) + 1
    sorted_genres = sorted([{"name": k, "count": v} for k, v in counts.items()], key=lambda x: x["count"], reverse=True)
    return sorted_genres

@router.get("/tropes")
def get_tropes(db: Session = Depends(get_db)):
    books = db.query(Book).all()
    counts = {}
    for b in books:
        for t in b.get_list("tropes"):
            counts[t] = counts.get(t, 0) + 1
    sorted_tropes = sorted([{"name": k, "count": v} for k, v in counts.items()], key=lambda x: x["count"], reverse=True)
    return sorted_tropes[:25]

@router.get("/{book_id}", response_model=BookDetailOut)
def get_book_details(
    book_id: int,
    user_id: Optional[int] = Depends(get_optional_user_id),
    db: Session = Depends(get_db)
):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found.")

    user_status = None
    user_rating = None
    user_review = None

    if user_id:
        entry = db.query(ReadingEntry).filter(
            ReadingEntry.user_id == user_id,
            ReadingEntry.book_id == book_id
        ).first()
        if entry:
            user_status = entry.status
            user_rating = entry.rating
            user_review = entry.review

    # Find 4 similar books
    similar = db.query(Book).filter(
        Book.id != book.id,
        or_(
            Book.genre == book.genre,
            Book.author == book.author
        )
    ).limit(4).all()

    book_out = book_to_schema(book)
    return BookDetailOut(
        **book_out.dict(),
        user_status=user_status,
        user_rating=user_rating,
        user_review=user_review,
        similar_books=[book_to_schema(sb) for sb in similar]
    )
