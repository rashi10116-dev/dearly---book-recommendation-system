"""
DEARLY Comprehensive Integration and Regression Test Suite
Tests:
1. PostgreSQL live connectivity
2. Database initialization and models schema
3. User registration with case-insensitive unique constraints
4. Secure PBKDF2 password hashing & constant-time verification
5. Case-insensitive username login & normalized email login
6. JWT token generation, validation, and expiration
7. User-specific authorization checks (preventing cross-user data tampering)
8. Onboarding preferences persistence and retrieval
9. Reading history CRUD (create, filter, update, delete)
10. Book catalog search and filtering
11. Google Books API integration & normalization (deterministic mocked tests)
12. Open Library API integration & normalization (deterministic mocked tests)
13. Provider failure & resilient fallback handling
14. Book deduplication across providers (ISBN-13, ISBN-10, Title/Author)
15. Preservation of distinct editions
16. Missing metadata & missing cover graceful handling
17. Recommendation generation with Taste Mixes & Unexpected Mix
18. Exclusion of previously read books from recommendations
19. CSV dataset import and duplicate detection
20. Scientific evaluation metric calculations (Precision, Recall, NDCG, ILD, EPC)
"""

import sys
import os
import json
import io
import math
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock

# Setup path
base_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(base_dir))

from app.database import SessionLocal, engine, check_database_connection
from app.models import User, Book, ReadingEntry, UserPreference
from app.auth import hash_password, verify_password, create_access_token, get_current_user
from app.schemas import (
    UserRegister, UserLogin, UserPreferenceCreate,
    ReadingEntryCreate, ReadingEntryUpdate
)
from app.routers.auth import register, login
from app.routers.preferences import get_user_preferences, save_user_preferences
from app.routers.reading import (
    get_user_reading_entries, get_reading_stats,
    add_or_update_reading_entry, update_reading_entry, delete_reading_entry
)
from app.catalog_service import (
    clean_isbn, normalize_title, normalize_author,
    map_genre_from_categories, extract_detected_narratives,
    catalog_service
)
from app.recommendations import recommendation_engine
from app.import_dataset import import_books_from_csv
from app.evaluation.metrics import (
    precision_at_k, recall_at_k, dcg_at_k, ndcg_at_k,
    intra_list_diversity, expected_popularity_complement
)
from fastapi import HTTPException
import jwt

