"""Manual refresh button for APRS Monitor."""

from homeassistant.components.button import ButtonDeviceClass, ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .hub import hub_device_info

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Create the central manual-refresh button."""
    async_add_entities(
        [AprsRefreshButton(hass.data[DOMAIN][entry.entry_id], entry.entry_id)]
    )


class AprsRefreshButton(CoordinatorEntity, ButtonEntity):
    """Request an immediate refresh through the shared coordinator."""

    _attr_has_entity_name = True
    _attr_translation_key = "refresh"
    _attr_device_class = ButtonDeviceClass.UPDATE

    def __init__(self, coordinator, entry_id: str) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry_id}_refresh"
        self._attr_device_info = hub_device_info(entry_id)

    @property
    def available(self) -> bool:
        """Keep recovery controls available during an API outage."""
        return True

    async def async_press(self) -> None:
        """Request an immediate coordinator refresh."""
        await self.coordinator.async_request_refresh()
