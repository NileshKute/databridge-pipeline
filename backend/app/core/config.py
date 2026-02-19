from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=os.getenv("ENV_FILE", ".env"),
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
    LDAP_ROLE_MAP: Dict[str, str] = {
        "cn=artists,OU=Groups,DC=redchillies,DC=com": "artist",
        "cn=team-leads,OU=Groups,DC=redchillies,DC=com": "team_lead",
        "cn=supervisors,OU=Groups,DC=redchillies,DC=com": "supervisor",
        "cn=line-producers,OU=Groups,DC=redchillies,DC=com": "line_producer",
        "cn=data-team,OU=Groups,DC=redchillies,DC=com": "data_team",
        "cn=it-team,OU=Groups,DC=redchillies,DC=com": "it_team",
        "cn=admins,OU=Groups,DC=redchillies,DC=com": "admin",
    }

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


settings = Settings()
