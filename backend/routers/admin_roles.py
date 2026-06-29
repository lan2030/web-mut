"""Admin: role & permission management (requires admin:roles)."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from ..db import get_db
from ..models import Permission, Role
from ..deps import require_permission
from ..schemas import PermissionOut, RoleCreate, RoleOut, RoleUpdate

router = APIRouter(
    prefix="/api/admin",
    tags=["admin:roles"],
    dependencies=[Depends(require_permission("admin:roles"))],
)


def to_out(role: Role) -> RoleOut:
    return RoleOut(
        id=role.id,
        key=role.key,
        name=role.name,
        description=role.description,
        is_system=role.is_system,
        permissions=[p.key for p in role.permissions],
    )


def _load_permissions(db: DbSession, keys: list[str]) -> list[Permission]:
    if not keys:
        return []
    perms = db.scalars(select(Permission).where(Permission.key.in_(keys))).all()
    if len(perms) != len(set(keys)):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Указаны несуществующие права")
    return list(perms)


@router.get("/permissions", response_model=list[PermissionOut])
def list_permissions(db: DbSession = Depends(get_db)):
    return db.scalars(select(Permission).order_by(Permission.key)).all()


@router.get("/roles", response_model=list[RoleOut])
def list_roles(db: DbSession = Depends(get_db)):
    return [to_out(r) for r in db.scalars(select(Role).order_by(Role.id)).all()]


@router.post("/roles", response_model=RoleOut, status_code=status.HTTP_201_CREATED)
def create_role(payload: RoleCreate, db: DbSession = Depends(get_db)):
    if db.scalar(select(Role).where(Role.key == payload.key)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Роль с таким ключом уже существует")
    role = Role(
        key=payload.key,
        name=payload.name,
        description=payload.description,
        permissions=_load_permissions(db, payload.permissions),
    )
    db.add(role)
    db.commit()
    db.refresh(role)
    return to_out(role)


@router.patch("/roles/{role_id}", response_model=RoleOut)
def update_role(role_id: int, payload: RoleUpdate, db: DbSession = Depends(get_db)):
    role = db.get(Role, role_id)
    if not role:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Роль не найдена")
    if role.is_system and payload.permissions is not None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Нельзя менять права системной роли")
    if payload.name is not None:
        role.name = payload.name
    if payload.description is not None:
        role.description = payload.description
    if payload.permissions is not None:
        role.permissions = _load_permissions(db, payload.permissions)
    db.commit()
    db.refresh(role)
    return to_out(role)


@router.delete("/roles/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_role(role_id: int, db: DbSession = Depends(get_db)):
    role = db.get(Role, role_id)
    if not role:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Роль не найдена")
    if role.is_system:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Нельзя удалить системную роль")
    db.delete(role)
    db.commit()
