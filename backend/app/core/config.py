from __future__ import annotations

import os as _os
from pathlib import Path
from typing import Dict, List

from pydantic_settings import BaseSettings, SettingsConfigDict

_env_path = ".env"
if not _os.path.exists(_env_path):
    _parent_env = _os.path.join(
        _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))),
        ".env",
    )
    if _os.path.exists(_parent_env):
        _env_path = _parent_env


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_env_path,
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # App
    APP_NAME: str = "DataBridge"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    ALLOWED_ORIGINS: List[str] = ["*"]

    # Database (existing PostgreSQL)
    DATABASE_URL: str = "postgresql+asyncpg://nilesh:P1a%40ss3@localhost:5432/databridge_db"
    DATABASE_ECHO: bool = False
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # LDAP (Red Chillies Active Directory)
    LDAP_ENABLED: bool = True
    LDAP_SERVER: str = "ldap://mumdc01.redchillies.com"
    LDAP_USE_SSL: bool = False
    LDAP_BASE_DN: str = "OU=Redchillies,DC=redchillies,DC=com"
    LDAP_USER_DN: str = "OU=Redchillies,DC=redchillies,DC=com"
    LDAP_GROUP_DN: str = "OU=Groups,DC=redchillies,DC=com"
    LDAP_BIND_DN: str = "cn=proxyuser,cn=Users,dc=redchillies,dc=com"
    LDAP_BIND_PASSWORD: str = ""
    LDAP_USER_ATTR: str = "uid"
    LDAP_EMAIL_ATTR: str = "mail"
    LDAP_DISPLAY_NAME_ATTR: str = "displayName"
    LDAP_USER_SEARCH_FILTER: str = "(&(objectClass=user)({user_attr}={username}))"

    # ShotGrid Department → App Role (LDAP authenticates; ShotGrid department determines role)
    SHOTGRID_DEPARTMENT_ROLE_MAP: Dict[str, str] = {
        "VFX": "artist",
        "Animation": "artist",
        "Lighting": "artist",
        "Compositing": "artist",
        "FX": "artist",
        "Matchmove": "artist",
        "Textures": "artist",
        "Modeling": "artist",
        "Rigging": "artist",
        "Layout": "artist",
        "Art": "artist",
        "Editorial": "artist",
        "Team Lead": "team_lead",
        "Lead": "team_lead",
        "Supervision": "supervisor",
        "VFX Supervision": "supervisor",
        "Production": "line_producer",
        "Line Production": "line_producer",
        "Production Management": "line_producer",
        "Data Management": "data_team",
        "Data": "data_team",
        "Pipeline": "data_team",
        "IT": "it_team",
        "Systems": "it_team",
        "Infrastructure": "it_team",
        "Administration": "admin",
        "Outsource": "admin",
    }
    SHOTGRID_DEFAULT_ROLE: str = "artist"

    # Superadmin (always works, bypasses LDAP)
    SUPERADMIN_USERNAME: str = "superadmin"
    SUPERADMIN_PASSWORD: str = "DataBridge@2026"
    SUPERADMIN_EMAIL: str = "admin@studio.com"

    # ShotGrid (RCVFX)
    SHOTGRID_ENABLED: bool = True
    SHOTGRID_URL: str = "https://rcvfx.shotgunstudio.com"
    SHOTGRID_SCRIPT_NAME: str = "shotgrid_api"
    SHOTGRID_API_KEY: str = ""
    SHOTGRID_PROJECT_ID: int = 0

    # JWT
    JWT_SECRET_KEY: str = "change-this-to-a-64-char-random-string"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # File paths (network mounts on your server)
    STAGING_NETWORK_PATH: str = "/mnt/staging"
    PRODUCTION_NETWORK_PATH: str = "/mnt/production"
    UPLOAD_TEMP_PATH: str = "/tmp/databridge_uploads"
    MAX_UPLOAD_SIZE_GB: float = 50.0

    # Transfer
    TRANSFER_METHOD: str = "rsync"

    # Allowed VFX file formats (extension -> category for preview)
    ALLOWED_FILE_FORMATS: Dict[str, List[str]] = {
        "image": [".jpg", ".jpeg", ".png", ".exr", ".tif", ".tiff", ".dpx", ".hdr", ".psd", ".tga"],
        "video": [".mov", ".mp4", ".avi", ".mxf", ".mkv"],
        "3d_scene": [".abc", ".fbx", ".obj", ".usd", ".usda", ".usdc", ".ma", ".mb"],
    }

    # Role hierarchy (higher number = higher authority)
    ROLE_HIERARCHY: Dict[str, int] = {
        "artist": 1,
        "team_lead": 2,
        "supervisor": 3,
        "line_producer": 4,
        "data_team": 5,
        "it_team": 6,
        "admin": 7,
    }

    # SMTP
    SMTP_HOST: str = "smtp.redchillies.com"
    SMTP_PORT: int = 587
    SMTP_FROM_EMAIL: str = "databridge@redchillies.com"
    NOTIFICATION_ENABLED: bool = True

    # ClamAV
    CLAMAV_ENABLED: bool = False

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = "/var/log/databridge"

    # Static files (built frontend)
    STATIC_DIR: str = str(Path(__file__).resolve().parent.parent.parent.parent / "frontend" / "dist")

    @property
    def database_url_sync(self) -> str:
        return self.DATABASE_URL.replace("+asyncpg", "+psycopg2")

    @property
    def all_allowed_extensions(self) -> List[str]:
        exts: List[str] = []
        for fmt_list in self.ALLOWED_FILE_FORMATS.values():
            exts.extend(fmt_list)
        return exts


def get_file_category(extension: str) -> str:
    """Return 'image', 'video', '3d_scene', or 'unknown'."""
    ext = (extension or "").lower().strip()
    if not ext.startswith("."):
        ext = f".{ext}"
    if ext in [".jpg", ".jpeg", ".png", ".exr", ".tif", ".tiff", ".dpx", ".hdr", ".psd", ".tga"]:
        return "image"
    if ext in [".mov", ".mp4", ".avi", ".mxf", ".mkv"]:
        return "video"
    if ext in [".abc", ".fbx", ".obj", ".usd", ".usda", ".usdc", ".ma", ".mb"]:
        return "3d_scene"
    return "unknown"


settings = Settings()
ALLOWED_EXTENSIONS: List[str] = settings.all_allowed_extensions
