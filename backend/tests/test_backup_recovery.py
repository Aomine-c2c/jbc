import os
import json
import shutil
import hashlib
import tarfile
import tempfile
import pytest
from pathlib import Path
from click.testing import CliRunner

from app.cli.main import ops_group
from app.cli.backup import _get_backup_dir, _prune_archives
from app.core.config import settings


@pytest.fixture
def clean_backup_env(tmp_path):
    """Isolates backup directory for test execution."""
    old_backup_dir = settings.BACKUP_DIR
    settings.BACKUP_DIR = str(tmp_path / "backups")
    os.makedirs(settings.BACKUP_DIR, exist_ok=True)
    yield tmp_path / "backups"
    settings.BACKUP_DIR = old_backup_dir


def test_backup_create_and_manifest_spec(clean_backup_env):
    """Verifies ops backup create produces standardized manifest and companion sha256 digest."""
    runner = CliRunner()
    result = runner.invoke(ops_group, ["backup", "create", "--note", "Automated pytest verification"])
    assert result.exit_code == 0, result.output
    assert "Disaster recovery snapshot created" in result.output
    assert "VERIFIED_SHA256" in result.output

    # Check generated files
    archives = list(clean_backup_env.glob("dwrms_backup_*.tar.gz"))
    assert len(archives) == 1
    archive_path = archives[0]

    # Verify sha256 companion file
    sha_file = clean_backup_env / f"{archive_path.name}.sha256"
    assert sha_file.exists()
    expected_sha = sha_file.read_text().split()[0].strip()
    actual_sha = hashlib.sha256(archive_path.read_bytes()).hexdigest()
    assert expected_sha == actual_sha

    # Inspect manifest inside archive
    with tarfile.open(archive_path, "r:gz") as tar:
        members = tar.getnames()
        assert any("manifest.json" in m for m in members)
        assert any("database.sql" in m for m in members)
        assert any("config.json" in m for m in members)

        m_file = tar.extractfile("manifest.json")
        assert m_file is not None
        manifest = json.loads(m_file.read().decode("utf-8"))
        assert "backup_id" in manifest
        assert manifest["backup_type"] == "MANUAL_ADMIN"
        assert manifest["status"] == "VERIFIED"
        assert manifest["integrity_status"] == "VERIFIED_SHA256"
        assert manifest["retention_days"] == 30


def test_backup_verify_command(clean_backup_env):
    """Verifies ops backup verify correctly validates intact archives and catches corruption."""
    runner = CliRunner()
    runner.invoke(ops_group, ["backup", "create"])
    archives = list(clean_backup_env.glob("dwrms_backup_*.tar.gz"))
    assert len(archives) == 1
    arc_name = archives[0].name

    # 1. Valid verification
    v_res = runner.invoke(ops_group, ["backup", "verify", arc_name])
    assert v_res.exit_code == 0, v_res.output
    assert "SHA-256 Digest Matched" in v_res.output
    assert "VERIFIED" in v_res.output

    # 2. Corrupt archive sha
    sha_file = clean_backup_env / f"{arc_name}.sha256"
    sha_file.write_text("invalid_hash_corrupted  archive\n")
    corrupt_res = runner.invoke(ops_group, ["backup", "verify", arc_name])
    assert corrupt_res.exit_code != 0
    assert "Integrity Check Failed" in corrupt_res.output


def test_backup_retention_pruning(clean_backup_env):
    """Verifies backup retention policy pruning preserves baseline snapshots while removing expired ones."""
    # Create 4 dummy archive files with older modification times
    for i in range(4):
        arc = clean_backup_env / f"dwrms_backup_2026010{i}_000000.tar.gz"
        arc.write_bytes(b"dummy archive data")
        sha = clean_backup_env / f"{arc.name}.sha256"
        sha.write_text("dummy_hash")
        # Set mtime to 60 days ago
        past_time = 1000000 + (i * 1000)
        os.utime(arc, (past_time, past_time))

    assert len(list(clean_backup_env.glob("*.tar.gz"))) == 4

    # Run prune
    _prune_archives(clean_backup_env, retention_days=30, verbose=True)

    # Must preserve at least the 2 newest baseline snapshots
    remaining = list(clean_backup_env.glob("*.tar.gz"))
    assert len(remaining) == 2


def test_restore_with_pre_snapshot_safeguard(clean_backup_env):
    """Verifies ops restore creates pre-restore safety snapshot before applying changes."""
    runner = CliRunner()
    # Create valid backup
    runner.invoke(ops_group, ["backup", "create", "--note", "Baseline target"])
    archives = sorted(clean_backup_env.glob("dwrms_backup_*.tar.gz"))
    target_arc = archives[0].name

    # Execute restore with --yes (bypasses prompt)
    restore_res = runner.invoke(ops_group, ["restore", target_arc, "-y"])
    assert restore_res.exit_code == 0, restore_res.output
    assert "Safety pre-restore snapshot created" in restore_res.output
    assert "RESTORATION COMPLETE" in restore_res.output

    # Verify that a pre-restore safety archive was generated
    safety_archives = list(clean_backup_env.glob("dwrms_prerestore_safety_*.tar.gz"))
    assert len(safety_archives) >= 1
