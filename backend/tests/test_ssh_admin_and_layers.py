import pytest
from click.testing import CliRunner
from app.cli.main import ops_group


@pytest.fixture
def runner():
    return CliRunner()


def test_cli_ops_version(runner):
    result = runner.invoke(ops_group, ["--version"])
    assert result.exit_code == 0
    assert "DWRMS Ops CLI" in result.output
    assert "v2." in result.output


def test_cli_status_non_interactive(runner):
    """Verifies that 'ops status' runs cleanly in non-interactive SSH sessions."""
    result = runner.invoke(ops_group, ["status"])
    assert result.exit_code == 0
    assert "SYSTEM STATUS" in result.output or "PLATFORM" in result.output
    assert "APPLICATION" in result.output or "HEALTHY" in result.output


def test_cli_health_probe(runner):
    """Verifies that 'ops health' runs cleanly over CLI/SSH."""
    result = runner.invoke(ops_group, ["health"])
    assert result.exit_code == 0
    assert "HEALTH" in result.output or "OK" in result.output or "passed" in result.output.lower()


def test_cli_diagnostics(runner):
    """Verifies hardware and pool diagnostics output."""
    result = runner.invoke(ops_group, ["diagnostics"])
    assert result.exit_code == 0
    assert "DIAGNOSTICS" in result.output or "CPU" in result.output or "Memory" in result.output


def test_cli_backup_create_and_list(runner):
    """Verifies that disaster recovery snapshots can be created and listed via CLI/SSH."""
    # 1. Create backup
    create_res = runner.invoke(ops_group, ["backup", "create", "--note", "Pytest SSH Automation Snapshot"])
    assert create_res.exit_code == 0
    assert "SUCCESS" in create_res.output or "created" in create_res.output.lower()

    # 2. List backups
    list_res = runner.invoke(ops_group, ["backup", "list"])
    assert list_res.exit_code == 0
    assert "BACKUP ARCHIVES" in list_res.output or "tar.gz" in list_res.output


def test_cli_network_info(runner):
    """Verifies network and domain inspection over CLI."""
    result = runner.invoke(ops_group, ["network"])
    assert result.exit_code == 0
    assert "NETWORK" in result.output or "Domain" in result.output or "Port" in result.output
