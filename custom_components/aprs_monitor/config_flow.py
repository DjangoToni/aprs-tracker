"""Config flow for APRS Monitor."""

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import section
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .api import AprsFiAuthenticationError, AprsFiError, async_validate_api
from .const import (
    CONF_API_KEY,
    CONF_CALLSIGNS,
    CONF_DISPLAY_NAME,
    CONF_HOME_RADIUS,
    CONF_MAP_MARKER_STYLE,
    CONF_MAX_POSITION_AGE,
    CONF_MOVEMENT_SPEED_THRESHOLD,
    CONF_STATION_PROFILES,
    CONF_UPDATE_INTERVAL,
    DEFAULT_HOME_RADIUS,
    DEFAULT_MAP_MARKER_STYLE,
    DEFAULT_MAX_POSITION_AGE,
    DEFAULT_MOVEMENT_SPEED_THRESHOLD,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    MAP_MARKER_STYLES,
    MAX_HOME_RADIUS,
    MAX_MAX_POSITION_AGE,
    MAX_MOVEMENT_SPEED_THRESHOLD,
    MAX_UPDATE_INTERVAL,
    MIN_HOME_RADIUS,
    MIN_MAX_POSITION_AGE,
    MIN_MOVEMENT_SPEED_THRESHOLD,
    MIN_UPDATE_INTERVAL,
    NAME,
)
from .validation import (
    normalize_callsigns,
    normalize_home_radius,
    normalize_max_position_age,
    normalize_movement_speed_threshold,
    normalize_update_interval,
)

_API_KEY_SELECTOR = TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD))
_MAP_MARKER_STYLE_SELECTOR = SelectSelector(
    SelectSelectorConfig(
        options=list(MAP_MARKER_STYLES),
        translation_key="map_marker_style",
    )
)
_OPTIONS_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_CALLSIGNS): str,
        vol.Required(CONF_UPDATE_INTERVAL): vol.All(
            vol.Coerce(int),
            vol.Range(min=MIN_UPDATE_INTERVAL, max=MAX_UPDATE_INTERVAL),
        ),
        vol.Required(CONF_MAX_POSITION_AGE): vol.All(
            vol.Coerce(int),
            vol.Range(min=MIN_MAX_POSITION_AGE, max=MAX_MAX_POSITION_AGE),
        ),
        vol.Required(CONF_HOME_RADIUS): vol.All(
            vol.Coerce(float),
            vol.Range(min=MIN_HOME_RADIUS, max=MAX_HOME_RADIUS),
        ),
        vol.Required(CONF_MOVEMENT_SPEED_THRESHOLD): vol.All(
            vol.Coerce(float),
            vol.Range(
                min=MIN_MOVEMENT_SPEED_THRESHOLD,
                max=MAX_MOVEMENT_SPEED_THRESHOLD,
            ),
        ),
        vol.Required(CONF_MAP_MARKER_STYLE): _MAP_MARKER_STYLE_SELECTOR,
    }
)


class AprsMonitorConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Create an APRS Monitor config entry."""

    VERSION = 2

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Return the APRS Monitor options flow."""
        return AprsMonitorOptionsFlow()

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Collect and locally validate the API configuration."""
        errors: dict[str, str] = {}
        if user_input is not None:
            api_key = user_input[CONF_API_KEY].strip()
            callsigns = normalize_callsigns(user_input[CONF_CALLSIGNS])
            if not api_key:
                errors[CONF_API_KEY] = "api_key_required"
            if not callsigns:
                errors[CONF_CALLSIGNS] = "invalid_callsigns"

            if not errors:
                try:
                    await async_validate_api(
                        async_get_clientsession(self.hass),
                        api_key,
                        callsigns,
                    )
                except AprsFiAuthenticationError:
                    errors["base"] = "invalid_auth"
                except AprsFiError:
                    errors["base"] = "cannot_connect"

                if not errors:
                    await self.async_set_unique_id(DOMAIN)
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(
                        title=NAME,
                        data={
                            CONF_API_KEY: api_key,
                            CONF_CALLSIGNS: list(callsigns),
                        },
                    )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_API_KEY): _API_KEY_SELECTOR,
                    vol.Required(CONF_CALLSIGNS): str,
                }
            ),
            errors=errors,
        )

    async def async_step_reauth(self, _entry_data: dict[str, Any]):
        """Start reauthentication for an existing config entry."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self,
        user_input: dict[str, Any] | None = None,
    ):
        """Validate and store a replacement aprs.fi API key."""
        errors: dict[str, str] = {}
        if user_input is not None:
            api_key = user_input[CONF_API_KEY].strip()
            entry = self._get_reauth_entry()
            callsigns = tuple(entry.options.get(CONF_CALLSIGNS, entry.data[CONF_CALLSIGNS]))
            if not api_key:
                errors[CONF_API_KEY] = "api_key_required"
            else:
                try:
                    await async_validate_api(
                        async_get_clientsession(self.hass),
                        api_key,
                        callsigns,
                    )
                except AprsFiAuthenticationError:
                    errors["base"] = "invalid_auth"
                except AprsFiError:
                    errors["base"] = "cannot_connect"

            if not errors:
                await self.async_set_unique_id(DOMAIN)
                self._abort_if_unique_id_mismatch()
                return self.async_update_reload_and_abort(
                    entry,
                    data_updates={CONF_API_KEY: api_key},
                    reload_even_if_entry_is_unchanged=False,
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({vol.Required(CONF_API_KEY): _API_KEY_SELECTOR}),
            errors=errors,
        )


