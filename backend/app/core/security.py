from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# WHY bcrypt: it's a slow, salted hashing algorithm purpose-built for passwords
# (unlike sha256/md5 which are fast and therefore brute-forceable). passlib
# manages the salt automatically per-password.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(subject: str, extra_claims: dict | None = None) -> str:
    """
    WHY JWT in an httpOnly cookie rather than localStorage:
    localStorage is readable by any JS running on the page, so an XSS bug
    anywhere in the frontend (or a compromised npm package) can steal the
    token. An httpOnly cookie is invisible to JavaScript entirely, which
    removes that attack surface. We pair it with SameSite=Lax to reduce CSRF risk.
    """
    to_encode: dict = {"sub": subject}
    if extra_claims:
        to_encode.update(extra_claims)
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode["exp"] = expire
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        return None
