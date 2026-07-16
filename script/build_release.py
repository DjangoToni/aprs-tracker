"""Build deterministic HACS and manual-install release archives."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import tomllib
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

ROOT = Path(__file__).parents[1]
COMPONENT = ROOT / "custom_components" / "aprs_monitor"
BLUEPRINTS = ROOT / "blueprints" / "automation" / "aprs_monitor"
EXAMPLES = ROOT / "examples"
FIXED_TIMESTAMP = (2026, 1, 1, 0, 0, 0)
VERSION_PATTERN = re.compile(r'^VERSION = "([^"]+)"$', re.MULTILINE)


def integration_version() -> str:
    """Return the synchronized project version or fail with a useful error."""
    manifest = json.loads((COMPONENT / "manifest.json").read_text(encoding="utf-8"))
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    const_source = (COMPONENT / "const.py").read_text(encoding="utf-8")
    const_match = VERSION_PATTERN.search(const_source)
    if const_match is None:
        raise ValueError("Could not find VERSION in const.py")

    versions = {
        "manifest.json": manifest["version"],
        "pyproject.toml": pyproject["project"]["version"],
        "const.py": const_match.group(1),
    }
    if len(set(versions.values())) != 1:
        details = ", ".join(f"{name}={version}" for name, version in versions.items())
        raise ValueError(f"Project versions do not match: {details}")
    return manifest["version"]


def component_files() -> list[Path]:
    """Return sorted distributable files without local caches."""
    return sorted(
        path
        for path in COMPONENT.rglob("*")
        if path.is_file()
        and "__pycache__" not in path.parts
        and path.suffix not in {".pyc", ".pyo"}
    )


def _write_member(archive: ZipFile, source: Path, archive_name: str) -> None:
    """Write one deterministic archive member."""
    info = ZipInfo(archive_name, FIXED_TIMESTAMP)
    info.compress_type = ZIP_DEFLATED
    info.external_attr = 0o100644 << 16
    archive.writestr(info, source.read_bytes(), compresslevel=9)


def _write_component_archive(path: Path, prefix: str) -> None:
    """Write one reproducible integration ZIP archive."""
    with ZipFile(path, "w", compression=ZIP_DEFLATED, compresslevel=9) as archive:
        for source in component_files():
            relative = source.relative_to(COMPONENT).as_posix()
            _write_member(archive, source, f"{prefix}{relative}")


def _write_extras_archive(path: Path) -> None:
    """Write blueprints and dashboard examples for extraction into /config."""
    with ZipFile(path, "w", compression=ZIP_DEFLATED, compresslevel=9) as archive:
        for source in sorted(BLUEPRINTS.glob("*.yaml")):
            _write_member(
                archive,
                source,
                f"blueprints/automation/aprs_monitor/{source.name}",
            )
        for source in sorted(EXAMPLES.iterdir()):
            if source.is_file():
                _write_member(archive, source, f"aprs_monitor_examples/{source.name}")


def build_release(output_dir: Path, expected_version: str | None = None) -> list[Path]:
    """Build HACS and direct-folder archives plus their checksums."""
    version = integration_version()
    if expected_version is not None and version != expected_version.removeprefix("v"):
        raise ValueError(
            f"Release tag {expected_version!r} does not match project version {version!r}"
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    hacs_archive = output_dir / "aprs_monitor.zip"
    manual_archive = output_dir / f"aprs_monitor-{version}-direct-folder.zip"
    extras_archive = output_dir / f"aprs_monitor-{version}-extras.zip"
    _write_component_archive(hacs_archive, "")
    _write_component_archive(manual_archive, "aprs_monitor/")
    _write_extras_archive(extras_archive)

    archives = [hacs_archive, manual_archive, extras_archive]
    checksum_lines = [
        f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}" for path in archives
    ]
    checksums = output_dir / "SHA256SUMS"
    checksums.write_text("\n".join(checksum_lines) + "\n", encoding="utf-8")
    return [*archives, checksums]


def main() -> None:
    """Run the release builder from the command line."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=ROOT / "dist")
    parser.add_argument("--expected-version")
    args = parser.parse_args()
    for path in build_release(args.output_dir, args.expected_version):
        print(path)


if __name__ == "__main__":
    main()
