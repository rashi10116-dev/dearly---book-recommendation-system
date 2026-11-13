from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, EmailStr, Field

# --- AUTH SCHEMAS ---

class UserRegister(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)

class UserLogin(BaseModel):
    username_or_email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    user_id: Optional[int] = None
    username: Optional[str] = None

class UserOut(BaseModel):
    id: int
    email: str
    username: str
    created_at: datetime
    has_preferences: bool = False
    display_name: Optional[str] = None

    class Config:
        from_attributes = True


# --- PREFERENCE SCHEMAS ---

class UserPreferenceBase(BaseModel):
    display_name: Optional[str] = None
    favorite_genres: List[str] = Field(default_factory=list)
    favorite_tropes: List[str] = Field(default_factory=list)
    favorite_themes: List[str] = Field(default_factory=list)
    preferred_writing_style: Optional[str] = None
    preferred_pacing: Optional[str] = None
    preferred_emotional_tone: Optional[str] = None
    preferred_book_length: Optional[str] = None
    favorite_authors: List[str] = Field(default_factory=list)
    disliked_elements: List[str] = Field(default_factory=list)
    reading_difficulty: Optional[str] = None

class UserPreferenceCreate(UserPreferenceBase):
    pass

class UserPreferenceUpdate(UserPreferenceBase):
    pass

class UserPreferenceOut(UserPreferenceBase):
    id: int
    user_id: int
    updated_at: datetime

    class Config:
        from_attributes = True


# --- BOOK SCHEMAS ---

class BookBase(BaseModel):
    title: str
    author: str
    description: Optional[str] = ""
    genre: Optional[str] = "General"
    subgenre: Optional[str] = None
    tropes: List[str] = Field(default_factory=list)
    themes: List[str] = Field(default_factory=list)
    writing_style: Optional[str] = None
    pacing: Optional[str] = None
    emotional_tone: Optional[str] = None
    book_length_category: Optional[str] = None
    pages: Optional[int] = None
    publication_year: Optional[int] = None
    cover_image: Optional[str] = None
    isbn: Optional[str] = None
    isbn_10: Optional[str] = None
    isbn_13: Optional[str] = None
    publisher: Optional[str] = None
    categories: List[str] = Field(default_factory=list)
    source_provider: Optional[str] = None
    external_id: Optional[str] = None
    external_url: Optional[str] = None
    retrieved_at: Optional[datetime] = None
    popularity_score: Optional[float] = 50.0
    average_rating: Optional[float] = 4.0
    ratings_count: Optional[int] = 50

class BookCreate(BookBase):
    pass

class BookOut(BookBase):
    id: int

    class Config:
        from_attributes = True

class BookDetailOut(BookOut):
    user_status: Optional[str] = None
    user_rating: Optional[float] = None
    user_review: Optional[str] = None
    similar_books: List[BookOut] = Field(default_factory=list)


# --- READING ENTRY SCHEMAS ---

class ReadingEntryCreate(BaseModel):
    book_id: int
    status: str = Field(..., pattern="^(want_to_read|currently_reading|completed|abandoned)$")
    rating: Optional[float] = Field(None, ge=1.0, le=5.0)
    review: Optional[str] = None
    liked_elements: List[str] = Field(default_factory=list)
    disliked_elements: List[str] = Field(default_factory=list)
    favorite_tropes_themes: List[str] = Field(default_factory=list)

class ReadingEntryUpdate(BaseModel):
    status: Optional[str] = Field(None, pattern="^(want_to_read|currently_reading|completed|abandoned)$")
    rating: Optional[float] = Field(None, ge=1.0, le=5.0)
    review: Optional[str] = None
    liked_elements: Optional[List[str]] = None
    disliked_elements: Optional[List[str]] = None
    favorite_tropes_themes: Optional[List[str]] = None

class ReadingEntryOut(BaseModel):
    id: int
    user_id: int
    book_id: int
    status: str
    rating: Optional[float] = None
    review: Optional[str] = None
    liked_elements: List[str] = Field(default_factory=list)
    disliked_elements: List[str] = Field(default_factory=list)
    favorite_tropes_themes: List[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    book: BookOut

    class Config:
        from_attributes = True


# --- RECOMMENDATION SCHEMAS ---

class RecommendationItem(BaseModel):
    book: BookOut
    match_score: float # 0 to 100 percentage
    collection_name: str
    rationale: str
    matched_signals: List[str] = Field(default_factory=list)
    is_unexpected: bool = False
    novelty_note: Optional[str] = None

class RecommendationDashboardOut(BaseModel):
    user_display_name: str
    has_reading_history: bool
    total_read_books: int
    taste_mixes: Dict[str, List[RecommendationItem]] # genre -> items
    unexpected_mix: List[RecommendationItem] = Field(default_factory=list)
    author_mix: List[RecommendationItem] = Field(default_factory=list)
    because_you_enjoyed_mix: List[RecommendationItem] = Field(default_factory=list)
    explore_genres_mix: List[RecommendationItem] = Field(default_factory=list)
    hidden_gems_mix: List[RecommendationItem] = Field(default_factory=list)
    anchor_book_title: Optional[str] = None
    discovery_summary: str


# --- DISCOVERY CATALOGUE SCHEMAS ---

class DiscoverySectionOut(BaseModel):
    id: str
    title: str
    description: str
    books: List[BookOut]
    total_available: int

class DiscoveryCatalogueOut(BaseModel):
    sections: List[DiscoverySectionOut]
    total_sections: int


# --- DATASET IMPORT SCHEMAS ---

class DatasetImportStats(BaseModel):
    total_rows_processed: int
    imported: int
    updated: int
    skipped: int
    errors: List[str] = Field(default_factory=list)
    total_books_in_catalog: int
