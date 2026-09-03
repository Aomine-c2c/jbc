import os
from pathlib import Path
from functools import lru_cache
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_NAME: str = "Bikita Minerals DWRMS"
    APP_VERSION: str = "v2.9.0"
    API_VERSION: str = "v1"
    DB_SCHEMA_VERSION: str = "2026.08.28.01"
    WEB_CLIENT_VERSION: str = "v2.9.0"
    DESKTOP_CLIENT_VERSION: str = "v2.9.0"
    MIN_SUPPORTED_CLIENT_VERSION: str = "v2.0.0"
    UPDATE_CHANNEL: str = "enterprise_lts"
    ENVIRONMENT: str = "development"  # development, testing, staging, production
    DEBUG: bool = False
    SERVER_NAME: str = "bikita-srv-01"
    TIMEZONE: str = "Africa/Harare"

    # DB configuration
    DB_ENGINE: str = "postgresql"  # postgresql, mysql, sqlite
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "postgres"
    DB_HOST: str = "db"
    DB_PORT: int = 5432
    DB_NAME: str = "dwrms"
    DATABASE_URL: str | None = None
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30

    # Redis & Worker configuration
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str | None = None
    CELERY_RESULT_BACKEND: str | None = None

    # Storage & File Attachments
    STORAGE_PATH: str = "./storage"
    MAX_UPLOAD_SIZE_MB: int = 25
    ALLOWED_EXTENSIONS: str = "pdf,jpg,jpeg,png,webp,xlsx,docx,csv,txt"

    # Disaster Recovery & Backups
    BACKUP_DIR: str = "./backups"
    RETENTION_DAYS: int = 30

    # Logging & Diagnostics
    LOG_DIR: str = "./logs"
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # json or text

    # Auth configuration
    AUTH_METHOD: str = "LOCAL"
    LDAP_SERVER_URL: str | None = None
    LDAP_BIND_DN: str | None = None
    LDAP_BIND_PASSWORD: str | None = None
    LDAP_USER_BASE_DN: str | None = None

    # Security Configurations
    SECRET_KEY: str | None = None
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    # Disabled by default. Use the explicit seed command for initial setup.
    SEED_DEMO_DATA: bool = False
    # Test-only mock bearer tokens are never accepted in a normal runtime.
    ALLOW_TEST_TOKENS: bool = False
    # Web Push VAPID keys (generate with: openssl ecparam -genkey -name prime256v1 -out private.pem && openssl ec -in private.pem -pubout -out public.pem)
    VAPID_PRIVATE_KEY: str | None = None
    VAPID_PUBLIC_KEY: str | None = None

    # Frontend URLs for CORS
    FRONTEND_URL: str = "http://localhost:3000"
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:1420,tauri://localhost,http://tauri.localhost"

    # Optional Remote Connectivity & Transport Layer (Provider-Agnostic)
    DEPLOYMENT_MODE: str = "LOCAL_ONLY"  # LOCAL_ONLY, HYBRID_REMOTE, PRIVATE_DISTRIBUTED
    REMOTE_CONNECTIVITY_ENABLED: bool = False
    REMOTE_NETWORK_PROVIDER: str = "none"  # none, tailscale, wireguard, custom_vpn, zero_trust
    REMOTE_NETWORK_INTERFACE: str = "tailscale0"
    REMOTE_NETWORK_HOSTNAME: str | None = None
    REMOTE_NETWORK_IP: str | None = None

    @model_validator(mode="after")
    def resolve_paths_and_urls(self) -> "Settings":
        # Resolve production default storage and log paths if not customized
        if self.ENVIRONMENT in ("production", "staging"):
            if self.STORAGE_PATH == "./storage":
                self.STORAGE_PATH = "/var/dwrms/storage"
            if self.LOG_DIR == "./logs":
                self.LOG_DIR = "/var/dwrms/logs"

        # Resolve Database URL
        if not self.DATABASE_URL:
            if self.ENVIRONMENT in ("development", "testing"):
                self.DATABASE_URL = "sqlite+aiosqlite:///./test_dwrms.db"
            elif self.DB_ENGINE == "mysql":
                self.DATABASE_URL = f"mysql+aiomysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
            else:
                self.DATABASE_URL = f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        else:
            # Normalize URL driver prefixes for async SQLAlchemy
            if self.DATABASE_URL.startswith("postgres://"):
                self.DATABASE_URL = self.DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
            elif self.DATABASE_URL.startswith("postgresql://") and "+asyncpg" not in self.DATABASE_URL:
                self.DATABASE_URL = self.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
            elif self.DATABASE_URL.startswith("mysql://") and "+aiomysql" not in self.DATABASE_URL:
                self.DATABASE_URL = self.DATABASE_URL.replace("mysql://", "mysql+aiomysql://", 1)

        # Resolve Celery URLs from Redis if not explicitly provided
        if not self.CELERY_BROKER_URL:
            self.CELERY_BROKER_URL = self.REDIS_URL
        if not self.CELERY_RESULT_BACKEND:
            self.CELERY_RESULT_BACKEND = self.REDIS_URL

        return self

    @property
    def get_secret_key(self) -> str:
        if self.SECRET_KEY:
            return self.SECRET_KEY
        if self.ENVIRONMENT == "production":
            raise ValueError("CRITICAL: SECRET_KEY environment variable MUST be set in production.")
        return "dev-secret-key-change-in-production-123456789"

    @property
    def get_cors_origins(self) -> list[str]:
        configured = [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]
        if self.ENVIRONMENT == "production":
            origins = list(configured)
            if self.FRONTEND_URL and self.FRONTEND_URL not in origins:
                origins.append(self.FRONTEND_URL)
            if "tauri://localhost" not in origins:
                origins.append("tauri://localhost")
            if "http://tauri.localhost" not in origins:
                origins.append("http://tauri.localhost")
            return origins

        dev_defaults = [
            "http://localhost:3000", "http://127.0.0.1:3000",
            "http://localhost:8000", "http://127.0.0.1:8000",
            "http://tauri.localhost", "tauri://localhost",
            "http://localhost:1420", "http://127.0.0.1:1420"
        ]
        return list(dict.fromkeys(configured + dev_defaults))

    @property
    def allowed_extensions_set(self) -> set[str]:
        return {ext.strip().lower().lstrip(".") for ext in self.ALLOWED_EXTENSIONS.split(",") if ext.strip()}

    model_config = SettingsConfigDict(env_file=".env", extra="allow")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