class AprsMonitorOptionsFlow(config_entries.OptionsFlowWithReload):
    """Change monitored callsigns and the polling interval."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        """Manage APRS Monitor options."""
        errors: dict[str, str] = {}
        if user_input is not None:
            callsigns = normalize_callsigns(user_input[CONF_CALLSIGNS])
            interval = normalize_update_interval(user_input[CONF_UPDATE_INTERVAL])
            max_position_age = normalize_max_position_age(user_input[CONF_MAX_POSITION_AGE])
            home_radius = normalize_home_radius(user_input[CONF_HOME_RADIUS])
            movement_speed_threshold = normalize_movement_speed_threshold(
                user_input[CONF_MOVEMENT_SPEED_THRESHOLD]
            )
            if not callsigns:
                errors[CONF_CALLSIGNS] = "invalid_callsigns"
            if interval is None:
                errors[CONF_UPDATE_INTERVAL] = "invalid_update_interval"
            if max_position_age is None:
                errors[CONF_MAX_POSITION_AGE] = "invalid_max_position_age"
            if home_radius is None:
                errors[CONF_HOME_RADIUS] = "invalid_home_radius"
            if movement_speed_threshold is None:
                errors[CONF_MOVEMENT_SPEED_THRESHOLD] = "invalid_movement_speed_threshold"
            if not errors:
                self._pending_options = {
                    CONF_CALLSIGNS: list(callsigns),
                    CONF_UPDATE_INTERVAL: interval,
                    CONF_MAX_POSITION_AGE: max_position_age,
                    CONF_HOME_RADIUS: home_radius,
                    CONF_MOVEMENT_SPEED_THRESHOLD: movement_speed_threshold,
                    CONF_MAP_MARKER_STYLE: user_input[CONF_MAP_MARKER_STYLE],
                }
                return await self.async_step_profiles()

        configured_callsigns = self.config_entry.options.get(
            CONF_CALLSIGNS,
            self.config_entry.data[CONF_CALLSIGNS],
        )
        suggested_values = user_input or {
            CONF_CALLSIGNS: ", ".join(configured_callsigns),
            CONF_UPDATE_INTERVAL: self.config_entry.options.get(
                CONF_UPDATE_INTERVAL,
                DEFAULT_UPDATE_INTERVAL,
            ),
            CONF_MAX_POSITION_AGE: self.config_entry.options.get(
                CONF_MAX_POSITION_AGE,
                DEFAULT_MAX_POSITION_AGE,
            ),
            CONF_HOME_RADIUS: self.config_entry.options.get(
                CONF_HOME_RADIUS,
                DEFAULT_HOME_RADIUS,
            ),
            CONF_MOVEMENT_SPEED_THRESHOLD: self.config_entry.options.get(
                CONF_MOVEMENT_SPEED_THRESHOLD,
                DEFAULT_MOVEMENT_SPEED_THRESHOLD,
            ),
            CONF_MAP_MARKER_STYLE: self.config_entry.options.get(
                CONF_MAP_MARKER_STYLE,
                DEFAULT_MAP_MARKER_STYLE,
            ),
        }
        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(
                _OPTIONS_SCHEMA,
                suggested_values,
            ),
            errors=errors,
        )

    async def async_step_profiles(self, user_input: dict[str, Any] | None = None):
        """Configure friendly names and thresholds for each station."""
        pending = self._pending_options
        callsigns = pending[CONF_CALLSIGNS]
        if user_input is not None:
            profiles = {}
            for callsign in callsigns:
                values = user_input[callsign]
                profiles[callsign] = {
                    CONF_DISPLAY_NAME: values[CONF_DISPLAY_NAME].strip(),
                    CONF_MAX_POSITION_AGE: int(values[CONF_MAX_POSITION_AGE]),
                    CONF_HOME_RADIUS: float(values[CONF_HOME_RADIUS]),
                    CONF_MOVEMENT_SPEED_THRESHOLD: float(values[CONF_MOVEMENT_SPEED_THRESHOLD]),
                }
            return self.async_create_entry(data={**pending, CONF_STATION_PROFILES: profiles})

        existing_profiles = self.config_entry.options.get(CONF_STATION_PROFILES, {})
        schema: dict = {}
        for callsign in callsigns:
            existing = existing_profiles.get(callsign, {})
            schema[vol.Required(callsign)] = section(
                vol.Schema(
                    {
                        vol.Required(
                            CONF_DISPLAY_NAME,
                            default=existing.get(CONF_DISPLAY_NAME, callsign),
                        ): vol.All(str, vol.Length(max=64)),
                        vol.Required(
                            CONF_MAX_POSITION_AGE,
                            default=existing.get(
                                CONF_MAX_POSITION_AGE,
                                pending[CONF_MAX_POSITION_AGE],
                            ),
                        ): vol.All(
                            vol.Coerce(int),
                            vol.Range(
                                min=MIN_MAX_POSITION_AGE,
                                max=MAX_MAX_POSITION_AGE,
                            ),
                        ),
                        vol.Required(
                            CONF_HOME_RADIUS,
                            default=existing.get(
                                CONF_HOME_RADIUS,
                                pending[CONF_HOME_RADIUS],
                            ),
                        ): vol.All(
                            vol.Coerce(float),
                            vol.Range(min=MIN_HOME_RADIUS, max=MAX_HOME_RADIUS),
                        ),
                        vol.Required(
                            CONF_MOVEMENT_SPEED_THRESHOLD,
                            default=existing.get(
                                CONF_MOVEMENT_SPEED_THRESHOLD,
                                pending[CONF_MOVEMENT_SPEED_THRESHOLD],
                            ),
                        ): vol.All(
                            vol.Coerce(float),
                            vol.Range(
                                min=MIN_MOVEMENT_SPEED_THRESHOLD,
                                max=MAX_MOVEMENT_SPEED_THRESHOLD,
                            ),
                        ),
                    }
                ),
                {"collapsed": True},
            )
        return self.async_show_form(
            step_id="profiles",
            data_schema=vol.Schema(schema),
        )
