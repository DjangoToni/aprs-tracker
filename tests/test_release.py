"""Tests for deterministic release packaging."""

import hashlib
from zipfile import ZipFile

from script.build_release import build_release, integration_version


def test_project_versions_are_synchronized() -> None:
    assert integration_version() == "1.2.0"


def test_builds_hacs_and_manual_archives(tmp_path) -> None:
    paths = build_release(tmp_path, "v1.2.0")
    hacs_archive, manual_archive, extras_archive, checksums = paths

    with ZipFile(hacs_archive) as archive:
        names = archive.namelist()
        assert "manifest.json" in names
        assert "brand/icon.png" in names
        assert not any("__pycache__" in name for name in names)

    with ZipFile(manual_archive) as archive:
        names = archive.namelist()
        assert "aprs_monitor/manifest.json" in names
        assert "aprs_monitor/brand/icon@2x.png" in names
        for name in names:
            if name.endswith(".py"):
                compile(archive.read(name), name, "exec")

    with ZipFile(extras_archive) as archive:
        names = archive.namelist()
        assert "blueprints/automation/aprs_monitor/station_activity_actions.yaml" in names
        assert "blueprints/automation/aprs_monitor/api_connection_actions.yaml" in names
        assert "blueprints/automation/aprs_monitor/zone_activity_actions.yaml" in names
        assert "aprs_monitor_examples/dashboard.yaml" in names
        assert "aprs_monitor_examples/README.md" in names

    checksum_text = checksums.read_text(encoding="utf-8")
    assert hashlib.sha256(hacs_archive.read_bytes()).hexdigest() in checksum_text
    assert hashlib.sha256(manual_archive.read_bytes()).hexdigest() in checksum_text
    assert hashlib.sha256(extras_archive.read_bytes()).hexdigest() in checksum_text


def test_release_archives_are_reproducible(tmp_path) -> None:
    first = build_release(tmp_path)
    first_hashes = [hashlib.sha256(path.read_bytes()).hexdigest() for path in first[:3]]
    second = build_release(tmp_path)
    second_hashes = [hashlib.sha256(path.read_bytes()).hexdigest() for path in second[:3]]
    assert first_hashes == second_hashes
