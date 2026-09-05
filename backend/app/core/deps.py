from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.application_panel import ApplicationPanel
from app.models.user import User
from app.models.enums import UserRole

COOKIE_NAME = "access_token"


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """
    The single source of truth for "who is making this request."
    Reads the JWT from the httpOnly cookie (never from a header/body the
    client could freely edit), decodes it, and loads the real User row from
    the database - we never trust claims embedded in the token for anything
    beyond identifying WHICH user, since role could theoretically change
    after the token was issued (e.g. an admin demoting someone).
    """
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1]
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired session")

    user = db.get(User, int(payload["sub"]))
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User no longer exists")

    return user


def require_role(*allowed_roles: UserRole):
    """
    A dependency FACTORY. WHY: it lets each route declare exactly which
    roles may call it, e.g. Depends(require_role(UserRole.RECRUITER)),
    while sharing one implementation. This is what makes "hide the button
    in React" irrelevant - even if a request bypasses the frontend
    entirely (curl, Postman, a modified fetch call), this dependency runs
    on every matching route and rejects the wrong role with 403 before any
    business logic executes.
    """

    def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This action requires role: {', '.join(r.value for r in allowed_roles)}",
            )
        return current_user

    return dependency


require_recruiter = require_role(UserRole.RECRUITER)
require_interviewer = require_role(UserRole.INTERVIEWER)


def is_interviewer_assigned(db: Session, application_id: int, user_id: int) -> bool:
    """
    Resource-level authorization check: is this specific interviewer on
    this specific application's panel? This is what prevents an
    interviewer from reading GET /applications/999 for a candidate they
    have nothing to do with, even though they're a valid, authenticated
    INTERVIEWER user.
    """
    return (
        db.query(ApplicationPanel)
        .filter(
            ApplicationPanel.application_id == application_id,
            ApplicationPanel.interviewer_id == user_id,
        )
        .first()
        is not None
    )
