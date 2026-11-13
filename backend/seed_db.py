from app.database import engine, Base, SessionLocal
from app.import_dataset import seed_database_if_empty
from app.models import Book
from app.recommendations import recommendation_engine

def run_seed():
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        count = seed_database_if_empty(db)
        print(f"Database seeded with {count} books.")
        books = db.query(Book).all()
        recommendation_engine.fit_catalog(books)
        print("Recommendation engine fitted.")
    finally:
        db.close()

if __name__ == "__main__":
    run_seed()
