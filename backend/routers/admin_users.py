"""Admin: user management (requires admin:users)."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from ..db import get_db
from ..deps import get_current_user, require_permission
from ..models import Role, User
from ..schemas import PasswordReset, UserCreate, UserOut, UserUpdate
from ..security import hash_password

router = APIRouter(
    prefix="/api/admin/users",
    tags=["admin:users"],
    dependencies=[Depends(require_permission("admin:users"))],
)


def to_out(user: User) -> UserOut:
    return UserOut(
        id=user.id,
        username=user.username,
        full_name=user.full_name,
        is_active=user.is_active,
        created_at=user.created_at,
        roles=[r.key for r in user.roles],
    )


def _load_roles(db: DbSession, role_ids: list[int]) -> list[Role]:
    if not role_ids:
        return []
    roles = db.scalars(select(Role).where(Role.id.in_(role_ids))).all()
    if len(roles) != len(set(role_ids)):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Одна или несколько ролей не найдены")
    return list(roles)


@router.get("", response_model=list[UserOut])
def list_users(db: DbSession = Depends(get_db)):
    users = db.scalars(select(User).order_by(User.id)).all()
    return [to_out(u) for u in users]


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, db: DbSession = Depends(get_db)):
    if db.scalar(select(User).where(User.username == payload.username)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Пользователь с таким логином уже существует")
    user = User(
        username=payload.username,
        password_hash=hash_password(payload.password),
        full_name=payload.full_name,
        roles=_load_roles(db, payload.role_ids),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return to_out(user)


@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: int, db: DbSession = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Пользователь не найден")
    return to_out(user)


@router.patch("/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    payload: UserUpdate,
    db: DbSession = Depends(get_db),
    current: User = Depends(get_current_user),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Пользователь не найден")

    if payload.full_name is not None:
        user.full_name = payload.full_name
    if payload.is_active is not None:
        if user.id == current.id and not payload.is_active:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Нельзя отключить самого себя")
        user.is_active = payload.is_active
    if payload.role_ids is not None:
        new_roles = _load_roles(db, payload.role_ids)
        # Safeguard: don't let the last admin strip their own admin access.
        if user.id == current.id and "admin:roles" not in {
            p.key for r in new_roles for p in r.permissions
        }:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, "Нельзя снять с себя административные права"
            )
        user.roles = new_roles

    db.commit()
    db.refresh(user)
    return to_out(user)


@router.post("/{user_id}/reset-password", status_code=status.HTTP_204_NO_CONTENT)
def reset_password(user_id: int, payload: PasswordReset, db: DbSession = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Пользователь не найден")
    user.password_hash = hash_password(payload.password)
    db.commit()


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_user(
    user_id: int, db: DbSession = Depends(get_db), current: User = Depends(get_current_user)
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Пользователь не найден")
    if user.id == current.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Нельзя удалить самого себя")
    user.is_active = False  # soft delete
    db.commit()
