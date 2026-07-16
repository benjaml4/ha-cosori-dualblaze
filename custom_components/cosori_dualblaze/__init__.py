"""The Cosori Dual Blaze integration."""
from __future__ import annotations

import logging

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import (
    ConfigEntryAuthFailed,
    ConfigEntryNotReady,
    HomeAssistantError,
)
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    ATTR_MINUTES,
    ATTR_PRESET,
    ATTR_TEMPERATURE,
    CONF_COUNTRY_CODE,
    DEFAULT_COUNTRY_CODE,
    DOMAIN,
    MANUAL_PRESET,
    MAX_MINUTES,
    MAX_TEMP_C,
    MIN_MINUTES,
    MIN_TEMP_C,
    PRESETS,
    SERVICE_END_COOK,
    SERVICE_START_COOK,
)
from .coordinator import DualBlazeCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SENSOR,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Cosori Dual Blaze from a config entry."""
    from pyvesync import VeSync

    try:
        from pyvesync.utils.errors import VeSyncLoginError
    except ImportError:  # library layout may change in future releases
        VeSyncLoginError = None  # type: ignore[assignment]

    manager = VeSync(
        entry.data[CONF_USERNAME],
        entry.data[CONF_PASSWORD],
        country_code=entry.data.get(CONF_COUNTRY_CODE, DEFAULT_COUNTRY_CODE),
        session=async_get_clientsession(hass),
        time_zone=hass.config.time_zone or "UTC",
    )

    try:
        if not await manager.login():
            raise ConfigEntryAuthFailed("VeSync login failed")
    except ConfigEntryAuthFailed:
        raise
    except Exception as err:
        if VeSyncLoginError is not None and isinstance(err, VeSyncLoginError):
            raise ConfigEntryAuthFailed(str(err)) from err
        raise ConfigEntryNotReady(f"Unable to reach the VeSync cloud: {err}") from err

    try:
        await manager.get_devices()
    except Exception as err:
        raise ConfigEntryNotReady(f"Unable to fetch VeSync devices: {err}") from err

    fryers = list(getattr(manager.devices, "air_fryers", []) or [])
    if not fryers:
        raise ConfigEntryNotReady(
            "No supported air fryer found on this VeSync account"
        )

    coordinators: list[DualBlazeCoordinator] = []
    for fryer in fryers:
        coordinator = DualBlazeCoordinator(hass, entry, manager, fryer)
        await coordinator.async_config_entry_first_refresh()
        coordinators.append(coordinator)

    entry.runtime_data = coordinators
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinators

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    _async_register_services(hass)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
        if not hass.data.get(DOMAIN):
            hass.services.async_remove(DOMAIN, SERVICE_START_COOK)
            hass.services.async_remove(DOMAIN, SERVICE_END_COOK)
    return unload_ok


def _async_register_services(hass: HomeAssistant) -> None:
    """Register domain services (once)."""
    if hass.services.has_service(DOMAIN, SERVICE_START_COOK):
        return

    def _coordinators() -> list[DualBlazeCoordinator]:
        return [
            coordinator
            for entry_coordinators in hass.data.get(DOMAIN, {}).values()
            for coordinator in entry_coordinators
        ]

    async def _handle_start_cook(call: ServiceCall) -> None:
        coordinators = _coordinators()
        if not coordinators:
            raise HomeAssistantError("No Dual Blaze air fryer is currently set up")
        for coordinator in coordinators:
            await coordinator.async_start_cook(
                call.data[ATTR_TEMPERATURE],
                call.data[ATTR_MINUTES],
                call.data.get(ATTR_PRESET, MANUAL_PRESET),
            )

    async def _handle_end_cook(call: ServiceCall) -> None:
        coordinators = _coordinators()
        if not coordinators:
            raise HomeAssistantError("No Dual Blaze air fryer is currently set up")
        for coordinator in coordinators:
            await coordinator.async_end_cook()

    hass.services.async_register(
        DOMAIN,
        SERVICE_START_COOK,
        _handle_start_cook,
        schema=vol.Schema(
            {
                vol.Required(ATTR_TEMPERATURE): vol.All(
                    vol.Coerce(int), vol.Range(min=MIN_TEMP_C, max=MAX_TEMP_C)
                ),
                vol.Required(ATTR_MINUTES): vol.All(
                    vol.Coerce(int), vol.Range(min=MIN_MINUTES, max=MAX_MINUTES)
                ),
                vol.Optional(ATTR_PRESET, default=MANUAL_PRESET): vol.In(
                    list(PRESETS)
                ),
            }
        ),
    )
    hass.services.async_register(
        DOMAIN, SERVICE_END_COOK, _handle_end_cook, schema=vol.Schema({})
    )
