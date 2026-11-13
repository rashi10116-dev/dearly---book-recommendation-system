from datetime import datetime
import json
from sqlalchemy import (
    Column, Integer, String, Text, Float, DateTime, ForeignKey, UniqueConstraint, Index
)
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    preference = relationship("UserPreference", back_populates="user", uselist=False, cascade="all, delete-orphan")
    reading_entries = relationship("ReadingEntry", back_populates="user", cascade="all, delete-orphan")


class UserPreference(Base):
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    display_name = Column(String(100), nullable=True)
    
    # Store list of genres as JSON string
    favorite_genres = Column(Text, default="[]")
    favorite_tropes = Column(Text, default="[]")
    favorite_themes = Column(Text, default="[]")
    preferred_writing_style = Column(String(100), nullable=True)
    preferred_pacing = Column(String(50), nullable=True)
    preferred_emotional_tone = Column(String(50), nullable=True)
    preferred_book_length = Column(String(50), nullable=True)
    favorite_authors = Column(Text, default="[]")
    disliked_elements = Column(Text, default="[]")
    reading_difficulty = Column(String(50), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="preference")

    def get_list(self, field_name: str) -> list:
        val = getattr(self, field_name, None)
        if not val:
            return []
        try:
            return json.loads(val)
        except Exception:
            return [x.strip() for x in val.split(",") if x.strip()]

    def set_list(self, field_name: str, values: list):
        setattr(self, field_name, json.dumps(values or []))


class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), index=True, nullable=False)
    author = Column(String(255), index=True, nullable=False)
    description = Column(Text, nullable=True, default="")
    genre = Column(String(100), index=True, nullable=True, default="General")
    subgenre = Column(String(100), nullable=True)
    tropes = Column(Text, default="[]")
    themes = Column(Text, default="[]")
    writing_style = Column(String(100), nullable=True)
    pacing = Column(String(50), nullable=True)
    emotional_tone = Column(String(50), nullable=True)
    book_length_category = Column(String(50), nullable=True)
    pages = Column(Integer, nullable=True)
    publication_year = Column(Integer, nullable=True)
    cover_image = Column(String(500), nullable=True)
    isbn = Column(String(50), index=True, nullable=True)
    isbn_10 = Column(String(20), index=True, nullable=True)
    isbn_13 = Column(String(20), index=True, nullable=True)
    publisher = Column(String(255), nullable=True)
    categories = Column(Text, default="[]")
    source_provider = Column(String(50), nullable=True, index=True) # google_books, open_library, curated, csv
    external_id = Column(String(100), index=True, nullable=True)
    external_url = Column(String(500), nullable=True)
    retrieved_at = Column(DateTime, default=datetime.utcnow)
    popularity_score = Column(Float, default=50.0) # 0 - 100
    average_rating = Column(Float, default=4.0)
    ratings_count = Column(Integer, default=50)

    reading_entries = relationship("ReadingEntry", back_populates="book", cascade="all, delete-orphan")

    def get_list(self, field_name: str) -> list:
        val = getattr(self, field_name, None)
        if not val:
            return []
        try:
            return json.loads(val)
        except Exception:
            return [x.strip() for x in val.split(",") if x.strip()]

    def set_list(self, field_name: str, values: list):
        setattr(self, field_name, json.dumps(values or []))


class ReadingEntry(Base):
    __tablename__ = "reading_entries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    book_id = Column(Integer, ForeignKey("books.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Statuses: 'want_to_read', 'currently_reading', 'completed', 'abandoned'
    status = Column(String(50), nullable=False, default="want_to_read")
    rating = Column(Float, nullable=True) # 1.0 to 5.0
    review = Column(Text, nullable=True)
    liked_elements = Column(Text, default="[]")
    disliked_elements = Column(Text, default="[]")
    favorite_tropes_themes = Column(Text, default="[]")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="reading_entries")
    book = relationship("Book", back_populates="reading_entries")

    __table_args__ = (
        UniqueConstraint("user_id", "book_id", name="uq_user_book_reading"),
    )

    def get_list(self, field_name: str) -> list:
        val = getattr(self, field_name, None)
        if not val:
            return []
        try:
            return json.loads(val)
        except Exception:
            return [x.strip() for x in val.split(",") if x.strip()]

    def set_list(self, field_name: str, values: list):
        setattr(self, field_name, json.dumps(values or []))
