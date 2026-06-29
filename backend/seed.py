"""Idempotent seeding: permissions catalog, system roles, first admin."""
from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from .config import settings
from .db import Base, SessionLocal, engine
from .models import Permission, Role, User
from .modules import all_permissions, module_permissions
from .security import hash_password


def seed(db: DbSession) -> None:
    # 1. Permission catalog
    existing_perms = {p.key for p in db.scalars(select(Permission)).all()}
    for key, desc in all_permissions():
        if key in existing_perms:
            continue
        db.add(Permission(key=key, description=desc))
    db.commit()

    # 2. System role: admin (gets every permission)
    admin_role = db.scalar(select(Role).where(Role.key == "admin"))
    all_perm_objs = db.scalars(select(Permission)).all()
    if not admin_role:
        admin_role = Role(
            key="admin",
            name="Администратор",
            description="Полный доступ ко всем модулям и админке",
            is_system=True,
            permissions=list(all_perm_objs),
        )
        db.add(admin_role)
    else:
        # keep admin in sync with the full catalog
        admin_role.permissions = list(all_perm_objs)
    db.commit()

    # 3. Convenience role: scanner_operator
    if not db.scalar(select(Role).where(Role.key == "scanner_operator")):
        scanner_perms = db.scalars(
            select(Permission).where(
                Permission.key.in_([k for k, _ in module_permissions()])
            )
        ).all()
        db.add(
            Role(
                key="scanner_operator",
                name="Оператор сканера",
                description="Доступ к модулю сканирования",
                is_system=False,
                permissions=list(scanner_perms),
            )
        )
        db.commit()

    # 4. First admin user (only if there are no users at all)
    if db.scalar(select(User)) is None:
        admin = User(
            username=settings.admin_username,
            password_hash=hash_password(settings.admin_password),
            full_name=settings.admin_full_name,
            is_active=True,
            roles=[admin_role],
        )
        db.add(admin)
        db.commit()
        print(f"[seed] created admin user '{settings.admin_username}'")


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed(db)


if __name__ == "__main__":
    init_db()
    print("[seed] done")
