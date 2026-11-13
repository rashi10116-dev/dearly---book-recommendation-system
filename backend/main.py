from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import ALLOWED_ORIGINS, ENVIRONMENT
from app.database import engine, Base, SessionLocal, check_database_connection
from app.import_dataset import seed_database_if_empty
from app.models import Book
from app.recommendations import recommendation_engine
from app.routers import (
    auth,
    preferences,
    books,
    reading,
    recommendations,
    dataset
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables
    Base.metadata.create_all(bind=engine)
    
    # Auto-seed database if empty
    db = SessionLocal()
    try:
        seed_count = seed_database_if_empty(db)
        print(f"[DEARLY] Catalog ready with {seed_count} initial titles.")
        
        # Fit recommendation engine
        all_books = db.query(Book).all()
        recommendation_engine.fit_catalog(all_books)
        print(f"[DEARLY] Recommendation engine fitted on {len(all_books)} titles.")
    finally:
        db.close()
    
    yield

app = FastAPI(
    title="DEARLY API",
    description="Personalized Book Recommendation Platform API with Google Books & Open Library Integration",
    version="2.0.0",
    lifespan=lifespan
)

# CORS configuration
cors_origins = ALLOWED_ORIGINS if ENVIRONMENT == "production" else ALLOWED_ORIGINS + ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"]
cors_origins = list(set(cors_origins))

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Health checks
@app.get("/api/health")
def health_check():
    db_status = check_database_connection()
    return {
        "status": "healthy" if db_status.get("connected") else "degraded",
        "service": "DEARLY Backend",
        "version": "2.0.0",
        "environment": ENVIRONMENT,
        "database": db_status,
        "recommendation_engine": {
            "is_fitted": recommendation_engine.is_fitted,
            "catalog_size": len(recommendation_engine.book_ids)
        }
    }

@app.get("/")
def root():
    return {
        "message": "Welcome to DEARLY API. Explore /docs for interactive documentation."
    }

# Mount routers
app.include_router(auth.router, prefix="/api")
app.include_router(preferences.router, prefix="/api")
app.include_router(books.router, prefix="/api")
app.include_router(reading.router, prefix="/api")
app.include_router(recommendations.router, prefix="/api")
app.include_router(dataset.router, prefix="/api")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
