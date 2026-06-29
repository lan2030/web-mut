"""Application configuration loaded from environment / .env."""
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent


class Settings(BaseSettings):
    # Session
    session_secret: str = "change-me-in-env"
    session_cookie_name: str = "session_id"
    session_ttl_hours: int = 24 * 7
    cookie_secure: bool = False  # set True behind HTTPS

    # Database
    database_url: str = f"sqlite:///{PROJECT_DIR / 'data' / 'app.db'}"

    # First admin (seeded once if no users exist)
    admin_username: str = "admin"
    admin_password: str = "admin12345"
    admin_full_name: str = "Administrator"

    # 1C proxy (reused from the original scanner)
    onec_auth: str = ""
    onec_user: str = ""
    onec_password: str = ""
    onec_base_url: str = "https://1c.ubtech.pro/test-trk-gkolymp/hs/mwp/getrests"

    model_config = SettingsConfigDict(
        env_file=(PROJECT_DIR / ".env", BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
