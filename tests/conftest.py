"""Test bootstrap for fast unit tests and optional Home Assistant runtime tests."""

import sys
from importlib.util import find_spec
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))

HAS_HOME_ASSISTANT = find_spec("homeassistant") is not None

if not HAS_HOME_ASSISTANT:
    collect_ignore = [str(Path(__file__).parent / "components" / "aprs_monitor")]

    COMPONENT_PATH = ROOT / "custom_components" / "aprs_monitor"
    package = ModuleType("custom_components.aprs_monitor")
    package.__path__ = [str(COMPONENT_PATH)]  # type: ignore[attr-defined]
    sys.modules.setdefault("custom_components.aprs_monitor", package)

    aiohttp = ModuleType("aiohttp")
    aiohttp.ClientError = type("ClientError", (Exception,), {})
    aiohttp.ClientSession = object
    sys.modules.setdefault("aiohttp", aiohttp)
