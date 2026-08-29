import click
from typing import Optional

from app.cli.utils import (
    print_header,
    print_table,
    print_success,
    print_error,
    print_warning,
    mask_secret,
    load_env_dict,
    update_env_file,
    ENV_FILE,
)

SENSITIVE_KEYS = {
    "SECRET_KEY",
    "DB_PASSWORD",
    "POSTGRES_PASSWORD",
    "LDAP_BIND_PASSWORD",
}


@click.group("configure")
def configure_group():
    """Inspect and modify platform configuration settings."""
    pass


@configure_group.command("list")
@click.option("--show-secrets", is_flag=True, help="Display plaintext secrets (CAUTION)")
def list_config(show_secrets):
    """List all platform configuration keys and values."""
    print_header("DWRMS ENVIRONMENT CONFIGURATION")
    env = load_env_dict()

    if not env:
        print_warning(f"No configuration file found at {ENV_FILE}. Run 'ops setup' first.")
        return

    rows = []
    for k, v in sorted(env.items()):
        if k in SENSITIVE_KEYS and not show_secrets:
            display_val = mask_secret(v)
        else:
            display_val = v
        rows.append([k, display_val])

    print_table(["Configuration Key", "Configured Value"], rows)
    click.echo(f"\nConfiguration file: {ENV_FILE}\n")


@configure_group.command("get")
@click.argument("key")
@click.option("--show-secret", is_flag=True, help="Reveal plaintext secret value")
def get_config(key, show_secret):
    """Get the value of a specific configuration setting."""
    env = load_env_dict()
    key_upper = key.upper()
    val = env.get(key_upper) or env.get(key)

    if val is None:
        print_error(f"Configuration key '{key}' is not set.")
        return

    if key_upper in SENSITIVE_KEYS and not show_secret:
        click.echo(mask_secret(val))
    else:
        click.echo(val)


@configure_group.command("set")
@click.argument("key")
@click.argument("value")
def set_config(key, value):
    """Set or update a configuration key in .env."""
    key_upper = key.upper()
    update_env_file({key_upper: value})
    print_success(f"Updated {key_upper} in {ENV_FILE}")
    print_warning("If services are running, reload them with 'ops server reload' for changes to take effect.")


@configure_group.command("validate")
def validate_config():
    """Validate configuration integrity and required parameters."""
    print_header("CONFIGURATION INTEGRITY AUDIT")
    env = load_env_dict()
    errors = 0
    warnings = 0

    # 1. Check SECRET_KEY
    sk = env.get("SECRET_KEY", "")
    if not sk or sk.startswith("change_this") or sk.startswith("dev-secret"):
        if env.get("ENVIRONMENT") == "production":
            print_error("SECRET_KEY is using a default or insecure value in production.")
            errors += 1
        else:
            print_warning("SECRET_KEY is using a development default.")
            warnings += 1
    elif len(sk) < 32:
        print_warning("SECRET_KEY is shorter than 32 characters.")
        warnings += 1
    else:
        print_success("SECRET_KEY is valid and secure.")

    # 2. Check Database Settings
    db_engine = env.get("DB_ENGINE", "postgresql")
    if db_engine not in ("postgresql", "mysql", "sqlite"):
        print_error(f"Invalid DB_ENGINE: '{db_engine}'. Allowed: postgresql, mysql, sqlite.")
        errors += 1
    else:
        print_success(f"Database engine configured: {db_engine}")

    # 3. Check Authoritative Domain
    frontend_url = env.get("FRONTEND_URL", "")
    if not frontend_url or not (frontend_url.startswith("http://") or frontend_url.startswith("https://")):
        print_error("FRONTEND_URL must be a valid HTTP/HTTPS URL.")
        errors += 1
    else:
        print_success(f"Authoritative domain: {frontend_url}")

    # 4. Check Storage Path
    storage_path = env.get("STORAGE_PATH", "")
    if not storage_path:
        print_error("STORAGE_PATH is not configured.")
        errors += 1
    else:
        print_success(f"Storage path: {storage_path}")

    click.echo("")
    if errors == 0:
        print_success(f"Configuration audit passed ({warnings} warnings, 0 errors).")
    else:
        print_error(f"Configuration audit failed with {errors} errors.")
        exit(1)
