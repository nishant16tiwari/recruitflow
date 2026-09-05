from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import COOKIE_NAME, get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import UserLogin, UserRead, UserRegister
from app.services.auth_service import authenticate_user, issue_token_for_user, register_user

router = APIRouter(prefix="/auth", tags=["auth"])


def _set_auth_cookie(response: Response, token: str) -> None:
    is_production = settings.ENVIRONMENT == "production"
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="none" if is_production else "lax",
        secure=is_production,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )


@router.post("/register", response_model=UserRead, status_code=201)
def register(data: UserRegister, response: Response, db: Session = Depends(get_db)):
    user = register_user(db, data)
    token = issue_token_for_user(user)
    _set_auth_cookie(response, token)
    user_read = UserRead.model_validate(user)
    user_read.access_token = token
    return user_read


@router.post("/login", response_model=UserRead)
def login(data: UserLogin, response: Response, db: Session = Depends(get_db)):
    user = authenticate_user(db, data)
    token = issue_token_for_user(user)
    _set_auth_cookie(response, token)
    user_read = UserRead.model_validate(user)
    user_read.access_token = token
    return user_read


@router.post("/logout")
def logout(response: Response):
    is_production = settings.ENVIRONMENT == "production"
    response.delete_cookie(
        key=COOKIE_NAME,
        path="/",
        samesite="none" if is_production else "lax",
        secure=is_production,
    )
    return {"success": True}


@router.get("/me", response_model=UserRead)
def me(current_user: User = Depends(get_current_user)):
    return current_user
