from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.schemas import Token, UserLogin, UserOut, UserSignup
from app.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


def _find_user(db: Session, identifier: str) -> User | None:
    clean = identifier.strip().lower()
    return (
        db.query(User)
        .filter(
            or_(
                func.lower(User.email) == clean,
                func.lower(User.username) == clean,
            )
        )
        .first()
    )


@router.post("/signup", response_model=Token, status_code=201)
def signup(data: UserSignup, db: Session = Depends(get_db)):
    email = data.email.lower().strip()
    username = data.username.strip()

    conflict = (
        db.query(User)
        .filter(
            or_(
                func.lower(User.email) == email,
                func.lower(User.username) == username.lower(),
            )
        )
        .first()
    )
    if conflict:
        if conflict.email.lower() == email:
            raise HTTPException(400, "An account with this email already exists")
        raise HTTPException(400, "This username is already taken")

    user = User(
        username=username,
        email=email,
        full_name=(data.full_name or "").strip() or None,
        password_hash=hash_password(data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return Token(access_token=create_access_token(user.id))


@router.post("/login", response_model=Token)
def login(data: UserLogin, db: Session = Depends(get_db)):
    user = _find_user(db, data.identifier or "")
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(401, "Incorrect email/username or password")
    return Token(access_token=create_access_token(user.id))


@router.post("/login-form", response_model=Token)
def login_form(
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = _find_user(db, form.username)
    if not user or not verify_password(form.password, user.password_hash):
        raise HTTPException(401, "Incorrect email/username or password")
    return Token(access_token=create_access_token(user.id))


@router.get("/me", response_model=UserOut)
def me(current: User = Depends(get_current_user)):
    return current


@router.post("/refresh", response_model=Token)
def refresh(current: User = Depends(get_current_user)):
    return Token(access_token=create_access_token(current.id))

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
import os

from supabase import create_client, Client


router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"]
)


SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")


if not SUPABASE_URL or not SUPABASE_KEY:
    print("WARNING: Supabase environment variables are missing.")


supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


@router.post("/forgot-password")
async def forgot_password(data: ForgotPasswordRequest):

    try:

        supabase.auth.reset_password_email(
            data.email,
            options={
                "redirect_to":
                "http://127.0.0.1:8000/reset-password"
            }
        )

        return {
            "success": True,
            "message":
            "If the account exists, a password reset email has been sent."
        }

    except Exception as e:

        print("Forgot password error:", e)

        # Don't reveal whether email exists
        return {
            "success": True,
            "message":
            "If the account exists, a password reset email has been sent."
        }