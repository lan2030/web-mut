"""Shared FastAPI dependencies: auth, permission checks, CSRF."""
from datetime import datetime, timezone

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session as DbSession

from .config import settings
from .db import get_db
from .models import Session as SessionModel, User

# State-changing methods require a valid CSRF token (double-submit).
UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


def _load_session(request: Request, db: DbSession) -> SessionModel | None:
    token = request.cookies.get(settings.session_cookie_name)
    if not token:
        return None
    session = db.get(SessionModel, token)
    if session is None:
        return None
    expires = session.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if expires < datetime.now(timezone.utc):
        db.delete(session)
        db.commit()
        return None
    return session


def get_current_session(request: Request, db: DbSession = Depends(get_db)) -> SessionModel:
    session = _load_session(request, db)
    if session is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")

    # CSRF: enforce double-submit token header on unsafe methods.
    if request.method in UNSAFE_METHODS:
        header = request.headers.get("X-CSRF-Token")
        if not header or header != session.csrf_token:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Invalid CSRF token")
    return session


def get_current_user(session: SessionModel = Depends(get_current_session)) -> User:
    user = session.user
    if not user or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Inactive or unknown user")
    return user


def require_permission(permission: str):
    def checker(user: User = Depends(get_current_user)) -> User:
        if permission not in user.permission_keys:
            raise HTTPException(status.HTTP_403_FORBIDDEN, f"Missing permission: {permission}")
        return user

    return checker
