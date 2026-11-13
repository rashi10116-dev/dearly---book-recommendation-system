from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, func

from ..database import get_db
from ..models import User, UserPreference
from ..schemas import UserRegister, UserLogin, Token, UserOut
from ..auth import hash_password, verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=dict)
def register(user_in: UserRegister, db: Session = Depends(get_db)):
    clean_email = user_in.email.strip().lower()
    clean_username = user_in.username.strip()

    if len(clean_username) < 3 or len(clean_username) > 50:
        raise HTTPException(status_code=400, detail="Username must be between 3 and 50 characters.")

    # 1. Case-insensitive check for existing email
    existing_email = db.query(User).filter(func.lower(User.email) == clean_email).first()
    if existing_email:
        raise HTTPException(status_code=400, detail="An account with this email already exists.")

    # 2. Case-insensitive check for existing username
    existing_username = db.query(User).filter(func.lower(User.username) == clean_username.lower()).first()
    if existing_username:
        raise HTTPException(status_code=400, detail="This username is already taken.")

    hashed_pw = hash_password(user_in.password)
    new_user = User(
        email=clean_email,
        username=clean_username,
        hashed_password=hashed_pw
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token = create_access_token(data={"sub": str(new_user.id), "username": new_user.username})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": new_user.id,
            "email": new_user.email,
            "username": new_user.username,
            "has_preferences": False,
            "display_name": new_user.username
        }
    }

@router.post("/login", response_model=dict)
def login(user_in: UserLogin, db: Session = Depends(get_db)):
    # Support case-insensitive lookup for both username and email
    identifier = user_in.username_or_email.strip().lower()

    if not identifier:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email is required."
        )

    user = db.query(User).filter(
        or_(func.lower(User.email) == identifier, func.lower(User.username) == identifier)
    ).first()

    if not user or not verify_password(user_in.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(data={"sub": str(user.id), "username": user.username})
    has_prefs = user.preference is not None
    display_name = user.preference.display_name if has_prefs and user.preference.display_name else user.username

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "has_preferences": has_prefs,
            "display_name": display_name
        }
    }

@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    has_prefs = current_user.preference is not None
    display_name = current_user.preference.display_name if has_prefs and current_user.preference.display_name else current_user.username
    return {
        "id": current_user.id,
        "email": current_user.email,
        "username": current_user.username,
        "has_preferences": has_prefs,
        "display_name": display_name
    }

@router.post("/logout")
def logout():
    return {"message": "Successfully logged out"}
