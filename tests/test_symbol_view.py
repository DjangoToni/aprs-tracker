"""Tests for bundled APRS symbol rendering."""

import hashlib
from io import BytesIO
from pathlib import Path

from PIL import Image

from custom_components.aprs_monitor.symbol_view import AprsSymbolRenderer

ASSET_PATH = Path(__file__).parents[1] / "custom_components" / "aprs_monitor" / "aprs_symbol_assets"


def _image(png: bytes | None) -> Image.Image:
    assert png is not None
    return Image.open(BytesIO(png)).convert("RGBA")


def test_renders_real_primary_and_alternate_symbols() -> None:
    renderer = AprsSymbolRenderer(ASSET_PATH)
    primary_car = _image(renderer.render("2f-3e"))
    alternate_bicycle = _image(renderer.render("5c-62"))

    assert primary_car.size == (64, 64)
    assert primary_car.getbbox() is not None
    assert hashlib.sha256(primary_car.tobytes()).hexdigest() == (
        "85e6fe5b2441f7152c81eac3e777d091dd53c2a99b98dd23ba181222d331a5e8"
    )
    assert alternate_bicycle.getbbox() is not None
    assert primary_car.tobytes() != alternate_bicycle.tobytes()


def test_applies_overlay_graphic_to_alternate_symbol() -> None:
    renderer = AprsSymbolRenderer(ASSET_PATH)
    alternate_car = _image(renderer.render("5c-3e"))
    overlaid_car = _image(renderer.render("41-3e"))

    assert alternate_car.tobytes() != overlaid_car.tobytes()


def test_rejects_malformed_or_nonprintable_codes() -> None:
    renderer = AprsSymbolRenderer(ASSET_PATH)
    assert renderer.render("../../secret") is None
    assert renderer.render("00-3e") is None
    assert renderer.render("2f-7f") is None
    assert renderer.render("2f-ff") is None
