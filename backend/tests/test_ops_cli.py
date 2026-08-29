import pytest
from click.testing import CliRunner
from app.cli.main import ops_group


def test_ops_help():
    runner = CliRunner()
    result = runner.invoke(ops_group, ["--help"])
    assert result.exit_code == 0
    assert "setup" in result.output
    assert "status" in result.output
    assert "health" in result.output
    assert "backup" in result.output
    assert "restore" in result.output
    assert "users" in result.output
    assert "configure" in result.output


def test_ops_version():
    runner = CliRunner()
    result = runner.invoke(ops_group, ["--version"])
    assert result.exit_code == 0
    assert "v2." in result.output


def test_ops_configure_list():
    runner = CliRunner()
    result = runner.invoke(ops_group, ["configure", "list"])
    assert result.exit_code == 0
    assert "ENVIRONMENT" in result.output
    # Ensure sensitive credentials are masked
    assert "******" in result.output


def test_ops_backup_list():
    runner = CliRunner()
    result = runner.invoke(ops_group, ["backup", "list"])
    assert result.exit_code == 0
    assert "AVAILABLE DWRMS BACKUP SNAPSHOTS" in result.output


def test_ops_diagnostics():
    runner = CliRunner()
    result = runner.invoke(ops_group, ["diagnostics"])
    assert result.exit_code == 0
    assert "DWRMS NON-SENSITIVE DIAGNOSTIC REPORT" in result.output


def test_ops_network():
    runner = CliRunner()
    result = runner.invoke(ops_group, ["network"])
    assert result.exit_code == 0
    assert "DWRMS NETWORK TOPOLOGY" in result.output
