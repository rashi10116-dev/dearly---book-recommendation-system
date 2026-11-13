import io
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Book
from ..schemas import DatasetImportStats
from ..import_dataset import import_books_from_csv, seed_database_if_empty
from ..recommendations import recommendation_engine
from ..config import MAX_UPLOAD_SIZE_BYTES, MAX_UPLOAD_ROWS

router = APIRouter(prefix="/dataset", tags=["Dataset"])

@router.post("/import-csv", response_model=DatasetImportStats)
async def upload_csv_dataset(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only valid CSV files (.csv) are supported.")

    content = await file.read()
    if len(content) > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum allowed size is {MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)} MB."
        )

    # Decode and check line count
    text_content = content.decode("utf-8", errors="replace")
    line_count = text_content.count("\n")
    if line_count > MAX_UPLOAD_ROWS + 5: # allow header + slight padding
        raise HTTPException(
            status_code=400,
            detail=f"CSV contains too many rows ({line_count}). Maximum allowed rows per import is {MAX_UPLOAD_ROWS}."
        )

    buffer = io.StringIO(text_content)
    stats = import_books_from_csv(buffer, db=db, update_duplicates=True)
    
    # Recompute recommendation engine on updated catalog
    books = db.query(Book).all()
    recommendation_engine.fit_catalog(books)

    return stats

@router.post("/reset-seed")
def reset_seed_data(db: Session = Depends(get_db)):
    """Seed database with default curated catalog."""
    total = seed_database_if_empty(db)
    books = db.query(Book).all()
    recommendation_engine.fit_catalog(books)
    return {"message": f"Seed catalogue ready with {total} books."}

@router.get("/stats")
def get_dataset_stats(db: Session = Depends(get_db)):
    books = db.query(Book).all()
    total = len(books)
    
    genre_dist = {}
    for b in books:
        genre_name = b.genre or "General"
        genre_dist[genre_name] = genre_dist.get(genre_name, 0) + 1

    return {
        "total_books": total,
        "total_genres": len(genre_dist),
        "genres": genre_dist,
        "is_model_fitted": recommendation_engine.is_fitted
    }
