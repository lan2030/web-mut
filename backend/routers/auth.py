"""Authentication: login, logout, current user."""
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from ..config import settings
from ..db import get_db
from ..deps import get_current_session, get_current_user
from ..models import Session as SessionModel, User, utcnow
from ..modules import modules_for
from ..schemas import LoginRequest, MeOut
from ..security import generate_token, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])


def build_me(user: User, csrf_token: str) -> MeOut:
    perms = user.permission_keys
    return MeOut(
        id=user.id,
        username=user.username,
        full_name=user.full_name,
        roles=[r.key for r in user.roles],
        permissions=sorted(perms),
        modules=modules_for(perms),
        csrf_token=csrf_token,
    )


@router.post("/login", response_model=MeOut)
def login(payload: LoginRequest, response: Response, db: DbSession = Depends(get_db)):
    user = db.scalar(select(User).where(User.username == payload.username))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Неверный логин или пароль")
    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Учётная запись отключена")

    session = SessionModel(
        token=generate_token(),
        user_id=user.id,
        csrf_token=generate_token(),
        expires_at=utcnow() + timedelta(hours=settings.session_ttl_hours),
    )
    db.add(session)
    db.commit()

    response.set_cookie(
        key=settings.session_cookie_name,
        value=session.token,
        max_age=settings.session_ttl_hours * 3600,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/",
    )
    return build_me(user, session.csrf_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    response: Response,
    session: SessionModel = Depends(get_current_session),
    db: DbSession = Depends(get_db),
):
    db.delete(session)
    db.commit()
    response.delete_cookie(settings.session_cookie_name, path="/")


@router.get("/me", response_model=MeOut)
def me(session: SessionModel = Depends(get_current_session), user: User = Depends(get_current_user)):
    return build_me(user, session.csrf_token)