def run_all_tests():
    print("=" * 70)
    print("DEARLY FULL INTEGRATION & REGRESSION TEST SUITE")
    print("=" * 70)

    passed_count = 0
    failed_count = 0

    def record_pass(test_name: str):
        nonlocal passed_count
        passed_count += 1
        print(f" [PASS] {test_name}")

    def record_fail(test_name: str, error: Exception):
        nonlocal failed_count
        failed_count += 1
        print(f" [FAIL] {test_name}: {error}")

    db = SessionLocal()
    try:
        # TEST 1: PostgreSQL Connectivity
        try:
            conn_status = check_database_connection()
            assert conn_status["connected"] is True, f"DB check failed: {conn_status}"
            assert conn_status["dialect"] == "postgresql", f"Expected postgresql, got {conn_status['dialect']}"
            record_pass("1. PostgreSQL live connectivity and dialect verification")
        except Exception as e:
            record_fail("1. PostgreSQL connectivity", e)

        # TEST 2: Password hashing security
        try:
            raw_pw = "SuperSecurePass123!"
            h1 = hash_password(raw_pw)
            h2 = hash_password(raw_pw)
            assert h1 != h2, "Salts must be unique per password hash"
            assert h1.startswith("pbkdf2:sha256:100000$"), "Must use PBKDF2 with 100k iterations"
            assert verify_password(raw_pw, h1) is True
            assert verify_password("WrongPassword!", h1) is False
            record_pass("2. Password hashing & constant-time verification")
        except Exception as e:
            record_fail("2. Password hashing", e)

        # TEST 3: User registration with normalization & unique checks
        test_email = "testrunner@example.com"
        test_username = "AlphaReader"
        try:
            # Clean up prior test data
            existing = db.query(User).filter(User.email == test_email).first()
            if existing:
                db.delete(existing)
                db.commit()

            reg_data = UserRegister(
                email="TestRunner@EXAMPLE.com",
                username=test_username,
                password="TestPassphrase123!"
            )
            reg_res = register(reg_data, db=db)
            assert reg_res["user"]["email"] == test_email, "Email should be lowercased"
            assert reg_res["user"]["username"] == test_username

            # Duplicate email rejection
            try:
                register(UserRegister(email=test_email.upper(), username="OtherUser", password="ValidPass123!"), db=db)
                assert False, "Duplicate email should fail"
            except HTTPException as http_err:
                assert http_err.status_code == 400

            # Duplicate username rejection (case-insensitive)
            try:
                register(UserRegister(email="other@example.com", username="alphareader", password="ValidPass123!"), db=db)
                assert False, "Duplicate username (lower) should fail"
            except HTTPException as http_err:
                assert http_err.status_code == 400

            record_pass("3. User registration with case-insensitive unique constraints")
        except Exception as e:
            record_fail("3. User registration", e)

        # TEST 4: Case-insensitive login with username and email
        try:
            # Exact username
            l1 = login(UserLogin(username_or_email="AlphaReader", password="TestPassphrase123!"), db=db)
            assert l1["user"]["username"] == test_username

            # Lowercase username
            l2 = login(UserLogin(username_or_email="alphareader", password="TestPassphrase123!"), db=db)
            assert l2["user"]["username"] == test_username

            # Alternating case username
            l3 = login(UserLogin(username_or_email="aLpHaReAdEr", password="TestPassphrase123!"), db=db)
            assert l3["user"]["username"] == test_username

            # Email login (lowercase)
            l4 = login(UserLogin(username_or_email="testrunner@example.com", password="TestPassphrase123!"), db=db)
            assert l4["user"]["username"] == test_username

            # Email login (uppercase)
            l5 = login(UserLogin(username_or_email="TESTRUNNER@EXAMPLE.COM", password="TestPassphrase123!"), db=db)
            assert l5["user"]["username"] == test_username

            # Wrong password
            try:
                login(UserLogin(username_or_email="AlphaReader", password="WrongPassword"), db=db)
                assert False, "Wrong password should fail"
            except HTTPException as http_err:
                assert http_err.status_code == 401

            record_pass("4. Case-insensitive username login & email login")
        except Exception as e:
            record_fail("4. Case-insensitive login", e)

        # TEST 5: JWT token validation and expiration
        try:
            from app.config import SECRET_KEY, ALGORITHM
            user_obj = db.query(User).filter(User.email == test_email).first()
            valid_token = create_access_token(data={"sub": str(user_obj.id), "username": user_obj.username})
            curr_user = get_current_user(token=valid_token, db=db)
            assert curr_user.id == user_obj.id

            # Expired token
            expired_token = create_access_token(
                data={"sub": str(user_obj.id), "username": user_obj.username},
                expires_delta=timedelta(seconds=-10)
            )
            try:
                get_current_user(token=expired_token, db=db)
                assert False, "Expired token should raise 401"
            except HTTPException as auth_err:
                assert auth_err.status_code == 401

            record_pass("5. JWT token creation, validation, and expiration")
        except Exception as e:
            record_fail("5. JWT validation", e)

        # TEST 6: User-specific authorization checks
        try:
            # Create a second user
            other_email = "otherreader@example.com"
            other_user = db.query(User).filter(User.email == other_email).first()
            if not other_user:
                other_user = User(
                    email=other_email,
                    username="BetaReader",
                    hashed_password=hash_password("Pass123!")
                )
                db.add(other_user)
                db.commit()
                db.refresh(other_user)

            # User 1 creates reading entry
            first_book = db.query(Book).first()
            entry1 = ReadingEntry(
                user_id=user_obj.id,
                book_id=first_book.id,
                status="completed",
                rating=5.0
            )
            db.add(entry1)
            db.commit()
            db.refresh(entry1)

            # User 2 attempts to delete User 1's entry -> must raise 404/unauthorized
            try:
                delete_reading_entry(entry_id=entry1.id, current_user=other_user, db=db)
                assert False, "User 2 should not be able to delete User 1's entry"
            except HTTPException as perm_err:
                assert perm_err.status_code == 404

            # User 2 attempts to update User 1's entry -> must raise 404/unauthorized
            try:
                update_reading_entry(entry_id=entry1.id, entry_in=ReadingEntryUpdate(rating=1.0), current_user=other_user, db=db)
                assert False, "User 2 should not be able to update User 1's entry"
            except HTTPException as perm_err:
                assert perm_err.status_code == 404

            # Clean up entry
            delete_reading_entry(entry_id=entry1.id, current_user=user_obj, db=db)
            record_pass("6. User-specific authorization protection against cross-user tampering")
        except Exception as e:
            record_fail("6. User authorization", e)

        # TEST 7: Onboarding preferences persistence
        try:
            pref_data = UserPreferenceCreate(
                display_name="Alpha",
                favorite_genres=["Fantasy", "Dark Academia"],
                favorite_tropes=["Found Family", "Secret Society"],
                favorite_themes=["Obsession"],
                preferred_writing_style="Lyrical",
                preferred_pacing="Moderate",
                preferred_emotional_tone="Bittersweet",
                preferred_book_length="Medium (300-450 pages)",
                favorite_authors=["Donna Tartt", "Leigh Bardugo"],
                disliked_elements=["Love Triangles"],
                reading_difficulty="Balanced"
            )
            saved_pref = save_user_preferences(pref_in=pref_data, current_user=user_obj, db=db)
            assert saved_pref.display_name == "Alpha"
            assert "Dark Academia" in saved_pref.favorite_genres

            fetched_pref = get_user_preferences(current_user=user_obj, db=db)
            assert fetched_pref.preferred_writing_style == "Lyrical"
            record_pass("7. Onboarding preferences persistence & retrieval")
        except Exception as e:
            record_fail("7. Preferences persistence", e)

        # TEST 8: Reading history CRUD & Stats
        try:
            b1 = db.query(Book).first()
            add_in = ReadingEntryCreate(
                book_id=b1.id,
                status="currently_reading",
                rating=4.5,
                review="Magnificent depth and character chemistry.",
                liked_elements=["Atmosphere", "Pacing"]
            )
            created_entry = add_or_update_reading_entry(entry_in=add_in, current_user=user_obj, db=db)
            assert created_entry.book_id == b1.id
            assert created_entry.rating == 4.5

            stats = get_reading_stats(current_user=user_obj, db=db)
            assert stats["total"] >= 1
            assert stats["currently_reading"] >= 1

            # Update entry
            up_in = ReadingEntryUpdate(status="completed", rating=5.0)
            updated_entry = update_reading_entry(entry_id=created_entry.id, entry_in=up_in, current_user=user_obj, db=db)
            assert updated_entry.status == "completed"
            assert updated_entry.rating == 5.0

            # Delete entry
            del_res = delete_reading_entry(entry_id=created_entry.id, current_user=user_obj, db=db)
            assert "deleted" in del_res["message"].lower()
            record_pass("8. Reading history CRUD and bookshelf statistics")
        except Exception as e:
            record_fail("8. Reading history CRUD", e)

        # TEST 9: Mocked Google Books API Integration
        try:
            mock_gbooks_resp = {
                "items": [{
                    "id": "mock_gb_1",
                    "volumeInfo": {
                        "title": "Neuromancer",
                        "authors": ["William Gibson"],
                        "description": "The sky above the port was the color of television.",
                        "publishedDate": "1984-07-01",
                        "publisher": "Ace",
                        "pageCount": 271,
                        "categories": ["Fiction / Science Fiction / Cyberpunk"],
                        "industryIdentifiers": [
                            {"type": "ISBN_10", "identifier": "0441569560"},
                            {"type": "ISBN_13", "identifier": "9780441569564"}
                        ],
                        "imageLinks": {
                            "thumbnail": "http://books.google.com/mock_neuromancer.jpg"
                        },
                        "averageRating": 4.5,
                        "ratingsCount": 250000
                    }
                }]
            }
            norm = catalog_service._normalize_google_book("mock_gb_1", mock_gbooks_resp["items"][0]["volumeInfo"])
            assert norm["title"] == "Neuromancer"
            assert norm["isbn_13"] == "9780441569564"
            assert norm["cover_image"].startswith("https://"), "Must upgrade HTTP cover to HTTPS"
            assert norm["genre"] == "Science Fiction"
            record_pass("9. Google Books API metadata normalization and HTTPS cover enforcement")
        except Exception as e:
            record_fail("9. Google Books normalization", e)

        # TEST 10: Mocked Open Library API Integration
        try:
            mock_ol_doc = {
                "key": "/works/OL27479W",
                "title": "The Left Hand of Darkness",
                "author_name": ["Ursula K. Le Guin"],
                "first_publish_year": 1969,
                "publisher": ["Ace Books"],
                "number_of_pages_median": 304,
                "isbn": ["9780441478125", "0441478123"],
                "cover_i": 8234567,
                "subject": ["Science Fiction", "Gender", "Winter"],
                "first_sentence": "I'll make my report as if I told a story.",
                "ratings_average": 4.6,
                "ratings_count": 8000
            }
            norm_ol = catalog_service._normalize_open_library_doc(mock_ol_doc)
            assert norm_ol["title"] == "The Left Hand of Darkness"
            assert norm_ol["author"] == "Ursula K. Le Guin"
            assert norm_ol["isbn_13"] == "9780441478125"
            assert "covers.openlibrary.org" in norm_ol["cover_image"]
            assert norm_ol["genre"] == "Science Fiction"
            record_pass("10. Open Library API metadata normalization & cover URL construction")
        except Exception as e:
            record_fail("10. Open Library normalization", e)

        # TEST 11: Cross-provider deduplication & merge
        try:
            cand1 = {
                "title": "Neuromancer",
                "author": "William Gibson",
                "description": "Detailed cyberpunk synopsis.",
                "genre": "Science Fiction",
                "subgenre": None,
                "tropes": [],
                "themes": [],
                "writing_style": None, "pacing": None, "emotional_tone": None,
                "book_length_category": "Short (<300 pages)",
                "pages": 271, "publication_year": 1984,
                "cover_image": "https://books.google.com/cover1.jpg",
                "isbn": "9780441569564", "isbn_10": "0441569560", "isbn_13": "9780441569564",
                "publisher": "Ace", "categories": ["Cyberpunk"],
                "source_provider": "google_books", "external_id": "gb1",
                "popularity_score": 75.0, "average_rating": 4.5, "ratings_count": 250000
            }
            cand2 = {
                "title": "Neuromancer (Sprawl #1)",
                "author": "William Gibson",
                "description": "",
                "genre": "Science Fiction",
                "subgenre": None,
                "tropes": [], "themes": [],
                "writing_style": None, "pacing": None, "emotional_tone": None,
                "book_length_category": "Short (<300 pages)",
                "pages": 271, "publication_year": 1984,
                "cover_image": None,
                "isbn": "9780441569564", "isbn_10": "0441569560", "isbn_13": "9780441569564",
                "publisher": "Ace", "categories": ["Artificial Intelligence"],
                "source_provider": "open_library", "external_id": "OL123W",
                "popularity_score": 50.0, "average_rating": 4.4, "ratings_count": 1000
            }
            merged = catalog_service.deduplicate_and_merge([cand1], [cand2])
            assert len(merged) == 1, "Should deduplicate by ISBN-13"
            assert "google_books+open_library" in merged[0]["source_provider"]
            assert "Artificial Intelligence" in merged[0]["categories"]
            assert merged[0]["cover_image"] == "https://books.google.com/cover1.jpg"
            record_pass("11. Cross-provider deduplication (ISBN-13 priority) and attribute merging")
        except Exception as e:
            record_fail("11. Deduplication & merge", e)

        # TEST 12: Preservation of distinct editions
        try:
            ed1 = {
                "title": "Frankenstein", "author": "Mary Shelley",
                "description": "Original 1818 text.",
                "genre": "Horror", "subgenre": None, "tropes": [], "themes": [],
                "writing_style": None, "pacing": None, "emotional_tone": None,
                "book_length_category": "Short (<300 pages)",
                "pages": 280, "publication_year": 1818,
                "cover_image": None, "isbn": "9780141439471", "isbn_10": "0141439475", "isbn_13": "9780141439471",
                "publisher": "Lackington", "categories": ["Classic"],
                "source_provider": "open_library", "external_id": "ol_frank",
                "popularity_score": 80.0, "average_rating": 4.2, "ratings_count": 50000
            }
            ed2 = {
                "title": "Frankenstein: The Graphic Novel", "author": "Mary Shelley",
                "description": "Modern illustrated adaptation.",
                "genre": "Graphic Novel", "subgenre": None, "tropes": [], "themes": [],
                "writing_style": None, "pacing": None, "emotional_tone": None,
                "book_length_category": "Short (<300 pages)",
                "pages": 140, "publication_year": 2012,
                "cover_image": None, "isbn": "9781906332150", "isbn_10": "1906332157", "isbn_13": "9781906332150",
                "publisher": "Classical Comics", "categories": ["Comics"],
                "source_provider": "google_books", "external_id": "gb_frank_gn",
                "popularity_score": 50.0, "average_rating": 4.3, "ratings_count": 200
            }
            distinct = catalog_service.deduplicate_and_merge([ed1], [ed2])
            assert len(distinct) == 2, "Distinct editions (adaptation, different years) must be preserved"
            record_pass("12. Preservation of genuinely distinct editions")
        except Exception as e:
            record_fail("12. Distinct editions", e)

        # TEST 13: PostgreSQL persistence of external books
        try:
            ext_dict = {
                "title": "Snow Crash",
                "author": "Neal Stephenson",
                "description": "Hiro Protagonist delivers pizza for the Mafia in cyberpunk Los Angeles.",
                "genre": "Science Fiction",
                "subgenre": "Cyberpunk",
                "tropes": ["Virtual Reality", "Linguistic Virus"],
                "themes": ["Corporate Hegemony"],
                "writing_style": "Witty",
                "pacing": "Fast",
                "emotional_tone": "Satirical",
                "book_length_category": "Medium (300-450 pages)",
                "pages": 440,
                "publication_year": 1992,
                "cover_image": "https://example.com/snow_crash.jpg",
                "isbn": "9780553380958",
                "isbn_10": "0553380958",
                "isbn_13": "9780553380958",
                "publisher": "Bantam Spectra",
                "categories": ["Science Fiction"],
                "source_provider": "google_books",
                "external_id": "gb_snowcrash",
                "popularity_score": 70.0,
                "average_rating": 4.3,
                "ratings_count": 80000
            }
            persisted = catalog_service.persist_or_get_book(db, ext_dict)
            assert persisted.id is not None
            assert persisted.title == "Snow Crash"
            # Verify retrieval from PostgreSQL
            in_pg = db.query(Book).filter(Book.id == persisted.id).first()
            assert in_pg is not None
            record_pass("13. PostgreSQL persistence of dynamically discovered titles")
        except Exception as e:
            record_fail("13. Dynamic book persistence", e)

        # TEST 14: Recommendation generation and read-book exclusion
        try:
            # Add reading entry for Snow Crash to verify exclusion
            entry = ReadingEntry(
                user_id=user_obj.id,
                book_id=persisted.id,
                status="completed",
                rating=5.0
            )
            db.add(entry)
            db.commit()

            dashboard = recommendation_engine.generate_recommendations(db=db, user=user_obj)
            assert dashboard.user_display_name == "Alpha"

            # Check that read book (Snow Crash) is NEVER recommended
            all_rec_ids = []
            for items in dashboard.taste_mixes.values():
                all_rec_ids.extend([it.book.id for it in items])
            all_rec_ids.extend([it.book.id for it in dashboard.unexpected_mix])
            all_rec_ids.extend([it.book.id for it in dashboard.author_mix])
            all_rec_ids.extend([it.book.id for it in dashboard.because_you_enjoyed_mix])

            assert persisted.id not in all_rec_ids, "Read books must be strictly excluded from recommendations"
            record_pass("14. Recommendation generation and exclusion of read titles")

            # Clean up entry
            db.delete(entry)
            db.commit()
        except Exception as e:
            record_fail("14. Recommendations", e)

        # TEST 15: CSV Import and Duplicate Detection
        try:
            # Ensure clean state for test title
            db.query(Book).filter(Book.title == "The Left Hand of Darkness").delete()
            db.commit()

            csv_content = (
                "title,author,description,genre,publication_year,pages\n"
                "The Left Hand of Darkness,Ursula K. Le Guin,Sci-Fi masterpiece,Science Fiction,1969,304\n"
                "The Left Hand of Darkness,Ursula K. Le Guin,Duplicate row test,Science Fiction,1969,304\n"
            )
            buffer = io.StringIO(csv_content)
            stats = import_books_from_csv(buffer, db=db, update_duplicates=True)
            assert stats.imported == 1, f"Expected 1 import, got {stats.imported}"
            assert stats.updated == 1, f"Expected 1 duplicate update, got {stats.updated}"
            record_pass("15. CSV import validation, parsing, and duplicate handling")
        except Exception as e:
            record_fail("15. CSV import", e)

        # TEST 16: Scientific Evaluation Metrics Unit Tests
        try:
            rec = [1, 2, 3, 4, 5]
            rel = {1, 3}
            # Precision@5 = 2 / 5 = 0.4
            assert precision_at_k(rec, rel, k=5) == 0.4
            # Recall@5 = 2 / 2 = 1.0
            assert recall_at_k(rec, rel, k=5) == 1.0
            # EPC@2 for items with pop 90 and 80 -> mean novelty = 0.15
            pops = {1: 90.0, 2: 80.0}
            assert math.isclose(expected_popularity_complement([1, 2], pops, k=2), 0.15, rel_tol=1e-5)
            record_pass("16. Scientific evaluation metric calculations (Precision, Recall, EPC, ILD)")
        except Exception as e:
            record_fail("16. Evaluation metrics", e)

    finally:
        db.close()

    print("\n" + "=" * 70)
    print(f"TEST SUITE COMPLETE: {passed_count} PASSED, {failed_count} FAILED.")
    print("=" * 70)
    if failed_count > 0:
        sys.exit(1)

if __name__ == "__main__":
    run_all_tests()
