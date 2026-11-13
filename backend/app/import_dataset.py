"""
DEARLY CSV Dataset Import & Preprocessing Service
Handles:
- Reusable CSV import with column mapping
- Data cleaning, validation, and missing value imputation
- Duplicate detection by ISBN or (title, author)
- Programmatic and CLI invocation
"""

import sys
import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple
import pandas as pd
from sqlalchemy.orm import Session

from .database import SessionLocal, engine, Base
from .models import Book
from .schemas import DatasetImportStats
from .seed_data import SEED_BOOKS

logger = logging.getLogger("dearly.importer")

COLUMN_ALIASES = {
    "title": ["title", "book_title", "original_title", "name"],
    "author": ["author", "authors", "book_author", "writer"],
    "description": ["description", "desc", "summary", "synopsis", "overview"],
    "genre": ["genre", "genres", "category", "categories", "main_genre"],
    "subgenre": ["subgenre", "sub_genre", "secondary_genre"],
    "tropes": ["tropes", "trope", "story_tropes"],
    "themes": ["themes", "theme", "subject_themes"],
    "writing_style": ["writing_style", "style", "prose_style"],
    "pacing": ["pacing", "pace"],
    "emotional_tone": ["emotional_tone", "tone", "mood"],
    "pages": ["pages", "page_count", "num_pages", "number_of_pages"],
    "publication_year": ["publication_year", "year", "pub_year", "original_publication_year"],
    "cover_image": ["cover_image", "cover", "image_url", "image", "thumbnail"],
    "isbn": ["isbn", "isbn13", "isbn10", "identifier"],
    "popularity_score": ["popularity_score", "popularity"],
    "average_rating": ["average_rating", "rating", "avg_rating"],
    "ratings_count": ["ratings_count", "ratings", "votes", "work_ratings_count"]
}

def map_column_names(df_columns: List[str]) -> Dict[str, str]:
    """Map external CSV columns to DEARLY standard fields."""
    mapping = {}
    lower_cols = {c.lower().strip(): c for c in df_columns}
    
    for standard_name, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            if alias in lower_cols:
                mapping[standard_name] = lower_cols[alias]
                break
    return mapping

def parse_list_field(val: Any) -> list:
    """Safely parse list fields from CSV (e.g. JSON array, pipe-separated, or comma-separated)."""
    if pd.isna(val) or val is None or str(val).strip() == "":
        return []
    val_str = str(val).strip()
    if val_str.startswith("[") and val_str.endswith("]"):
        try:
            return json.loads(val_str)
        except Exception:
            pass
    if "|" in val_str:
        return [x.strip() for x in val_str.split("|") if x.strip()]
    if ";" in val_str:
        return [x.strip() for x in val_str.split(";") if x.strip()]
    return [x.strip() for x in val_str.split(",") if x.strip()]

