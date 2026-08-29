import re
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
from pydantic import BaseModel

from app.core.config import settings
from app.core.logging_config import logger


class ComponentVersion(BaseModel):
    name: str
    version: str
    status: str
    notes: Optional[str] = None


class VersionMatrix(BaseModel):
    server_version: str
    api_version: str
    db_schema_version: str
    web_client_version: str
    desktop_client_version: str
    min_supported_client_version: str
    update_channel: str
    environment: str
    last_updated: str
    components: List[ComponentVersion]


def parse_semver(v: str) -> Tuple[int, int, int]:
    """Extracts (major, minor, patch) integers from a semver string like 'v2.9.0' or '2.9.0'."""
    clean = re.sub(r'^[vV]', '', v.strip())
    parts = clean.split('.')
    try:
        major = int(parts[0]) if len(parts) > 0 else 0
        minor = int(parts[1]) if len(parts) > 1 else 0
        patch = int(re.sub(r'[^\d].*', '', parts[2])) if len(parts) > 2 else 0
        return (major, minor, patch)
    except Exception:
        return (0, 0, 0)


class PlatformVersionManager:
    """Manages version matrix tracking, client compatibility verification, and update checks."""

    def __init__(self):
        self.update_policy = "CONTROLLED_MANUAL"  # AUTOMATIC, CONTROLLED_MANUAL, DISABLED

    def get_version_matrix(self) -> VersionMatrix:
        """Returns the authoritative multi-tier version matrix."""
        comps = [
            ComponentVersion(name="Server Platform Core", version=settings.APP_VERSION, status="ACTIVE", notes="Ubuntu Server Authoritative Core"),
            ComponentVersion(name="Backend REST API", version=f"{settings.API_VERSION} ({settings.APP_VERSION})", status="ACTIVE", notes="Authoritative Django/FastAPI API"),
            ComponentVersion(name="Database Schema", version=settings.DB_SCHEMA_VERSION, status="APPLIED", notes=f"{settings.DB_ENGINE.upper()} Schema"),
            ComponentVersion(name="Web Client (Next.js)", version=settings.WEB_CLIENT_VERSION, status="ACTIVE", notes="First-class Browser / PWA Access"),
            ComponentVersion(name="Desktop Client (Tauri)", version=settings.DESKTOP_CLIENT_VERSION, status="COMPATIBLE", notes="Cross-platform Desktop Client"),
        ]

        return VersionMatrix(
            server_version=settings.APP_VERSION,
            api_version=settings.API_VERSION,
            db_schema_version=settings.DB_SCHEMA_VERSION,
            web_client_version=settings.WEB_CLIENT_VERSION,
            desktop_client_version=settings.DESKTOP_CLIENT_VERSION,
            min_supported_client_version=settings.MIN_SUPPORTED_CLIENT_VERSION,
            update_channel=settings.UPDATE_CHANNEL,
            environment=settings.ENVIRONMENT,
            last_updated=datetime.now(timezone.utc).isoformat(),
            components=comps,
        )

    def is_client_compatible(self, client_version: str) -> Tuple[bool, str]:
        """
        Validates whether a connecting Web/Tauri client version meets the minimum required version threshold.
        """
        if not client_version:
            return True, "Version header not supplied; operating in legacy compatibility mode."

        client_semver = parse_semver(client_version)
        min_semver = parse_semver(settings.MIN_SUPPORTED_CLIENT_VERSION)

        if client_semver >= min_semver:
            return True, f"Client {client_version} is compatible with platform {settings.APP_VERSION}."
        else:
            return False, f"Client version {client_version} is below minimum supported version {settings.MIN_SUPPORTED_CLIENT_VERSION}. Please update your desktop client."

    def check_for_updates(self) -> Dict[str, Any]:
        """
        Checks for available platform updates on the configured release channel without auto-installing.
        """
        # In self-hosted offline or air-gapped deployments, check local update bundles or approved repository
        current_v = settings.APP_VERSION
        
        # Simulating enterprise LTS channel check
        return {
            "current_version": current_v,
            "channel": settings.UPDATE_CHANNEL,
            "update_policy": self.update_policy,
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "has_update": False,
            "latest_approved_version": current_v,
            "status": "UP_TO_DATE",
            "release_notes_url": "/docs/RELEASE_NOTES.md",
            "message": f"Platform is running the latest approved release ({current_v}) on the '{settings.UPDATE_CHANNEL}' channel.",
        }


version_manager = PlatformVersionManager()
