"""
DEARLY Recommendation Engine
Implements:
1. Content-Based Filtering with TF-IDF Vectorization & Cosine Similarity
2. Dynamic Reader Taste Profile Vector (Onboarding preferences + positive/negative reading feedback)
3. Multi-Signal Explainable Scoring
4. Diversity-Aware Reranking using Maximal Marginal Relevance (MMR)
5. Anti-Popularity / Serendipity Discovery ("Your Unexpected Next Read")
6. Author Recommender ("From Authors You've Read" for authors with >= 2 read books)
7. Item-to-Item Story DNA Similarity ("Because You Enjoyed...")
8. Cold-start handling with transparent, honest content-based explanations
"""

import json
import logging
from typing import List, Dict, Tuple, Optional, Set, Any
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.orm import Session
from sqlalchemy import or_

from .models import Book, User, UserPreference, ReadingEntry
from .schemas import RecommendationItem, RecommendationDashboardOut, BookOut

logger = logging.getLogger("dearly.recommendations")

def build_book_feature_text(book: Book) -> str:
    """
    Build a comprehensive text representation of a book for TF-IDF vectorization.
    Combines title, author, genre, subgenre, narrative tropes/themes, provider categories,
    and description. Handles missing or sparse attributes gracefully without failing.
    """
    tropes = " ".join(book.get_list("tropes") * 2)  # Boost narrative tropes
    themes = " ".join(book.get_list("themes") * 2)  # Boost thematic elements
    raw_cats = " ".join(book.get_list("categories")) if hasattr(book, "categories") and book.categories else ""
    
    parts = [
        book.title or "",
        book.author or "",
        book.genre or "General",
        book.subgenre or "",
        tropes,
        themes,
        raw_cats,
        f"style_{book.writing_style}" if book.writing_style else "",
        f"pacing_{book.pacing}" if book.pacing else "",
        f"tone_{book.emotional_tone}" if book.emotional_tone else "",
        book.description or ""
    ]
    return " ".join([p for p in parts if p]).lower()

def book_to_schema(book: Book) -> BookOut:
    return BookOut(
        id=book.id,
        title=book.title,
        author=book.author,
        description=book.description or "",
        genre=book.genre or "General",
        subgenre=book.subgenre,
        tropes=book.get_list("tropes"),
        themes=book.get_list("themes"),
        writing_style=book.writing_style,
        pacing=book.pacing,
        emotional_tone=book.emotional_tone,
        book_length_category=book.book_length_category or "Medium (300-450 pages)",
        pages=book.pages,
        publication_year=book.publication_year,
        cover_image=book.cover_image,
        isbn=book.isbn,
        isbn_10=getattr(book, "isbn_10", None),
        isbn_13=getattr(book, "isbn_13", None),
        publisher=getattr(book, "publisher", None),
        categories=book.get_list("categories") if hasattr(book, "categories") else [],
        source_provider=getattr(book, "source_provider", "curated_seed"),
        external_id=getattr(book, "external_id", None),
        external_url=getattr(book, "external_url", None),
        retrieved_at=getattr(book, "retrieved_at", None),
        popularity_score=book.popularity_score or 50.0,
        average_rating=book.average_rating or 4.0,
        ratings_count=book.ratings_count or 50
    )

