import os
import shutil
import uuid
import mimetypes
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional
from app.core.config import settings
from app.core.logging_config import logger

STORAGE_CATEGORIES = ("job_cards", "reports", "fleet", "signatures", "temp")


class StorageManager:
    """Enterprise Storage Manager for industrial file attachments and document archives."""

    def __init__(self, base_path: str | None = None):
        self.base_path = Path(base_path or settings.STORAGE_PATH).resolve()

    def init_storage(self) -> None:
        """Initializes and verifies storage directory structures and permissions."""
        try:
            self.base_path.mkdir(parents=True, exist_ok=True)
            for category in STORAGE_CATEGORIES:
                cat_dir = self.base_path / category
                cat_dir.mkdir(parents=True, exist_ok=True)
            
            # Verify write permissions with a temporary probe file
            test_file = self.base_path / "temp" / f".probe_{uuid.uuid4().hex[:8]}"
            test_file.write_text("storage_probe_ok", encoding="utf-8")
            test_file.unlink()
            
            logger.info(f"Storage initialized and verified at: {self.base_path}")
        except Exception as e:
            logger.error(f"Failed to initialize storage at {self.base_path}: {e}")
            raise RuntimeError(f"Storage initialization failure: {e}")

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitizes filename against path traversal attacks."""
        name = os.path.basename(filename).replace(" ", "_")
        # Keep only alphanumeric, hyphens, underscores, dots
        clean = "".join(c for c in name if c.isalnum() or c in (".", "-", "_"))
        return clean or f"attachment_{uuid.uuid4().hex[:8]}"

    def save_file(
        self,
        category: str,
        filename: str,
        content: bytes,
        content_type: Optional[str] = None,
    ) -> dict:
        """Saves a file attachment into the designated category directory."""
        if category not in STORAGE_CATEGORIES:
            raise ValueError(f"Invalid storage category: '{category}'. Allowed: {STORAGE_CATEGORIES}")

        # Check file size limit
        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        if len(content) > max_bytes:
            raise ValueError(
                f"File size ({len(content) / (1024 * 1024):.1f}MB) exceeds maximum limit ({settings.MAX_UPLOAD_SIZE_MB}MB)."
            )

        sanitized_name = self._sanitize_filename(filename)
        ext = sanitized_name.rsplit(".", 1)[-1].lower() if "." in sanitized_name else ""

        # Validate extension
        if ext and ext not in settings.allowed_extensions_set:
            raise ValueError(
                f"File extension '.{ext}' is not permitted. Allowed: {settings.ALLOWED_EXTENSIONS}"
            )

        # Generate unique storage filename
        file_uuid = uuid.uuid4().hex
        stored_filename = f"{file_uuid}_{sanitized_name}"
        category_dir = self.base_path / category
        category_dir.mkdir(parents=True, exist_ok=True)
        file_path = category_dir / stored_filename

        # Write file contents
        file_path.write_bytes(content)

        detected_type = content_type or mimetypes.guess_type(sanitized_name)[0] or "application/octet-stream"

        metadata = {
            "file_id": file_uuid,
            "original_filename": sanitized_name,
            "stored_filename": stored_filename,
            "category": category,
            "size_bytes": len(content),
            "content_type": detected_type,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "relative_path": f"{category}/{stored_filename}",
        }

        logger.info(f"File stored successfully: {metadata['relative_path']} ({len(content)} bytes)")
        return metadata

    def get_file_path(self, category: str, stored_filename: str) -> Path:
        """Safely resolves file path preventing directory traversal."""
        if category not in STORAGE_CATEGORIES:
            raise ValueError(f"Invalid storage category: {category}")

        sanitized_name = os.path.basename(stored_filename)
        target_path = (self.base_path / category / sanitized_name).resolve()

        # Strict containment check
        if not str(target_path).startswith(str(self.base_path)):
            raise PermissionError("Access denied: Attempted directory traversal outside storage root.")

        if not target_path.exists() or not target_path.is_file():
            raise FileNotFoundError(f"File not found: {category}/{sanitized_name}")

        return target_path

    def delete_file(self, category: str, stored_filename: str) -> bool:
        """Deletes a file attachment."""
        try:
            path = self.get_file_path(category, stored_filename)
            path.unlink()
            logger.info(f"File deleted: {category}/{stored_filename}")
            return True
        except Exception as e:
            logger.warning(f"Failed to delete file {category}/{stored_filename}: {e}")
            return False

    def get_storage_health(self) -> dict:
        """Probes storage directory accessibility and available disk space."""
        health = {
            "status": "healthy",
            "path": str(self.base_path),
            "exists": self.base_path.exists(),
            "write_ok": False,
            "total_bytes": 0,
            "free_bytes": 0,
            "used_bytes": 0,
            "free_percentage": 0.0,
        }

        if not self.base_path.exists():
            health["status"] = "degraded"
            health["error"] = "Storage directory does not exist"
            return health

        # Probe write access
        try:
            probe_path = self.base_path / "temp" / f".probe_{uuid.uuid4().hex[:6]}"
            probe_path.parent.mkdir(parents=True, exist_ok=True)
            probe_path.write_text("probe", encoding="utf-8")
            probe_path.unlink()
            health["write_ok"] = True
        except Exception as e:
            health["status"] = "unhealthy"
            health["write_ok"] = False
            health["error"] = f"Write permission failed: {str(e)}"

        # Calculate disk usage
        try:
            total, used, free = shutil.disk_usage(self.base_path)
            health["total_bytes"] = total
            health["used_bytes"] = used
            health["free_bytes"] = free
            health["free_percentage"] = round((free / total) * 100, 2) if total > 0 else 0.0

            if health["free_percentage"] < 5.0:
                health["status"] = "warning"
                health["warning"] = "Low disk space (<5% remaining)"
        except Exception as e:
            health["disk_usage_error"] = str(e)

        return health


# Singleton storage manager
storage_manager = StorageManager()
