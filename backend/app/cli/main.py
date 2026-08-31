import sys
from pathlib import Path
import click

# Ensure backend path is in sys.path
backend_dir = Path(__file__).resolve().parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.cli.setup import setup_command
from app.cli.install import install_command
from app.cli.configure import configure_group
from app.cli.status import status_command
from app.cli.health import health_command
from app.cli.logs import logs_command
from app.cli.diagnostics import diagnostics_command
from app.cli.backup import backup_group
from app.cli.restore import restore_command
from app.cli.users import users_group
from app.cli.network import network_command
from app.cli.server import server_group
from app.cli.update import update_group


@click.group(
    "ops",
    context_settings={"help_option_names": ["-h", "--help"]},
    help="Bikita Minerals DWRMS — Authoritative Platform Administration CLI.",
)
@click.version_option(version="v2.9.0", prog_name="DWRMS Ops CLI")
def ops_group():
    """Bikita Minerals Industrial Operations Platform Administration Suite."""
    pass


@ops_group.command("version")
def version_command():
    """Display platform version, database engine, schema version, and environment."""
    from app.cli.utils import print_header
    from app.core.config import settings
    print_header("BIKITA MINERALS DWRMS -- PLATFORM VERSION")
    click.echo(f"  Application:       {settings.APP_NAME}")
    click.echo(f"  Platform Version:  {settings.APP_VERSION}")
    click.echo(f"  API Version:       {settings.API_VERSION}")
    click.echo(f"  Database Engine:   {settings.DB_ENGINE.upper()}")
    click.echo(f"  Database Schema:   {settings.DB_SCHEMA_VERSION}")
    click.echo(f"  Environment:       {settings.ENVIRONMENT.upper()}")
    click.echo(f"  Release Channel:   {settings.UPDATE_CHANNEL}")
    click.echo(f"  Min Client:        {settings.MIN_SUPPORTED_CLIENT_VERSION}\n")


# Register Core Commands
ops_group.add_command(setup_command)
ops_group.add_command(install_command)
ops_group.add_command(configure_group)
ops_group.add_command(status_command)
ops_group.add_command(health_command)
ops_group.add_command(logs_command)
ops_group.add_command(diagnostics_command)
ops_group.add_command(backup_group)
ops_group.add_command(restore_command)
ops_group.add_command(users_group)
ops_group.add_command(network_command)
ops_group.add_command(server_group)
ops_group.add_command(update_group)
ops_group.add_command(version_command)


# ── Backward-compatible Aliases ──────────────────────────────

@ops_group.command("init-db", hidden=True)
def init_db_alias():
    """Alias for database table initialization."""
    from app.cli.setup import _provision_admin_user
    import asyncio
    from app.db.session import engine, Base
    import app.modules.iam.models  # noqa: F401
    import app.modules.fleet.models  # noqa: F401
    import app.modules.jobs.models  # noqa: F401
    import app.modules.approvals.models  # noqa: F401
    import app.modules.notifications.models  # noqa: F401

    async def _init():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        await engine.dispose()

    asyncio.run(_init())
    click.secho("[SUCCESS] Database tables initialized.", fg="green", bold=True)


@ops_group.command("migrate", hidden=True)
def migrate_alias():
    """Alias for Alembic migration."""
    import subprocess
    subprocess.run(["alembic", "upgrade", "head"], cwd=str(backend_dir))


@ops_group.command("seed", hidden=True)
def seed_alias():
    """Alias for baseline seeding."""
    import asyncio
    from seed import seed
    asyncio.run(seed())
    click.secho("[SUCCESS] Database seed complete.", fg="green", bold=True)


@ops_group.command("createsuperuser", hidden=True)
@click.option("--email", prompt="Administrator Email")
@click.option("--first-name", prompt="First Name", default="System")
@click.option("--last-name", prompt="Last Name", default="Administrator")
@click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True)
@click.option("--department", default="Maintenance")
def createsuperuser_alias(email, first_name, last_name, password, department):
    """Alias for user creation."""
    from app.cli.users import create_admin
    ctx = click.get_current_context()
    ctx.invoke(create_admin, email=email, first_name=first_name, last_name=last_name, password=password, department=department)


@ops_group.command("storage-verify", hidden=True)
def storage_verify_alias():
    """Alias for storage verification."""
    from app.core.storage import storage_manager
    storage_manager.init_storage()
    h = storage_manager.get_storage_health()
    click.secho(f"[SUCCESS] Storage verified: {h['path']} (Writable: {h['write_ok']})", fg="green")


def main():
    ops_group()


if __name__ == "__main__":
    main()
