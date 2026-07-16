"""Validate public project metadata with Home Assistant's YAML loader."""

from pathlib import Path

from homeassistant.util.yaml import load_yaml

ROOT = Path(__file__).parents[3]


def test_github_issue_forms_are_valid_yaml_and_require_privacy_confirmation() -> None:
    issue_dir = ROOT / ".github" / "ISSUE_TEMPLATE"
    bug = load_yaml(str(issue_dir / "bug_report.yml"))
    feature = load_yaml(str(issue_dir / "feature_request.yml"))
    config = load_yaml(str(issue_dir / "config.yml"))
    assert bug["name"] == "Fehlerbericht"
    assert any(item.get("id") == "privacy" for item in bug["body"])
    assert feature["name"] == "Funktionswunsch"
    assert config["blank_issues_enabled"] is False


def test_final_release_documentation_exists() -> None:
    for relative in (
        "docs/README.de.md",
        "docs/entity-contract.md",
        "docs/release-checklist.md",
        "docs/upgrade.de.md",
        "SECURITY.md",
    ):
        assert (ROOT / relative).is_file()
