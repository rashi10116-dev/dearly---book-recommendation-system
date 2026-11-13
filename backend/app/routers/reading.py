from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from ..database import get_db
from ..models import User, Book, ReadingEntry
from ..schemas import ReadingEntryCreate, ReadingEntryUpdate, ReadingEntryOut
from ..auth import get_current_user
from ..recommendations import book_to_schema

router = APIRouter(prefix="/reading", tags=["Reading History"])

def entry_to_schema(entry: ReadingEntry) -> ReadingEntryOut:
    return ReadingEntryOut(
        id=entry.id,
        user_id=entry.user_id,
        book_id=entry.book_id,
        status=entry.status,
        rating=entry.rating,
        review=entry.review,
        liked_elements=entry.get_list("liked_elements"),
        disliked_elements=entry.get_list("disliked_elements"),
        favorite_tropes_themes=entry.get_list("favorite_tropes_themes"),
        created_at=entry.created_at,
        updated_at=entry.updated_at,
        book=book_to_schema(entry.book)
    )

@router.get("", response_model=List[ReadingEntryOut])
def get_user_reading_entries(
    status: Optional[str] = Query(None, description="Filter by status: want_to_read, currently_reading, completed, abandoned"),
    genre: Optional[str] = Query(None, description="Filter by book genre"),
    rating: Optional[float] = Query(None, description="Filter by minimum rating"),
    q: Optional[str] = Query(None, description="Search in book title or author"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(ReadingEntry).join(Book).filter(ReadingEntry.user_id == current_user.id)

    if status and status.lower() != "all":
        query = query.filter(ReadingEntry.status == status.lower())

    if genre and genre.lower() != "all":
        query = query.filter(Book.genre.ilike(f"%{genre.strip()}%"))

    if rating:
        query = query.filter(ReadingEntry.rating >= rating)

    if q:
        search_filter = f"%{q.strip()}%"
        query = query.filter(
            (Book.title.ilike(search_filter)) | (Book.author.ilike(search_filter))
        )

    entries = query.order_by(desc(ReadingEntry.updated_at)).all()
    return [entry_to_schema(e) for e in entries]

@router.get("/stats")
def get_reading_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    entries = db.query(ReadingEntry).filter(ReadingEntry.user_id == current_user.id).all()
    
    total = len(entries)
    completed = sum(1 for e in entries if e.status == "completed")
    currently_reading = sum(1 for e in entries if e.status == "currently_reading")
    want_to_read = sum(1 for e in entries if e.status == "want_to_read")
    abandoned = sum(1 for e in entries if e.status == "abandoned")

    ratings = [e.rating for e in entries if e.rating is not None]
    avg_rating = round(sum(ratings) / len(ratings), 2) if ratings else 0.0

    return {
        "total": total,
        "completed": completed,
        "currently_reading": currently_reading,
        "want_to_read": want_to_read,
        "abandoned": abandoned,
        "average_rating": avg_rating,
        "total_rated": len(ratings)
    }

@router.post("", response_model=ReadingEntryOut)
def add_or_update_reading_entry(
    entry_in: ReadingEntryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    book = db.query(Book).filter(Book.id == entry_in.book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found.")

    # Check for existing entry to prevent duplicates
    entry = db.query(ReadingEntry).filter(
        ReadingEntry.user_id == current_user.id,
        ReadingEntry.book_id == entry_in.book_id
    ).first()

    if not entry:
        entry = ReadingEntry(
            user_id=current_user.id,
            book_id=entry_in.book_id
        )
        db.add(entry)

    entry.status = entry_in.status
    entry.rating = entry_in.rating
    entry.review = entry_in.review
    entry.set_list("liked_elements", entry_in.liked_elements)
    entry.set_list("disliked_elements", entry_in.disliked_elements)
    entry.set_list("favorite_tropes_themes", entry_in.favorite_tropes_themes)
    entry.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(entry)
    return entry_to_schema(entry)

@router.put("/{entry_id}", response_model=ReadingEntryOut)
def update_reading_entry(
    entry_id: int,
    entry_in: ReadingEntryUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    entry = db.query(ReadingEntry).filter(
        ReadingEntry.id == entry_id,
        ReadingEntry.user_id == current_user.id
    ).first()

    if not entry:
        raise HTTPException(status_code=404, detail="Reading entry not found or unauthorized.")

    if entry_in.status is not None:
        entry.status = entry_in.status
    if entry_in.rating is not None:
        entry.rating = entry_in.rating
    if entry_in.review is not None:
        entry.review = entry_in.review
    if entry_in.liked_elements is not None:
        entry.set_list("liked_elements", entry_in.liked_elements)
    if entry_in.disliked_elements is not None:
        entry.set_list("disliked_elements", entry_in.disliked_elements)
    if entry_in.favorite_tropes_themes is not None:
        entry.set_list("favorite_tropes_themes", entry_in.favorite_tropes_themes)
    
    entry.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(entry)
    return entry_to_schema(entry)

@router.delete("/{entry_id}")
def delete_reading_entry(
    entry_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    entry = db.query(ReadingEntry).filter(
        ReadingEntry.id == entry_id,
        ReadingEntry.user_id == current_user.id
    ).first()

    if not entry:
        raise HTTPException(status_code=404, detail="Reading entry not found or unauthorized.")

    db.delete(entry)
    db.commit()
    return {"message": "Reading entry successfully deleted."}
