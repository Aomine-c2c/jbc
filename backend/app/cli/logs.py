import os
import sys
import re
import click
from pathlib import Path

from app.cli.utils import (
    print_header,
    print_error,
    print_warning,
    run_command_capture,
    ROOT_DIR,
)
from app.core.config import settings


@click.command("logs")
@click.option("--service", "-s", default="app", help="Service/Log file (app, error, backend, worker, beat, nginx, db, redis)")
@click.option("--lines", "-n", default=50, type=int, help="Number of lines to inspect (default: 50)")
@click.option("--follow", "-f", is_flag=True, help="Follow logs continuously")
@click.option("--level", "-l", type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"], case_sensitive=False), help="Filter by minimum log level")
@click.option("--search", "-q", help="Filter lines matching a search query or regex")
@click.option("--request-id", help="Filter logs by X-Request-ID correlation ID")
def logs_command(service, lines, follow, level, search, request_id):
    """Inspect and filter application and container logs."""
    service_lower = service.lower()

    # If asking for container logs directly
    if service_lower in ("backend", "worker", "beat", "nginx", "frontend", "db", "redis"):
        cmd = ["docker", "compose", "-f", "docker-compose.prod.yml", "logs"]
        if follow:
            cmd.append("-f")
        cmd.extend(["--tail", str(lines), service_lower])

        if follow:
            try:
                import subprocess
                subprocess.run(cmd, cwd=str(ROOT_DIR))
            except KeyboardInterrupt:
                pass
            return
        else:
            code, out, err = run_command_capture(cmd)
            if code == 0:
                _filter_and_print_lines(out.splitlines(), level, search, request_id)
            else:
                print_error(f"Failed to fetch container logs for {service_lower}: {err}")
            return

    # File-based application logs
    log_dir = Path(settings.LOG_DIR)
    if not log_dir.is_absolute():
        log_dir = ROOT_DIR / log_dir

    if service_lower == "error":
        target_file = log_dir / "dwrms_error.log"
    else:
        target_file = log_dir / "dwrms_app.log"

    if not target_file.exists():
        print_warning(f"Log file not found at: {target_file}")
        # Try inspecting via docker compose
        print_warning(f"Falling back to 'docker compose logs {service_lower}'...")
        code, out, _ = run_command_capture(["docker", "compose", "-f", "docker-compose.prod.yml", "logs", "--tail", str(lines)])
        if out:
            _filter_and_print_lines(out.splitlines(), level, search, request_id)
        return

    print_header(f"LOG STREAM: {target_file.name} (Last {lines} lines)")

    if follow:
        import time
        with target_file.open("r", encoding="utf-8", errors="replace") as f:
            f.seek(0, os.SEEK_END)
            try:
                while True:
                    line = f.readline()
                    if line:
                        _filter_and_print_lines([line.rstrip()], level, search, request_id)
                    else:
                        time.sleep(0.5)
            except KeyboardInterrupt:
                pass
        return

    # Read tail
    with target_file.open("r", encoding="utf-8", errors="replace") as f:
        all_lines = f.readlines()
        tail_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
        _filter_and_print_lines([l.rstrip() for l in tail_lines], level, search, request_id)


def _filter_and_print_lines(lines: list[str], level: str = None, search: str = None, request_id: str = None):
    level_order = {"DEBUG": 10, "INFO": 20, "WARNING": 30, "WARN": 30, "ERROR": 40, "CRITICAL": 50}
    min_level_val = level_order.get(level.upper(), 0) if level else 0

    for line in lines:
        if not line.strip():
            continue

        # Filter by request ID
        if request_id and request_id not in line:
            continue

        # Filter by search string
        if search and not re.search(search, line, re.IGNORECASE):
            continue

        # Filter by log level
        if level:
            match_found = False
            for lvl_name, lvl_val in level_order.items():
                if f'"{lvl_name}"' in line or f'[{lvl_name}]' in line or f' {lvl_name} ' in line:
                    if lvl_val >= min_level_val:
                        match_found = True
                    break
            if not match_found:
                continue

        # Syntax color output
        if '"level": "ERROR"' in line or "[ERROR]" in line or "ERROR" in line:
            click.secho(line, fg="red")
        elif '"level": "WARNING"' in line or "[WARN]" in line:
            click.secho(line, fg="yellow")
        elif '"level": "INFO"' in line or "[INFO]" in line:
            click.secho(line, fg="white")
        else:
            click.secho(line, fg="bright_black")
