from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User, Book
from ..schemas import RecommendationDashboardOut
from ..auth import get_current_user
from ..recommendations import recommendation_engine

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])

@router.get("/dashboard", response_model=RecommendationDashboardOut)
async def get_recommendation_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate personalized discovery mixes for the authenticated reader across 6 collections:
    - Your Taste: Collections for top 3 genres, MMR reranked (12 books).
    - Your Unexpected Next Read: Cross-genre serendipitous discoveries (12 books).
    - From Authors You've Read: For authors with read books or favorites (10-12 books).
    - Because You Enjoyed...: Books similar to highly rated reads (12 books).
    - Explore New Genres: Acclaimed books outside the reader's primary genres (12 books).
    - Hidden Gems: High-rated books with understated circulation (12 books).
    """
    return await recommendation_engine.generate_recommendations_async(db=db, user=current_user)

@router.post("/recompute")
def recompute_recommendation_models(db: Session = Depends(get_db)):
    """Refit TF-IDF vectorizer over the book catalog."""
    books = db.query(Book).all()
    recommendation_engine.fit_catalog(books)
    return {
        "message": "Recommendation models recomputed successfully",
        "catalog_size": len(books)
    }
