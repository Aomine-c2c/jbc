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


def get_compose_file() -> Path:
    """Returns the primary production or development docker compose file."""
    candidates = [
        ROOT_DIR / "docker-compose.prod.yml",
        ROOT_DIR / "infrastructure" / "docker-compose.prod.yml",
        ROOT_DIR / "docker-compose.yml",
        ROOT_DIR / "infrastructure" / "docker-compose.yml",
    ]
    for c in candidates:
        if c.exists():
            return c
    return ROOT_DIR / "infrastructure" / "docker-compose.prod.yml"


def get_docker_cmd() -> list[str]:
    """Returns ['docker'] or ['sudo', 'docker'] if non-root user lacks socket permissions."""
    if os.name != "nt" and hasattr(os, "geteuid") and os.geteuid() != 0:
        res = subprocess.run(["docker", "ps"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if res.returncode != 0:
            return ["sudo", "docker"]
    return ["docker"]


def run_command_capture(cmd: list[str], cwd: Optional[str] = None) -> tuple[int, str, str]:
    """Executes a system command with automatic docker socket handling and compose context resolution."""
    final_cmd = list(cmd)
    if final_cmd and final_cmd[0] == "docker":
        prefix = get_docker_cmd()
        if prefix != ["docker"]:
            final_cmd = prefix + final_cmd[1:]

        # Normalize docker compose invocations
        if "compose" in final_cmd:
            comp_idx = final_cmd.index("compose")
            insertions = []
            if "--project-directory" not in final_cmd:
                insertions.extend(["--project-directory", str(ROOT_DIR)])
            if ENV_FILE.exists() and "--env-file" not in final_cmd:
                insertions.extend(["--env-file", str(ENV_FILE)])

            # If -f is used with a relative file, ensure it resolves
            if "-f" in final_cmd:
                f_idx = final_cmd.index("-f")
                if f_idx + 1 < len(final_cmd):
                    cf_val = final_cmd[f_idx + 1]
                    if not Path(cf_val).is_absolute() and not (Path(cwd or ROOT_DIR) / cf_val).exists():
                        final_cmd[f_idx + 1] = str(get_compose_file())
            elif "-f" not in final_cmd and len(final_cmd) > comp_idx + 1 and not final_cmd[comp_idx + 1].startswith("-"):
                insertions.extend(["-f", str(get_compose_file())])

            if insertions:
                final_cmd = final_cmd[:comp_idx + 1] + insertions + final_cmd[comp_idx + 1:]

    try:
        proc = subprocess.run(
            final_cmd,
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
