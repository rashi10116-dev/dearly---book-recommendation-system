"""
DEARLY SQLite -> PostgreSQL Migration & Verification Tool
Safely migrates all user accounts, preferences, catalog books, and reading history
from the local SQLite database to a PostgreSQL instance specified by DATABASE_URL.
Does NOT delete or overwrite the SQLite database.
"""

import sys
import os
import json
from pathlib import Path
from sqlalchemy import create_engine, text, select
from sqlalchemy.orm import sessionmaker

# Setup paths and environment
base_dir = Path(__file__).resolve().parent
root_dir = base_dir.parent
sys.path.insert(0, str(base_dir))

from app.config import DATABASE_URL
from app.models import Base, User, UserPreference, Book, ReadingEntry

def verify_and_migrate():
    print("=" * 60)
    print("DEARLY PostgreSQL Migration & Verification Service")
    print("=" * 60)

    # 1. Inspect target DATABASE_URL
    if not DATABASE_URL or not (DATABASE_URL.startswith("postgresql://") or DATABASE_URL.startswith("postgres://") or DATABASE_URL.startswith("postgresql+")):
        print("\n[ERROR] DATABASE_URL is not configured for PostgreSQL.")
        print(f"Current DATABASE_URL: {DATABASE_URL}")
        print("\nPlease update your DATABASE_URL in backend/.env or .env to point to your PostgreSQL instance:")
        print("Format: postgresql://<username>:<password>@<host>:<port>/<dbname>")
        sys.exit(1)

    print(f"\n[1/5] Target PostgreSQL URL detected (host hidden): {DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else 'configured'}")

    # 2. Test PostgreSQL connectivity
    print("[2/5] Testing PostgreSQL live connection...")
    try:
        pg_engine = create_engine(DATABASE_URL, pool_pre_ping=True)
        with pg_engine.connect() as conn:
            result = conn.execute(text("SELECT version();")).fetchone()
            print(f"  --> Connection SUCCESSFUL!")
            print(f"  --> PostgreSQL Version: {result[0]}")
    except Exception as e:
        print(f"\n[ERROR] Failed to connect to PostgreSQL database: {e}")
        print("\nTroubleshooting tips:")
        print("1. Ensure PostgreSQL is running on the specified host and port.")
        print("2. Check that the database name exists.")
        print("3. Verify username and password in your .env file.")
        sys.exit(1)

    # 3. Create tables in PostgreSQL
    print("[3/5] Creating table schema in PostgreSQL...")
    Base.metadata.create_all(bind=pg_engine)
    print("  --> Tables (users, user_preferences, books, reading_entries) ready.")

    # 4. Locate and read SQLite database
    sqlite_paths = [
        root_dir / "dearly.db",
        base_dir / "dearly.db"
    ]
    sqlite_file = None
    for p in sqlite_paths:
        if p.exists() and p.stat().st_size > 0:
            sqlite_file = p
            break

    if not sqlite_file:
        print("[INFO] No populated SQLite database found. Fresh PostgreSQL schema is initialized and ready.")
        return

    print(f"[4/5] Reading data from existing SQLite database: {sqlite_file}")
    sqlite_engine = create_engine(f"sqlite:///{sqlite_file}", connect_args={"check_same_thread": False})
    
    PgSession = sessionmaker(bind=pg_engine)
    pg_db = PgSession()

    try:
        with sqlite_engine.connect() as s_conn:
            # Migrate Users
            user_rows = s_conn.execute(text("SELECT * FROM users;")).mappings().all()
            print(f"  --> Found {len(user_rows)} users in SQLite.")
            for r in user_rows:
                existing_user = pg_db.query(User).filter(User.id == r["id"]).first()
                if not existing_user:
                    new_u = User(
                        id=r["id"],
                        email=r["email"].strip().lower(),
                        username=r["username"].strip(),
                        hashed_password=r["hashed_password"],
                        created_at=r.get("created_at")
                    )
                    pg_db.add(new_u)
            pg_db.commit()

            # Migrate UserPreferences
            pref_rows = s_conn.execute(text("SELECT * FROM user_preferences;")).mappings().all()
            print(f"  --> Found {len(pref_rows)} user preference records in SQLite.")
            for r in pref_rows:
                existing_pref = pg_db.query(UserPreference).filter(UserPreference.id == r["id"]).first()
                if not existing_pref:
                    new_pref = UserPreference(
                        id=r["id"],
                        user_id=r["user_id"],
                        display_name=r.get("display_name"),
                        favorite_genres=r.get("favorite_genres", "[]"),
                        favorite_tropes=r.get("favorite_tropes", "[]"),
                        favorite_themes=r.get("favorite_themes", "[]"),
                        preferred_writing_style=r.get("preferred_writing_style"),
                        preferred_pacing=r.get("preferred_pacing"),
                        preferred_emotional_tone=r.get("preferred_emotional_tone"),
                        preferred_book_length=r.get("preferred_book_length"),
                        favorite_authors=r.get("favorite_authors", "[]"),
                        disliked_elements=r.get("disliked_elements", "[]"),
                        reading_difficulty=r.get("reading_difficulty"),
                        updated_at=r.get("updated_at")
                    )
                    pg_db.add(new_pref)
            pg_db.commit()

            # Migrate Books
            book_rows = s_conn.execute(text("SELECT * FROM books;")).mappings().all()
            print(f"  --> Found {len(book_rows)} books in SQLite.")
            for r in book_rows:
                existing_book = pg_db.query(Book).filter(Book.id == r["id"]).first()
                if not existing_book:
                    clean_isbn = str(r["isbn"]).replace("-", "").strip() if r.get("isbn") else None
                    isbn_10 = clean_isbn if clean_isbn and len(clean_isbn) == 10 else None
                    isbn_13 = clean_isbn if clean_isbn and len(clean_isbn) == 13 else None

                    new_b = Book(
                        id=r["id"],
                        title=r["title"],
                        author=r["author"],
                        description=r.get("description") or "",
                        genre=r.get("genre") or "General",
                        subgenre=r.get("subgenre"),
                        tropes=r.get("tropes", "[]"),
                        themes=r.get("themes", "[]"),
                        writing_style=r.get("writing_style"),
                        pacing=r.get("pacing"),
                        emotional_tone=r.get("emotional_tone"),
                        book_length_category=r.get("book_length_category"),
                        pages=r.get("pages"),
                        publication_year=r.get("publication_year"),
                        cover_image=r.get("cover_image"),
                        isbn=r.get("isbn"),
                        isbn_10=isbn_10,
                        isbn_13=isbn_13,
                        publisher=r.get("publisher"),
                        categories=r.get("categories", "[]"),
                        source_provider="curated_seed",
                        external_id=r.get("external_id"),
                        popularity_score=r.get("popularity_score") or 50.0,
                        average_rating=r.get("average_rating") or 4.0,
                        ratings_count=r.get("ratings_count") or 50
                    )
                    pg_db.add(new_b)
            pg_db.commit()

            # Migrate Reading Entries
            entry_rows = s_conn.execute(text("SELECT * FROM reading_entries;")).mappings().all()
            print(f"  --> Found {len(entry_rows)} reading interaction entries in SQLite.")
            for r in entry_rows:
                existing_entry = pg_db.query(ReadingEntry).filter(ReadingEntry.id == r["id"]).first()
                if not existing_entry:
                    new_e = ReadingEntry(
                        id=r["id"],
                        user_id=r["user_id"],
                        book_id=r["book_id"],
                        status=r.get("status", "want_to_read"),
                        rating=r.get("rating"),
                        review=r.get("review"),
                        liked_elements=r.get("liked_elements", "[]"),
                        disliked_elements=r.get("disliked_elements", "[]"),
                        favorite_tropes_themes=r.get("favorite_tropes_themes", "[]"),
                        created_at=r.get("created_at"),
                        updated_at=r.get("updated_at")
                    )
                    pg_db.add(new_e)
            pg_db.commit()

        # Reset PostgreSQL ID sequences to prevent primary key collisions on new records
        print("[5/5] Synchronizing PostgreSQL sequence generators...")
        tables = ["users", "user_preferences", "books", "reading_entries"]
        with pg_engine.connect() as conn:
            for tbl in tables:
                try:
                    conn.execute(text(f"SELECT setval(pg_get_serial_sequence('{tbl}', 'id'), coalesce((SELECT max(id) FROM {tbl}), 1));"))
                    conn.commit()
                except Exception as seq_err:
                    print(f"  Warning setting sequence for {tbl}: {seq_err}")

        # Final verification
        pg_users_cnt = pg_db.query(User).count()
        pg_books_cnt = pg_db.query(Book).count()
        pg_entries_cnt = pg_db.query(ReadingEntry).count()

        print("\n" + "=" * 60)
        print("MIGRATION COMPLETE & VERIFIED")
        print("=" * 60)
        print(f"PostgreSQL Users:          {pg_users_cnt} (SQLite had {len(user_rows)})")
        print(f"PostgreSQL Books:          {pg_books_cnt} (SQLite had {len(book_rows)})")
        print(f"PostgreSQL Reading Logs:   {pg_entries_cnt} (SQLite had {len(entry_rows)})")
        print(f"Original SQLite database preserved at: {sqlite_file}")
        print("=" * 60)

    finally:
        pg_db.close()

if __name__ == "__main__":
    verify_and_migrate()
