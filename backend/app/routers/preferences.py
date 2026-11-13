from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User, UserPreference
from ..schemas import UserPreferenceCreate, UserPreferenceUpdate, UserPreferenceOut
from ..auth import get_current_user

router = APIRouter(prefix="/preferences", tags=["Preferences"])

@router.get("", response_model=UserPreferenceOut)
def get_user_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    pref = db.query(UserPreference).filter(UserPreference.user_id == current_user.id).first()
    if not pref:
        raise HTTPException(status_code=404, detail="No preferences found for this user.")
    
    return UserPreferenceOut(
        id=pref.id,
        user_id=pref.user_id,
        display_name=pref.display_name,
        favorite_genres=pref.get_list("favorite_genres"),
        favorite_tropes=pref.get_list("favorite_tropes"),
        favorite_themes=pref.get_list("favorite_themes"),
        preferred_writing_style=pref.preferred_writing_style,
        preferred_pacing=pref.preferred_pacing,
        preferred_emotional_tone=pref.preferred_emotional_tone,
        preferred_book_length=pref.preferred_book_length,
        favorite_authors=pref.get_list("favorite_authors"),
        disliked_elements=pref.get_list("disliked_elements"),
        reading_difficulty=pref.reading_difficulty,
        updated_at=pref.updated_at
    )

@router.post("", response_model=UserPreferenceOut)
def save_user_preferences(
    pref_in: UserPreferenceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    pref = db.query(UserPreference).filter(UserPreference.user_id == current_user.id).first()
    if not pref:
        pref = UserPreference(user_id=current_user.id)
        db.add(pref)

    pref.display_name = pref_in.display_name or current_user.username
    pref.set_list("favorite_genres", pref_in.favorite_genres)
    pref.set_list("favorite_tropes", pref_in.favorite_tropes)
    pref.set_list("favorite_themes", pref_in.favorite_themes)
    pref.preferred_writing_style = pref_in.preferred_writing_style
    pref.preferred_pacing = pref_in.preferred_pacing
    pref.preferred_emotional_tone = pref_in.preferred_emotional_tone
    pref.preferred_book_length = pref_in.preferred_book_length
    pref.set_list("favorite_authors", pref_in.favorite_authors)
    pref.set_list("disliked_elements", pref_in.disliked_elements)
    pref.reading_difficulty = pref_in.reading_difficulty

    db.commit()
    db.refresh(pref)

    return UserPreferenceOut(
        id=pref.id,
        user_id=pref.user_id,
        display_name=pref.display_name,
        favorite_genres=pref.get_list("favorite_genres"),
        favorite_tropes=pref.get_list("favorite_tropes"),
        favorite_themes=pref.get_list("favorite_themes"),
        preferred_writing_style=pref.preferred_writing_style,
        preferred_pacing=pref.preferred_pacing,
        preferred_emotional_tone=pref.preferred_emotional_tone,
        preferred_book_length=pref.preferred_book_length,
        favorite_authors=pref.get_list("favorite_authors"),
        disliked_elements=pref.get_list("disliked_elements"),
        reading_difficulty=pref.reading_difficulty,
        updated_at=pref.updated_at
    )
