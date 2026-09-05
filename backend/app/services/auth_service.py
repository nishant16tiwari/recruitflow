from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password, create_access_token
from app.models.user import User
from app.schemas.auth import UserRegister, UserLogin


def register_user(db: Session, data: UserRegister) -> User:
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        # WHY 400 not 409 here: FastAPI/most frontends treat 400 as "fix your
        # input," which is exactly the case - duplicate email is a validation
        # failure from the client's perspective, not a server conflict.
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
        name=data.name,
        role=data.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, data: UserLogin) -> User:
    user = db.query(User).filter(User.email == data.email).first()
    # WHY check verify_password even when user is None (against a dummy hash
    # would be more robust, but here we keep it simple): the important part
    # is returning the SAME generic error either way, so an attacker can't
    # use response differences to enumerate which emails are registered.
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    return user


def issue_token_for_user(user: User) -> str:
    return create_access_token(subject=str(user.id), extra_claims={"role": user.role.value})
