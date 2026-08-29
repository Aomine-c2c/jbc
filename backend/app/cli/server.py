import sys
import click

from app.cli.utils import (
    print_header,
    print_success,
    print_error,
    print_warning,
    print_info,
    run_command_capture,
    ROOT_DIR,
)


@click.group("server")
def server_group():
    """Control platform server lifecycle (start, stop, restart, reload)."""
    pass


@server_group.command("start")
@click.option("--build", is_flag=True, help="Rebuild container images before starting")
def start_server(build):
    """Start all DWRMS platform containers and background services."""
    print_header("STARTING DWRMS PLATFORM SERVICES")
    cmd = ["docker", "compose", "-f", "docker-compose.prod.yml", "up", "-d"]
    if build:
        cmd.append("--build")

    code, out, err = run_command_capture(cmd)
    if code == 0:
        print_success("Platform stack launched successfully.")
        click.echo("Run 'ops status' or 'ops health' to verify readiness.\n")
    else:
        print_error(f"Failed to start server stack: {err}")
        sys.exit(1)


@server_group.command("stop")
@click.option("--yes", "-y", is_flag=True, help="Bypass confirmation prompt")
def stop_server(yes):
    """Stop all DWRMS platform containers."""
    if not yes:
        if not click.confirm("Are you sure you want to stop all DWRMS platform services?"):
            print_warning("Operation cancelled.")
            return

    print_header("STOPPING DWRMS PLATFORM SERVICES")
    code, out, err = run_command_capture(["docker", "compose", "-f", "docker-compose.prod.yml", "down"])
    if code == 0:
        print_success("Platform services stopped.")
    else:
        print_error(f"Failed to stop services: {err}")


@server_group.command("restart")
@click.argument("service", required=False)
def restart_server(service):
    """Restart all or a specific platform service (e.g. ops server restart backend)."""
    target = service or "all services"
    print_header(f"RESTARTING: {target.upper()}")

    cmd = ["docker", "compose", "-f", "docker-compose.prod.yml", "restart"]
    if service:
        cmd.append(service)

    code, out, err = run_command_capture(cmd)
    if code == 0:
        print_success(f"{target.capitalize()} restarted.")
    else:
        print_error(f"Failed to restart {target}: {err}")


@server_group.command("reload")
def reload_server():
    """Apply updated configuration and reload containers with zero downtime."""
    print_header("RELOADING DWRMS CONTAINER STACK")
    cmd = ["docker", "compose", "-f", "docker-compose.prod.yml", "up", "-d", "--remove-orphans"]
    code, out, err = run_command_capture(cmd)
    if code == 0:
        print_success("Container configuration reloaded.")
    else:
        print_error(f"Failed to reload containers: {err}")


@server_group.command("ps")
def ps_server():
    """List running platform containers."""
    code, out, err = run_command_capture(["docker", "compose", "-f", "docker-compose.prod.yml", "ps"])
    if out:
        click.echo(out)
    else:
        click.echo("No active containers found.")