def import_books_from_csv(file_path_or_buffer, db: Session, update_duplicates: bool = True) -> DatasetImportStats:
    """Read and import books from a CSV file into the database."""
    try:
        df = pd.read_csv(file_path_or_buffer)
    except Exception as e:
        return DatasetImportStats(
            total_rows_processed=0,
            imported=0,
            updated=0,
            skipped=0,
            errors=[f"Failed to read CSV: {str(e)}"],
            total_books_in_catalog=db.query(Book).count()
        )

    col_map = map_column_names(df.columns.tolist())
    if "title" not in col_map or "author" not in col_map:
        return DatasetImportStats(
            total_rows_processed=len(df),
            imported=0,
            updated=0,
            skipped=len(df),
            errors=["CSV must contain at least 'title' and 'author' columns."],
            total_books_in_catalog=db.query(Book).count()
        )

    imported_count = 0
    updated_count = 0
    skipped_count = 0
    errors = []

    for idx, row in df.iterrows():
        try:
            title = str(row[col_map["title"]]).strip()
            author = str(row[col_map["author"]]).strip()
            if not title or pd.isna(title) or not author or pd.isna(author):
                skipped_count += 1
                continue

            isbn = str(row[col_map["isbn"]]).strip() if "isbn" in col_map and not pd.isna(row[col_map["isbn"]]) else None
            
            # Check for existing book (by ISBN or (title, author))
            existing_book = None
            if isbn:
                existing_book = db.query(Book).filter(Book.isbn == isbn).first()
            if not existing_book:
                existing_book = db.query(Book).filter(
                    Book.title.ilike(title),
                    Book.author.ilike(author)
                ).first()

            desc = str(row[col_map["description"]]).strip() if "description" in col_map and not pd.isna(row[col_map["description"]]) else ""
            genre = str(row[col_map["genre"]]).strip() if "genre" in col_map and not pd.isna(row[col_map["genre"]]) else "Fiction"
            subgenre = str(row[col_map["subgenre"]]).strip() if "subgenre" in col_map and not pd.isna(row[col_map["subgenre"]]) else None
            
            tropes = parse_list_field(row[col_map["tropes"]]) if "tropes" in col_map else []
            themes = parse_list_field(row[col_map["themes"]]) if "themes" in col_map else []
            
            style = str(row[col_map["writing_style"]]).strip() if "writing_style" in col_map and not pd.isna(row[col_map["writing_style"]]) else None
            pacing = str(row[col_map["pacing"]]).strip() if "pacing" in col_map and not pd.isna(row[col_map["pacing"]]) else None
            tone = str(row[col_map["emotional_tone"]]).strip() if "emotional_tone" in col_map and not pd.isna(row[col_map["emotional_tone"]]) else None

            # Numeric fields
            def get_int(field, default=None):
                if field in col_map and not pd.isna(row[col_map[field]]):
                    try:
                        return int(float(row[col_map[field]]))
                    except Exception:
                        return default
                return default

            def get_float(field, default=None):
                if field in col_map and not pd.isna(row[col_map[field]]):
                    try:
                        return float(row[col_map[field]])
                    except Exception:
                        return default
                return default

            pages = get_int("pages", 320)
            pub_year = get_int("publication_year", 2020)
            popularity = get_float("popularity_score", 50.0)
            avg_rating = get_float("average_rating", 4.0)
            ratings_count = get_int("ratings_count", 50)

            # Determine book length category
            length_cat = "Medium (300-450 pages)"
            if pages and pages < 300:
                length_cat = "Short (<300 pages)"
            elif pages and pages >= 450:
                length_cat = "Long (450+ pages)"

            # Legitimate cover image handling: only use if supplied as valid URL, do NOT assign random stock photos
            cover = str(row[col_map["cover_image"]]).strip() if "cover_image" in col_map and not pd.isna(row[col_map["cover_image"]]) else None
            if not cover or not cover.startswith("http"):
                cover = None

            if existing_book:
                if update_duplicates:
                    if desc:
                        existing_book.description = desc
                    existing_book.genre = genre
                    existing_book.subgenre = subgenre
                    if tropes:
                        existing_book.set_list("tropes", tropes)
                    if themes:
                        existing_book.set_list("themes", themes)
                    if style:
                        existing_book.writing_style = style
                    if pacing:
                        existing_book.pacing = pacing
                    if tone:
                        existing_book.emotional_tone = tone
                    if pages:
                        existing_book.pages = pages
                    if pub_year:
                        existing_book.publication_year = pub_year
                    if cover:
                        existing_book.cover_image = cover
                    existing_book.average_rating = avg_rating
                    existing_book.popularity_score = popularity
                    updated_count += 1
                else:
                    skipped_count += 1
            else:
                new_book = Book(
                    title=title,
                    author=author,
                    description=desc,
                    genre=genre,
                    subgenre=subgenre,
                    writing_style=style,
                    pacing=pacing,
                    emotional_tone=tone,
                    book_length_category=length_cat,
                    pages=pages,
                    publication_year=pub_year,
                    cover_image=cover,
                    isbn=isbn,
                    source_provider="csv_import",
                    popularity_score=popularity,
                    average_rating=avg_rating,
                    ratings_count=ratings_count
                )
                new_book.set_list("tropes", tropes)
                new_book.set_list("themes", themes)
                db.add(new_book)
                db.flush() # Flush to enable intra-batch duplicate detection
                imported_count += 1

        except Exception as e:
            errors.append(f"Row {idx + 1} error: {str(e)}")
            skipped_count += 1

    db.commit()
    total_in_db = db.query(Book).count()

    return DatasetImportStats(
        total_rows_processed=len(df),
        imported=imported_count,
        updated=updated_count,
        skipped=skipped_count,
        errors=errors[:10],
        total_books_in_catalog=total_in_db
    )

def seed_database_if_empty(db: Session) -> int:
    """Populate database with seed books, adding any that are missing without creating duplicates."""
    for b_data in SEED_BOOKS:
        existing = db.query(Book).filter(
            Book.title == b_data["title"],
            Book.author == b_data["author"]
        ).first()
        if not existing:
            b = Book(
                title=b_data["title"],
                author=b_data["author"],
                description=b_data.get("description", ""),
                genre=b_data.get("genre", "General"),
                subgenre=b_data.get("subgenre"),
                writing_style=b_data.get("writing_style"),
                pacing=b_data.get("pacing"),
                emotional_tone=b_data.get("emotional_tone"),
                book_length_category=b_data.get("book_length_category"),
                pages=b_data.get("pages"),
                publication_year=b_data.get("publication_year"),
                cover_image=b_data.get("cover_image"),
                isbn=b_data.get("isbn"),
                source_provider="curated_seed",
                popularity_score=b_data.get("popularity_score", 50.0),
                average_rating=b_data.get("average_rating", 4.0),
                ratings_count=b_data.get("ratings_count", 50)
            )
            b.set_list("tropes", b_data.get("tropes", []))
            b.set_list("themes", b_data.get("themes", []))
            db.add(b)

    db.commit()
    return db.query(Book).count()

if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if len(sys.argv) > 1:
            csv_path = sys.argv[1]
            print(f"Importing dataset from {csv_path}...")
            stats = import_books_from_csv(csv_path, db)
            print(f"Import complete: {stats.imported} imported, {stats.updated} updated, {stats.skipped} skipped.")
            print(f"Total books in catalog: {stats.total_books_in_catalog}")
        else:
            print("No CSV provided, checking seed database...")
            total = seed_database_if_empty(db)
            print(f"Catalogue verified with {total} books.")
    finally:
        db.close()
