"""Config flow for the Cosori Dual Blaze integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import CONF_COUNTRY_CODE, DEFAULT_COUNTRY_CODE, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Required(CONF_COUNTRY_CODE, default=DEFAULT_COUNTRY_CODE): str,
    }
)


async def _async_validate(hass: HomeAssistant, data: dict[str, Any]) -> str | None:
    """Try logging in; return an error key or None on success."""
    from pyvesync import VeSync

    try:
        from pyvesync.utils.errors import VeSyncLoginError
    except ImportError:
        VeSyncLoginError = None  # type: ignore[assignment]

    manager = VeSync(
        data[CONF_USERNAME],
        data[CONF_PASSWORD],
        country_code=data.get(CONF_COUNTRY_CODE, DEFAULT_COUNTRY_CODE),
        session=async_get_clientsession(hass),
        time_zone=hass.config.time_zone or "UTC",
    )
    try:
        if not await manager.login():
            return "invalid_auth"
    except Exception as err:
        if VeSyncLoginError is not None and isinstance(err, VeSyncLoginError):
            return "invalid_auth"
        _LOGGER.exception("Unexpected error logging in to VeSync")
        return "cannot_connect"

    try:
        await manager.get_devices()
    except Exception:
        _LOGGER.exception("Unexpected error fetching VeSync devices")
        return "cannot_connect"

    if not list(getattr(manager.devices, "air_fryers", []) or []):
        return "no_air_fryer"
    return None


class DualBlazeConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the config flow."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_USERNAME].lower())
            self._abort_if_unique_id_configured()
            error = await _async_validate(self.hass, user_input)
            if error is None:
                return self.async_create_entry(
                    title=user_input[CONF_USERNAME],
                    data={
                        CONF_USERNAME: user_input[CONF_USERNAME],
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                        CONF_COUNTRY_CODE: user_input[CONF_COUNTRY_CODE].upper(),
                    },
                )
            errors["base"] = error
        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_SCHEMA, errors=errors
        )

    async def async_step_reauth(
        self, entry_data: dict[str, Any]
    ) -> ConfigFlowResult:
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        reauth_entry = self._get_reauth_entry()
        if user_input is not None:
            data = {**reauth_entry.data, CONF_PASSWORD: user_input[CONF_PASSWORD]}
            error = await _async_validate(self.hass, data)
            if error is None:
                return self.async_update_reload_and_abort(reauth_entry, data=data)
            errors["base"] = error
        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({vol.Required(CONF_PASSWORD): str}),
            errors=errors,
        )
