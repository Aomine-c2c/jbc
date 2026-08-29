import os
import sys
import json
import logging
from logging.handlers import RotatingFileHandler
from contextvars import ContextVar
from datetime import datetime, timezone
from pathlib import Path
from app.core.config import settings

# Context variables for request tracing
request_id_ctx: ContextVar[str] = ContextVar("request_id", default="-")
user_id_ctx: ContextVar[str] = ContextVar("user_id", default="-")
client_ip_ctx: ContextVar[str] = ContextVar("client_ip", default="-")


class JSONFormatter(logging.Formatter):
    """Structured JSON formatter for production log aggregation."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": request_id_ctx.get(),
            "user_id": user_id_ctx.get(),
            "client_ip": client_ip_ctx.get(),
            "module": record.module,
            "line": record.lineno,
            "environment": settings.ENVIRONMENT,
        }

        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        # Include any custom attributes in extra
        if hasattr(record, "extra_data") and isinstance(record.extra_data, dict):
            log_obj["extra"] = record.extra_data

        return json.dumps(log_obj)


class TextFormatter(logging.Formatter):
    """Clean text formatter with correlation IDs for developer consoles."""

    def format(self, record: logging.LogRecord) -> str:
        req_id = request_id_ctx.get()
        req_str = f" [{req_id[:8]}]" if req_id != "-" else ""
        record.req_info = req_str
        return super().format(record)


def setup_logging():
    """Initializes centralized structured logging for the application."""
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    # Ensure log directory exists
    log_path = Path(settings.LOG_DIR)
    try:
        log_path.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        # Fallback to local logs directory if permissions fail
        log_path = Path("./logs")
        log_path.mkdir(parents=True, exist_ok=True)

    # Choose formatter
    if settings.LOG_FORMAT.lower() == "json" or settings.ENVIRONMENT == "production":
        formatter = JSONFormatter()
    else:
        formatter = TextFormatter(
            fmt="%(asctime)s [%(levelname)s]%(req_info)s %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    # Root Logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers.clear()

    # 1. Console Handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)
    root_logger.addHandler(console_handler)

    # 2. Main App Log File (Rotating: 50MB per file, max 10 backups)
    app_log_file = log_path / "dwrms_app.log"
    try:
        app_file_handler = RotatingFileHandler(
            app_log_file, maxBytes=50 * 1024 * 1024, backupCount=10, encoding="utf-8"
        )
        app_file_handler.setFormatter(formatter)
        app_file_handler.setLevel(log_level)
        root_logger.addHandler(app_file_handler)
    except Exception as e:
        sys.stderr.write(f"Warning: Could not create app log file at {app_log_file}: {e}\n")

    # 3. Error-Only Log File (Rotating: 20MB per file, max 10 backups)
    error_log_file = log_path / "dwrms_error.log"
    try:
        error_file_handler = RotatingFileHandler(
            error_log_file, maxBytes=20 * 1024 * 1024, backupCount=10, encoding="utf-8"
        )
        error_file_handler.setFormatter(formatter)
        error_file_handler.setLevel(logging.ERROR)
        root_logger.addHandler(error_file_handler)
    except Exception as e:
        sys.stderr.write(f"Warning: Could not create error log file at {error_log_file}: {e}\n")

    # Configure 3rd-party noisy loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("aiosqlite").setLevel(logging.WARNING)
    logging.getLogger("asyncpg").setLevel(logging.WARNING)

    root_logger.info(
        f"Logging initialized: Level={settings.LOG_LEVEL}, Format={settings.LOG_FORMAT}, Path={log_path}"
    )


# Get application-level logger
logger = logging.getLogger("dwrms")
