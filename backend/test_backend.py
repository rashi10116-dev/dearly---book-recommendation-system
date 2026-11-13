"""Automated backend verification test."""
from app.database import SessionLocal, Base, engine
from app.models import User, Book, ReadingEntry, UserPreference
from app.auth import hash_password, verify_password, create_access_token
from app.recommendations import recommendation_engine
from app.schemas import UserRegister, UserLogin, UserPreferenceCreate, ReadingEntryCreate

def test_backend_flow():
    db = SessionLocal()
    try:
        # 1. Verify books
        books = db.query(Book).all()
        print(f"Books in DB: {len(books)}")
        assert len(books) >= 30, "Seed books should be at least 30"

        # 2. Test user creation
        test_email = "testreader@example.com"
        existing = db.query(User).filter(User.email == test_email).first()
        if existing:
            db.delete(existing)
            db.commit()

        user = User(
            email=test_email,
            username="AriaBookworm",
            hashed_password=hash_password("Passphrase123!")
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"User created: {user.username} (ID: {user.id})")
        assert verify_password("Passphrase123!", user.hashed_password)

        # 3. Test preferences
        pref = UserPreference(
            user_id=user.id,
            display_name="Aria",
            preferred_writing_style="Lyrical",
            preferred_pacing="Slow Burn",
            preferred_emotional_tone="Dark",
            reading_difficulty="Balanced"
        )
        pref.set_list("favorite_genres", ["Dark Academia", "Fantasy", "Mystery"])
        pref.set_list("favorite_tropes", ["Enemies to Lovers", "Secret Society", "Found Family"])
        pref.set_list("favorite_themes", ["Obsession", "Trauma and Resilience"])
        pref.set_list("disliked_elements", ["Love Triangle"])
        pref.set_list("favorite_authors", ["Donna Tartt", "Leigh Bardugo"])
        db.add(pref)
        db.commit()
        print("Preferences saved.")

        # 4. Generate recommendations (cold-start / onboarding phase)
        dashboard = recommendation_engine.generate_recommendations(db, user)
        print("Dashboard generated successfully!")
        print(f"Taste Mixes genres: {list(dashboard.taste_mixes.keys())}")
        for g, items in dashboard.taste_mixes.items():
            print(f"  Genre '{g}': {len(items)} recommendations (Top: {items[0].book.title if items else 'None'})")
        print(f"Unexpected Mix: {len(dashboard.unexpected_mix)} recommendations (Top: {dashboard.unexpected_mix[0].book.title if dashboard.unexpected_mix else 'None'})")
        if dashboard.unexpected_mix:
            print(f"  Unexpected rationale: {dashboard.unexpected_mix[0].rationale}")

        # 5. Add reading interactions
        # User reads 2 books by Leigh Bardugo ("Six of Crows" and "Crooked Kingdom")
        soc = db.query(Book).filter(Book.title.ilike("%Six of Crows%")).first()
        ck = db.query(Book).filter(Book.title.ilike("%Crooked Kingdom%")).first()
        if soc and ck:
            entry1 = ReadingEntry(
                user_id=user.id,
                book_id=soc.id,
                status="completed",
                rating=5.0,
                review="Absolute masterpiece of character chemistry and heist precision!"
            )
            entry1.set_list("liked_elements", ["Found Family", "Kaz Brekker", "Witty Banter"])
            db.add(entry1)

            entry2 = ReadingEntry(
                user_id=user.id,
                book_id=ck.id,
                status="completed",
                rating=4.5,
                review="Stunning conclusion to the duology."
            )
            entry2.set_list("liked_elements", ["Pacing", "Emotional Stakes"])
            db.add(entry2)
            db.commit()
            print("Logged 2 books by Leigh Bardugo.")

        # 6. Re-generate recommendations after reading interactions
        dashboard2 = recommendation_engine.generate_recommendations(db, user)
        print("\n--- Dashboard After Reading History ---")
        print(f"Total read books: {dashboard2.total_read_books}")
        print(f"Because You Enjoyed Mix: {len(dashboard2.because_you_enjoyed_mix)} items (Anchor: {dashboard2.anchor_book_title})")
        if dashboard2.because_you_enjoyed_mix:
            print(f"  Item 1: {dashboard2.because_you_enjoyed_mix[0].book.title} - {dashboard2.because_you_enjoyed_mix[0].rationale}")
        print(f"Author Mix: {len(dashboard2.author_mix)} items")
        if dashboard2.author_mix:
            print(f"  Author Rec 1: {dashboard2.author_mix[0].book.title} by {dashboard2.author_mix[0].book.author}")
        print("Backend flow test PASSED with flying colors!")

    finally:
        db.close()

if __name__ == "__main__":
    test_backend_flow()
