"""Registry of application modules and the permission catalog.

Modules are gated by ``module:<key>`` permissions; the dashboard menu is built
from the modules the current user is allowed to see. This is the single source
of truth the backend uses both to seed permissions and to answer /auth/me.
"""

# key, name, icon (lucide), route (frontend), permission
MODULES = [
    {
        "key": "scanner",
        "name": "Сканер 1С",
        "icon": "qr-code",
        "route": "/modules/scanner",
        "permission": "module:scanner",
    },
]

# Admin permissions (not tied to a module tile)
ADMIN_PERMISSIONS = [
    ("admin:users", "Управление пользователями"),
    ("admin:roles", "Управление ролями"),
]


def module_permissions() -> list[tuple[str, str]]:
    return [(m["permission"], f"Доступ к модулю: {m['name']}") for m in MODULES]


def all_permissions() -> list[tuple[str, str]]:
    """Full catalog of permission keys with human descriptions."""
    return module_permissions() + ADMIN_PERMISSIONS


def modules_for(permission_keys: set[str]) -> list[dict]:
    """Modules visible to a user holding the given permissions."""
    return [m for m in MODULES if m["permission"] in permission_keys]