class RecommendationEngine:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            stop_words="english",
            max_features=5000,
            sublinear_tf=True
        )
        self.book_ids: List[int] = []
        self.tfidf_matrix = None
        self.is_fitted = False
        self._cached_catalog_ids: List[int] = []

    def fit_catalog(self, books: List[Book], force: bool = False):
        """
        Fit TF-IDF on available books in the catalog.
        Caches feature matrix to prevent repeated full-catalog vectorization
        unless catalog items have actually changed.
        """
        if not books:
            self.is_fitted = False
            self.book_ids = []
            self.tfidf_matrix = None
            self._cached_catalog_ids = []
            return

        current_ids = [b.id for b in books]
        if not force and self.is_fitted and self._cached_catalog_ids == current_ids:
            # Reusing already-fitted TF-IDF matrix
            return

        self.book_ids = current_ids
        self._cached_catalog_ids = list(current_ids)
        corpus = [build_book_feature_text(b) for b in books]
        self.tfidf_matrix = self.vectorizer.fit_transform(corpus)
        self.is_fitted = True
        logger.info(f"Fitted recommendation TF-IDF matrix on {len(books)} books.")

    def calculate_mmr(
        self,
        candidate_indices: List[int],
        similarity_scores: np.ndarray,
        doc_vectors,
        top_k: int = 6,
        lambda_param: float = 0.7
    ) -> List[int]:
        """
        Maximal Marginal Relevance (MMR) for diversity-aware reranking.
        Balances user profile relevance against intra-list pairwise similarity.
        """
        if not candidate_indices or top_k <= 0:
            return []
        
        selected_indices = [candidate_indices[0]]
        remaining_indices = list(candidate_indices[1:])

        while len(selected_indices) < min(top_k, len(candidate_indices)):
            best_score = -float("inf")
            best_idx = None

            for cand_idx in remaining_indices:
                cand_sim_to_user = similarity_scores[cand_idx]
                
                # Compute maximum similarity to any already selected book
                cand_vec = doc_vectors[cand_idx]
                selected_vecs = doc_vectors[selected_indices]
                intra_sim = cosine_similarity(cand_vec, selected_vecs).max()

                mmr_val = lambda_param * cand_sim_to_user - (1 - lambda_param) * intra_sim
                if mmr_val > best_score:
                    best_score = mmr_val
                    best_idx = cand_idx

            if best_idx is not None:
                selected_indices.append(best_idx)
                remaining_indices.remove(best_idx)
            else:
                break

        return selected_indices

    async def ensure_candidates_async(self, db: Session, user: User):
        """
        Dynamically discover candidates via Google Books & Open Library
        if local candidate pools are insufficient for user's favorite genres,
        cross-genre serendipity, or authors.
        Persists newly discovered books into PostgreSQL and refits models.
        """
        from .catalog_service import catalog_service
        preference = user.preference
        fav_genres = preference.get_list("favorite_genres") if preference else []
        top_genres = fav_genres[:3] if fav_genres else ["Fantasy", "Literary Fiction", "Science Fiction"]

        genres_to_fetch = []
        for g in top_genres:
            cnt = db.query(Book).filter(Book.genre.ilike(f"%{g}%")).count()
            if cnt < 16:
                genres_to_fetch.append(g)

        # Check outside genres for Unexpected, Explore New Genres, and Hidden Gems
        user_genre_set = {g.lower() for g in top_genres}
        outside_cnt = db.query(Book).filter(
            ~or_(*[Book.genre.ilike(f"%{g}%") for g in top_genres])
        ).count()
        if outside_cnt < 24:
            for extra_g in ["Romance", "Mystery", "Historical Fiction", "Young Adult", "Non-Fiction"]:
                if extra_g.lower() not in user_genre_set and extra_g not in genres_to_fetch:
                    genres_to_fetch.append(extra_g)

        if not genres_to_fetch:
            return

        import asyncio
        fetch_tasks = [
            catalog_service.search_catalog(query="", limit=16, genre=g)
            for g in genres_to_fetch[:4]  # Batch to keep latency low (<3s)
        ]
        results = await asyncio.gather(*fetch_tasks, return_exceptions=True)

        new_persisted = False
        for res in results:
            if isinstance(res, tuple) and res[0]:
                for b_dict in res[0]:
                    try:
                        catalog_service.persist_or_get_book(db, b_dict)
                        new_persisted = True
                    except Exception:
                        db.rollback()

        if new_persisted:
            all_b = db.query(Book).all()
            self.fit_catalog(all_b, force=True)

    async def generate_recommendations_async(
        self,
        db: Session,
        user: User
    ) -> RecommendationDashboardOut:
        await self.ensure_candidates_async(db, user)
        return self.generate_recommendations(db, user)

    def generate_recommendations(
        self,
        db: Session,
        user: User
    ) -> RecommendationDashboardOut:
        all_books = db.query(Book).all()
        if not all_books:
            return RecommendationDashboardOut(
                user_display_name=user.username,
                has_reading_history=False,
                total_read_books=0,
                taste_mixes={},
                unexpected_mix=[],
                author_mix=[],
                because_you_enjoyed_mix=[],
                discovery_summary="Catalog is currently empty. Please search for books or import a dataset."
            )

        # Ensure model is fitted (reuses cached matrix if catalog hasn't changed)
        self.fit_catalog(all_books)
        book_id_to_idx = {bid: idx for idx, bid in enumerate(self.book_ids)}
        book_id_to_book = {b.id: b for b in all_books}

        # Fetch user preferences
        preference = user.preference
        display_name = preference.display_name if preference and preference.display_name else user.username
        fav_genres = preference.get_list("favorite_genres") if preference else []
        fav_tropes = set(preference.get_list("favorite_tropes")) if preference else set()
        fav_themes = set(preference.get_list("favorite_themes")) if preference else set()
        disliked = set(preference.get_list("disliked_elements")) if preference else set()
        style_pref = preference.preferred_writing_style if preference else None
        pacing_pref = preference.preferred_pacing if preference else None
        tone_pref = preference.preferred_emotional_tone if preference else None

        # Fetch user reading history
        reading_entries = db.query(ReadingEntry).filter(ReadingEntry.user_id == user.id).all()
        read_book_ids: Set[int] = {e.book_id for e in reading_entries}
        has_history = len(reading_entries) > 0

        # Build User Taste Vector
        # 1. Base query from preferences
        user_query_parts = []
        if fav_genres:
            user_query_parts.extend(fav_genres * 3)
        if fav_tropes:
            user_query_parts.extend(list(fav_tropes) * 2)
        if fav_themes:
            user_query_parts.extend(list(fav_themes) * 2)
        if style_pref:
            user_query_parts.append(f"style_{style_pref}")
        if pacing_pref:
            user_query_parts.append(f"pacing_{pacing_pref}")
        if tone_pref:
            user_query_parts.append(f"tone_{tone_pref}")
        
        user_query_text = " ".join(user_query_parts).lower()
        if user_query_text:
            user_vec = self.vectorizer.transform([user_query_text]).toarray()[0]
        else:
            user_vec = np.zeros(self.tfidf_matrix.shape[1])

        # 2. Adjust with Reading Feedback & Ratings
        # Positive books (rating >= 4 or completed) pull taste vector closer
        # Negative books (rating <= 2 or abandoned) push taste vector away
        for entry in reading_entries:
            if entry.book_id in book_id_to_idx:
                idx = book_id_to_idx[entry.book_id]
                book_vec = self.tfidf_matrix[idx].toarray()[0]
                
                weight = 0.0
                if entry.rating:
                    if entry.rating >= 4.5:
                        weight = 1.6
                    elif entry.rating >= 4.0:
                        weight = 1.0
                    elif entry.rating <= 2.0:
                        weight = -1.2
                    elif entry.rating < 3.0:
                        weight = -0.5
                elif entry.status == "completed":
                    weight = 0.8
                elif entry.status == "abandoned":
                    weight = -0.8

                user_vec += weight * book_vec

                # Add liked elements from review
                liked = entry.get_list("liked_elements")
                if liked:
                    liked_vec = self.vectorizer.transform([" ".join(liked)]).toarray()[0]
                    user_vec += 0.5 * liked_vec

                # Subtract disliked elements from review
                entry_disliked = entry.get_list("disliked_elements")
                if entry_disliked:
                    disliked.update(entry_disliked)

        # Normalize user vector
        norm = np.linalg.norm(user_vec)
        if norm > 0:
            user_vec = user_vec / norm

        # Compute raw cosine similarity for all books
        user_vec_2d = user_vec.reshape(1, -1)
        sim_scores = cosine_similarity(user_vec_2d, self.tfidf_matrix)[0]

        # Calculate explainable score and rationale for each candidate book
        scored_candidates = []
        for idx, book in enumerate(all_books):
            if book.id in read_book_ids:
                continue

            base_sim = float(sim_scores[idx])
            book_tropes = set(book.get_list("tropes"))
            book_themes = set(book.get_list("themes"))

            # Check overlap
            matched_tropes = list(book_tropes.intersection(fav_tropes))
            matched_themes = list(book_themes.intersection(fav_themes))
            matched_signals = []

            multiplier = 1.0
            if matched_tropes:
                multiplier += 0.15 * len(matched_tropes)
                matched_signals.append(f"Tropes: {', '.join(matched_tropes[:2])}")
            if matched_themes:
                multiplier += 0.10 * len(matched_themes)
                matched_signals.append(f"Themes: {', '.join(matched_themes[:2])}")
            if style_pref and book.writing_style == style_pref:
                multiplier += 0.12
                matched_signals.append(f"{book.writing_style} writing style")
            if pacing_pref and book.pacing == pacing_pref:
                multiplier += 0.08
                matched_signals.append(f"{book.pacing} pacing")
            if tone_pref and book.emotional_tone == tone_pref:
                multiplier += 0.10
                matched_signals.append(f"{book.emotional_tone} tone")

            # Penalty for disliked elements
            matched_disliked = list((book_tropes | book_themes | {book.genre or ''}).intersection(disliked))
            if matched_disliked:
                multiplier *= 0.4

            final_score = float(base_sim * multiplier)
            affinity_score = round(final_score, 4)

            scored_candidates.append({
                "index": idx,
                "book": book,
                "score": final_score,
                "affinity_score": affinity_score,
                "matched_signals": matched_signals,
                "matched_tropes": matched_tropes,
                "matched_themes": matched_themes
            })

        # --- COLLECTION A: "Your Taste" ---
        top_genres = fav_genres[:3] if fav_genres else ["Fantasy", "Literary Fiction", "Science Fiction"]
        taste_mixes: Dict[str, List[RecommendationItem]] = {}
        global_used_book_ids: Set[int] = set()
        k_per_genre = max(4, 12 // max(1, len(top_genres)))

        for g in top_genres:
            genre_candidates = [
                c for c in scored_candidates
                if (c["book"].genre or "").lower() == g.lower() and c["book"].id not in global_used_book_ids
            ]
            genre_candidates.sort(key=lambda x: x["score"], reverse=True)
            
            if genre_candidates:
                candidate_indices = [c["index"] for c in genre_candidates]
                selected_indices = self.calculate_mmr(
                    candidate_indices=candidate_indices,
                    similarity_scores=sim_scores,
                    doc_vectors=self.tfidf_matrix,
                    top_k=k_per_genre,
                    lambda_param=0.75
                )

                items = []
                for s_idx in selected_indices:
                    cand = next(c for c in genre_candidates if c["index"] == s_idx)
                    b = cand["book"]
                    global_used_book_ids.add(b.id)

                    signals_str = ", ".join(cand["matched_signals"]) if cand["matched_signals"] else f"Matches your preferred {g} aesthetic"
                    rationale = f"Ranked for your taste in {g} — aligns with {signals_str}."

                    items.append(RecommendationItem(
                        book=book_to_schema(b),
                        match_score=cand["affinity_score"],
                        collection_name=f"Your Taste: {g}",
                        rationale=rationale,
                        matched_signals=cand["matched_signals"],
                        is_unexpected=False
                    ))
                taste_mixes[g] = items

        # --- COLLECTION B: "Your Unexpected Next Read" ---
        user_genre_set = {g.lower() for g in top_genres}
        unexpected_candidates = [
            c for c in scored_candidates
            if (c["book"].genre or "").lower() not in user_genre_set and c["book"].id not in global_used_book_ids
        ]

        for cand in unexpected_candidates:
            b = cand["book"]
            pop = b.popularity_score or 50.0
            novelty_multiplier = 1.0 + max(0.0, (70.0 - pop) / 100.0)
            cand["unexpected_score"] = cand["score"] * novelty_multiplier

        unexpected_candidates.sort(key=lambda x: x.get("unexpected_score", 0), reverse=True)
        unexpected_items = []
        for cand in unexpected_candidates[:12]:
            b = cand["book"]
            global_used_book_ids.add(b.id)
            
            reasons = []
            if cand["matched_tropes"]:
                reasons.append(f"shares your affinity for '{cand['matched_tropes'][0]}'")
            if cand["matched_themes"]:
                reasons.append(f"explores '{cand['matched_themes'][0]}'")
            if b.emotional_tone and tone_pref and b.emotional_tone == tone_pref:
                reasons.append(f"matches your desired {b.emotional_tone.lower()} tone")
            
            why_text = f" and {reasons[1]}" if len(reasons) > 1 else ""
            primary_reason = reasons[0] if reasons else "carries narrative textures resonant with your reading taste"

            rationale = (
                f"Outside your typical {', '.join(top_genres[:2])} shelf, this {b.genre or 'work'} {primary_reason}{why_text}. "
                f"Selected as an unexpected discovery."
            )

            novelty_note = "Hidden Gem: Lower mainstream circulation" if (b.popularity_score or 50) < 65 else "Cross-Genre Discovery"

            unexpected_items.append(RecommendationItem(
                book=book_to_schema(b),
                match_score=round(cand.get("unexpected_score", cand["affinity_score"]), 4),
                collection_name="Your Unexpected Next Read",
                rationale=rationale,
                matched_signals=cand["matched_signals"],
                is_unexpected=True,
                novelty_note=novelty_note
            ))

        # --- COLLECTION C: "From Authors You've Read" ---
        author_read_counts: Dict[str, int] = {}
        for entry in reading_entries:
            b = book_id_to_book.get(entry.book_id)
            if b and b.author:
                author_read_counts[b.author] = author_read_counts.get(b.author, 0) + 1

        qualified_authors = [auth for auth, count in author_read_counts.items() if count >= 2]
        author_items = []

        if qualified_authors:
            for auth in qualified_authors:
                other_books = [
                    b for b in all_books
                    if b.author.lower() == auth.lower()
                    and b.id not in read_book_ids
                    and b.id not in global_used_book_ids
                ]
                for ob in other_books:
                    global_used_book_ids.add(ob.id)
                    ob_idx = book_id_to_idx.get(ob.id, 0)
                    auth_score = round(float(sim_scores[ob_idx]), 4) if ob_idx < len(sim_scores) else 0.5
                    author_items.append(RecommendationItem(
                        book=book_to_schema(ob),
                        match_score=auth_score,
                        collection_name="From Authors You've Read",
                        rationale=f"Because you've completed {author_read_counts[auth]} books by {auth}. Discover another title from their catalog.",
                        matched_signals=[f"{author_read_counts[auth]} books read by {auth}"],
                        is_unexpected=False
                    ))
                    if len(author_items) >= 12:
                        break
                if len(author_items) >= 12:
                    break
        else:
            fav_authors = preference.get_list("favorite_authors") if preference else []
            for auth in fav_authors:
                fav_author_books = [
                    b for b in all_books
                    if b.author.lower() == auth.lower()
                    and b.id not in read_book_ids
                    and b.id not in global_used_book_ids
                ]
                for ob in fav_author_books:
                    global_used_book_ids.add(ob.id)
                    ob_idx = book_id_to_idx.get(ob.id, 0)
                    auth_score = round(float(sim_scores[ob_idx]), 4) if ob_idx < len(sim_scores) else 0.5
                    author_items.append(RecommendationItem(
                        book=book_to_schema(ob),
                        match_score=auth_score,
                        collection_name="From Authors You've Read",
                        rationale=f"From your favorite author {auth} (read 2 books to unlock dedicated reading history mix).",
                        matched_signals=[f"Favorite author: {auth}"],
                        is_unexpected=False
                    ))
                    if len(author_items) >= 12:
                        break
                if len(author_items) >= 12:
                    break

        # --- COLLECTION D: "Because You Enjoyed..." ---
        anchor_book = None
        anchor_entry = None
        because_you_enjoyed_items = []

        positive_entries = [e for e in reading_entries if (e.rating and e.rating >= 4.0) or e.status == "completed"]
        positive_entries.sort(key=lambda x: (x.rating or 3.5), reverse=True)

        if positive_entries:
            anchor_entry = positive_entries[0]
            anchor_book = book_id_to_book.get(anchor_entry.book_id)

        if anchor_book and anchor_book.id in book_id_to_idx:
            anchor_idx = book_id_to_idx[anchor_book.id]
            anchor_vec = self.tfidf_matrix[anchor_idx]
            anchor_sims = cosine_similarity(anchor_vec, self.tfidf_matrix)[0]

            item_candidates = []
            for idx, b in enumerate(all_books):
                if b.id in read_book_ids or b.id in global_used_book_ids:
                    continue
                item_candidates.append({
                    "book": b,
                    "sim": float(anchor_sims[idx]),
                    "index": idx
                })

            item_candidates.sort(key=lambda x: x["sim"], reverse=True)
            for c in item_candidates[:12]:
                b = c["book"]
                global_used_book_ids.add(b.id)
                
                shared_tropes = set(b.get_list("tropes")).intersection(set(anchor_book.get_list("tropes")))
                shared_trope_str = f"such as '{list(shared_tropes)[0]}'" if shared_tropes else "shared narrative style"

                rationale = (
                    f"Recommended because you loved '{anchor_book.title}' "
                    f"({anchor_entry.rating or 5}/5 stars) — shares key story DNA {shared_trope_str} and {b.writing_style or 'rich'} storytelling."
                )

                because_you_enjoyed_items.append(RecommendationItem(
                    book=book_to_schema(b),
                    match_score=round(float(c["sim"]), 4),
                    collection_name=f"Because You Enjoyed '{anchor_book.title}'",
                    rationale=rationale,
                    matched_signals=[f"Similar to {anchor_book.title}"],
                    is_unexpected=False
                ))

        # --- COLLECTION E: "Explore New Genres" ---
        explore_candidates = [
            c for c in scored_candidates
            if (c["book"].genre or "").lower() not in user_genre_set and c["book"].id not in global_used_book_ids
        ]
        # Rank by combination of rating quality and thematic appeal
        explore_candidates.sort(
            key=lambda x: (x["book"].average_rating or 4.0) * 0.7 + (x["score"] * 10) * 0.3,
            reverse=True
        )
        explore_items = []
        for cand in explore_candidates[:12]:
            b = cand["book"]
            global_used_book_ids.add(b.id)
            g_name = b.genre or "Cross-Genre"
            rationale = (
                f"Venturing beyond your familiar genres into {g_name} — "
                f"celebrated with an average rating of {b.average_rating or 4.0}/5 stars."
            )
            explore_items.append(RecommendationItem(
                book=book_to_schema(b),
                match_score=cand["affinity_score"],
                collection_name=f"Explore New Genres: {g_name}",
                rationale=rationale,
                matched_signals=[f"Top-rated {g_name}", f"Rating: {b.average_rating or 4.0}/5"],
                is_unexpected=True,
                novelty_note="Genre Expansion"
            ))

        # --- COLLECTION F: "Hidden Gems" ---
        gem_candidates = [
            c for c in scored_candidates
            if (c["book"].popularity_score or 50.0) < 65.0
            and (c["book"].average_rating or 4.0) >= 4.0
            and c["book"].id not in global_used_book_ids
        ]
        gem_candidates.sort(key=lambda x: (x["book"].average_rating or 4.0), reverse=True)
        hidden_gems_items = []
        for cand in gem_candidates[:12]:
            b = cand["book"]
            global_used_book_ids.add(b.id)
            rationale = (
                f"Lesser-circulated discovery in {b.genre or 'Fiction'} with high critical appreciation "
                f"({b.average_rating or 4.2}/5 stars) and nuanced narrative depth."
            )
            hidden_gems_items.append(RecommendationItem(
                book=book_to_schema(b),
                match_score=cand["affinity_score"],
                collection_name="Hidden Gems",
                rationale=rationale,
                matched_signals=[f"Rating: {b.average_rating or 4.2}/5", "Understated circulation"],
                is_unexpected=True,
                novelty_note="Hidden Circulation • High Rating"
            ))

        total_recs = (
            sum(len(items) for items in taste_mixes.values())
            + len(unexpected_items)
            + len(author_items)
            + len(because_you_enjoyed_items)
            + len(explore_items)
            + len(hidden_gems_items)
        )
        if has_history:
            history_note = f"Synthesizing your taste profile across {len(reading_entries)} logged books and onboarding preferences."
        else:
            history_note = "Generated from your initial onboarding taste profile. Start logging and rating books in My Reading to adapt your mixes!"

        return RecommendationDashboardOut(
            user_display_name=display_name,
            has_reading_history=has_history,
            total_read_books=len(reading_entries),
            taste_mixes=taste_mixes,
            unexpected_mix=unexpected_items,
            author_mix=author_items,
            because_you_enjoyed_mix=because_you_enjoyed_items,
            explore_genres_mix=explore_items,
            hidden_gems_mix=hidden_gems_items,
            anchor_book_title=anchor_book.title if anchor_book else None,
            discovery_summary=f"Found {total_recs} personalized discoveries. {history_note}"
        )

# Global singleton
recommendation_engine = RecommendationEngine()
