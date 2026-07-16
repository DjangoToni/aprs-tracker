"""Ensure every supported language exposes the complete translation contract."""

import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
COMPONENT = ROOT / "custom_components" / "aprs_monitor"


def _key_paths(value, prefix=()):
    paths = set()
    if isinstance(value, dict):
        for key, child in value.items():
            path = (*prefix, key)
            paths.add(path)
            paths.update(_key_paths(child, path))
    return paths


def test_source_english_and_german_translation_trees_match() -> None:
    source = json.loads((COMPONENT / "strings.json").read_text(encoding="utf-8"))
    english = json.loads(
        (COMPONENT / "translations" / "en.json").read_text(encoding="utf-8")
    )
    german = json.loads(
        (COMPONENT / "translations" / "de.json").read_text(encoding="utf-8")
    )
    assert _key_paths(source) == _key_paths(english) == _key_paths(german)
