"""Validate APRS Monitor blueprints with Home Assistant's own schema."""

from pathlib import Path

import pytest
from homeassistant.components.automation.config import AUTOMATION_BLUEPRINT_SCHEMA
from homeassistant.components.blueprint.models import Blueprint
from homeassistant.util.yaml import load_yaml

ROOT = Path(__file__).parents[3]
BLUEPRINTS = ROOT / "blueprints" / "automation" / "aprs_monitor"


@pytest.mark.parametrize(
    "filename",
    ["station_activity_actions.yaml", "api_connection_actions.yaml"],
)
def test_automation_blueprint_passes_home_assistant_schema(filename: str) -> None:
    path = BLUEPRINTS / filename
    blueprint = Blueprint(
        load_yaml(str(path)),
        path=str(path),
        expected_domain="automation",
        schema=AUTOMATION_BLUEPRINT_SCHEMA,
    )
    assert blueprint.validate() is None
