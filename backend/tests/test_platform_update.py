import pytest
from click.testing import CliRunner

from app.cli.main import ops_group
from app.core.config import settings
from app.core.version import version_manager, parse_semver


def test_semver_parser():
    """Verifies semver string parsing for various formats."""
    assert parse_semver("v2.9.0") == (2, 9, 0)
    assert parse_semver("2.9.1") == (2, 9, 1)
    assert parse_semver("v2.0.0-beta") == (2, 0, 0)
    assert parse_semver("invalid") == (0, 0, 0)


def test_version_matrix():
    """Verifies version matrix reports all multi-tier components."""
    matrix = version_manager.get_version_matrix()
    assert matrix.server_version == "v2.9.0"
    assert matrix.api_version == "v1"
    assert matrix.db_schema_version == "2026.08.28.01"
    assert matrix.web_client_version == "v2.9.0"
    assert matrix.desktop_client_version == "v2.9.0"
    assert matrix.min_supported_client_version == "v2.0.0"
    assert len(matrix.components) >= 5


def test_client_compatibility():
    """Verifies connecting client versions are checked against minimum threshold."""
    # Compatible versions
    ok, msg = version_manager.is_client_compatible("v2.9.0")
    assert ok is True

    ok, msg = version_manager.is_client_compatible("v2.0.0")
    assert ok is True

    ok, msg = version_manager.is_client_compatible("v2.1.4")
    assert ok is True

    # Incompatible older version
    ok, msg = version_manager.is_client_compatible("v1.5.0")
    assert ok is False
    assert "below minimum supported version" in msg

    # Legacy header omission
    ok, msg = version_manager.is_client_compatible("")
    assert ok is True


def test_ops_update_matrix_cli():
    """Verifies ops update matrix outputs complete component table."""
    runner = CliRunner()
    result = runner.invoke(ops_group, ["update", "matrix"])
    assert result.exit_code == 0
    assert "DWRMS AUTHORITATIVE VERSION MATRIX" in result.output
    assert "Server Platform Core" in result.output
    assert "Backend REST API" in result.output
    assert "Database Schema" in result.output
    assert "Web Client" in result.output
    assert "Desktop Client" in result.output


def test_ops_update_check_cli():
    """Verifies ops update check queries approved release channel."""
    runner = CliRunner()
    result = runner.invoke(ops_group, ["update", "check"])
    assert result.exit_code == 0
    assert "CHECKING FOR PLATFORM UPDATES" in result.output
    assert "enterprise_lts" in result.output


def test_ops_update_apply_pipeline(tmp_path):
    """Verifies ops update apply runs the 8-step pipeline with pre-upgrade snapshot."""
    old_backup_dir = settings.BACKUP_DIR
    settings.BACKUP_DIR = str(tmp_path / "backups")
    runner = CliRunner()

    result = runner.invoke(ops_group, ["update", "apply", "--yes", "--skip-git", "--target-version", "v2.9.0"])
    settings.BACKUP_DIR = old_backup_dir

    assert result.exit_code == 0, result.output
    assert "EXECUTING CONTROLLED UPDATE PIPELINE" in result.output
    assert "[Step 1/8]" in result.output
    assert "[Step 3/8] Creating pre-upgrade disaster recovery snapshot" in result.output
    assert "[Step 5/8] Applying database schema migrations" in result.output
    assert "[Step 8/8]" in result.output
    assert "PLATFORM SUCCESSFULLY UPDATED" in result.output
