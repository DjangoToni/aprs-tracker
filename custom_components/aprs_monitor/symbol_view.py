"""Serve real APRS symbol graphics for Home Assistant maps."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from secrets import compare_digest

from aiohttp import web
from homeassistant.components.http import HomeAssistantView
from homeassistant.core import HomeAssistant
from PIL import Image

from .aprs_symbols import decode_aprs_symbol_code

_CACHE_HEADERS = {"Cache-Control": "public, max-age=2592000"}
_CELL_SIZE = 64
_COLUMNS = 16
_FIRST_SYMBOL_CODE = ord("!")


class AprsSymbolRenderer:
    """Crop and combine APRS symbols from the bundled aprs.fi sprite tables."""

    def __init__(self, asset_path: Path) -> None:
        self._tables = tuple(
            Image.open(asset_path / f"aprs-symbols-64-{table_id}.png").convert("RGBA").copy()
            for table_id in range(3)
        )
        self._cache: dict[str, bytes] = {}

    def render(self, code: str) -> bytes | None:
        """Return one transparent PNG for a validated APRS symbol code."""
        if cached := self._cache.get(code):
            return cached
        decoded = decode_aprs_symbol_code(code)
        if decoded is None:
            return None
        table, symbol = decoded
        table_id = 0 if table == "/" else 1
        image = self._crop(table_id, symbol)
        if table not in {"/", "\\"}:
            image.alpha_composite(self._crop(2, table))

        output = BytesIO()
        image.save(output, format="PNG", optimize=True)
        png = output.getvalue()
        if len(self._cache) >= 512:
            self._cache.pop(next(iter(self._cache)))
        self._cache[code] = png
        return png

    def _crop(self, table_id: int, character: str) -> Image.Image:
        """Return one 64-pixel cell from a loaded sprite table."""
        index = ord(character) - _FIRST_SYMBOL_CODE
        column = index % _COLUMNS
        row = index // _COLUMNS
        left = column * _CELL_SIZE
        top = row * _CELL_SIZE
        return self._tables[table_id].crop((left, top, left + _CELL_SIZE, top + _CELL_SIZE))


class AprsSymbolView(HomeAssistantView):
    """Return local symbol graphics without exposing station data."""

    url = "/api/aprs_monitor/symbol/{code}.png"
    name = "api:aprs_monitor:symbol"
    requires_auth = False

    def __init__(
        self,
        hass: HomeAssistant,
        renderer: AprsSymbolRenderer,
        access_token: str,
    ) -> None:
        self._hass = hass
        self._renderer = renderer
        self._access_token = access_token

    async def get(self, request: web.Request, code: str) -> web.Response:
        """Return a transparent PNG for a valid APRS table and symbol pair."""
        if not compare_digest(request.query.get("token", ""), self._access_token):
            raise web.HTTPNotFound
        png = await self._hass.async_add_executor_job(self._renderer.render, code)
        if png is None:
            raise web.HTTPNotFound
        return web.Response(
            body=png,
            content_type="image/png",
            headers=_CACHE_HEADERS,
        )
