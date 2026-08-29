import os
import sys
import subprocess
import shutil
from pathlib import Path
from typing import Optional, Any
import click

# Resolve platform paths
ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
ENV_FILE = ROOT_DIR / ".env"


def _safe_str(val: Any) -> str:
    """Sanitizes text to ASCII-safe representation for cross-platform terminals."""
    if val is None:
        return "-"
    s = str(val)
    # Replace common unicode chars
    s = s.replace("\u2014", "--").replace("\u2013", "-").replace("\u2019", "'").replace("\u201c", '"').replace("\u201d", '"')
    try:
        s.encode(sys.stdout.encoding or "utf-8")
        return s
    except UnicodeEncodeError:
        return s.encode("ascii", errors="replace").decode("ascii")


def mask_secret(val: Optional[str], show_chars: int = 2) -> str:
    """Masks sensitive credentials for secure terminal output."""
    if not val:
        return "<not set>"
    if len(val) <= show_chars * 2:
        return "******"
    return f"{val[:show_chars]}******{val[-show_chars:]}"


def print_header(title: str):
    """Prints a styled CLI section header."""
    click.echo("")
    click.secho("=" * 70, fg="blue", bold=True)
    click.secho(f"  {_safe_str(title)}", fg="cyan", bold=True)
    click.secho("=" * 70, fg="blue", bold=True)


def print_success(msg: str):
    click.secho(f"  [OK] {_safe_str(msg)}", fg="green", bold=True)


def print_error(msg: str):
    click.secho(f"  [ERROR] {_safe_str(msg)}", fg="red", bold=True, err=True)


def print_warning(msg: str):
    click.secho(f"  [WARN] {_safe_str(msg)}", fg="yellow", bold=True)


def print_info(msg: str):
    click.secho(f"  [INFO] {_safe_str(msg)}", fg="blue")


def print_table(headers: list[str], rows: list[list[Any]], title: Optional[str] = None):
    """Renders a clean ASCII table formatted for remote SSH terminals."""
    if title:
        click.secho(f"\n--- {_safe_str(title)} ---", fg="cyan", bold=True)

    if not rows:
        click.secho("  (No records found)", fg="bright_black")
        return

    # Calculate column widths
    safe_headers = [_safe_str(h) for h in headers]
    safe_rows = [[_safe_str(val) for val in row] for row in rows]

    col_widths = [len(h) for h in safe_headers]
    for row in safe_rows:
        for i, val in enumerate(row):
            col_widths[i] = max(col_widths[i], len(val))

    # Print header
    header_line = "  ".join(f"{safe_headers[i]:<{col_widths[i]}}" for i in range(len(safe_headers)))
    separator_line = "  ".join("-" * col_widths[i] for i in range(len(safe_headers)))
    
    click.secho(header_line, fg="cyan", bold=True)
    click.secho(separator_line, fg="bright_black")

    # Print rows
    for row in safe_rows:
        formatted_row = [f"{row[i]:<{col_widths[i]}}" for i in range(len(row))]
        click.echo("  ".join(formatted_row))


def run_command_capture(cmd: list[str], cwd: Optional[str] = None) -> tuple[int, str, str]:
    """Executes a system command and returns (exit_code, stdout, stderr)."""
    try:
        proc = subprocess.run(
            cmd,
            cwd=cwd or str(ROOT_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=False,
        )
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
    except Exception as e:
        return 1, "", str(e)


def load_env_dict(path: Optional[Path] = None) -> dict[str, str]:
    """Loads key-value pairs from an env file."""
    target_path = path or ENV_FILE
    result = {}
    if not target_path.exists():
        return result

    for line in target_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            k, v = line.split("=", 1)
            result[k.strip()] = v.strip().strip('"').strip("'")
    return result


def update_env_file(updates: dict[str, str], path: Optional[Path] = None):
    """Updates key-value pairs in an env file while preserving existing lines."""
    target_path = path or ENV_FILE
    existing_lines = target_path.read_text(encoding="utf-8").splitlines() if target_path.exists() else []

    updated_keys = set()
    new_lines = []

    for line in existing_lines:
        trimmed = line.strip()
        if trimmed and not trimmed.startswith("#") and "=" in trimmed:
            k, _ = trimmed.split("=", 1)
            k = k.strip()
            if k in updates:
                new_lines.append(f'{k}="{updates[k]}"')
                updated_keys.add(k)
                continue
        new_lines.append(line)

    for k, v in updates.items():
        if k not in updated_keys:
            new_lines.append(f'{k}="{v}"')

    target_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
