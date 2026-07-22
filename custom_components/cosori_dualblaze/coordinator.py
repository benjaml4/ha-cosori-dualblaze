"""DataUpdateCoordinator for the Cosori Dual Blaze integration."""
from __future__ import annotations

import logging
from dataclasses import replace
from datetime import timedelta
from typing import TYPE_CHECKING, Any

from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    ACTIVE_STATUSES,
    CONF_SCAN_COOKING,
    CONF_SCAN_IDLE,
    DEFAULT_MINUTES,
    DEFAULT_SCAN_COOKING,
    DEFAULT_SCAN_IDLE,
    DEFAULT_TEMP_C,
    DOMAIN,
    MANUAL_PRESET,
    MIN_SCAN_SECONDS,
    PRESETS,
    RUNNING_STATUSES,
)

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)


class DualBlazeCoordinator(DataUpdateCoordinator[None]):
    """Polls one air fryer and holds the pending cook settings.

    The pending temperature / minutes / preset are edited through the number
    and select entities and consumed by the start button and the
    cosori_dualblaze.start_cook service.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        manager: Any,
        fryer: Any,
    ) -> None:
        # Clamp to the hard floor so a stale/aggressive option can't trip
        # VeSync's rate limiter.
        self._interval_active = max(
            MIN_SCAN_SECONDS,
            entry.options.get(CONF_SCAN_COOKING, DEFAULT_SCAN_COOKING),
        )
        self._interval_idle = max(
            MIN_SCAN_SECONDS,
            entry.options.get(CONF_SCAN_IDLE, DEFAULT_SCAN_IDLE),
        )
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN} {fryer.device_name}",
            update_interval=timedelta(seconds=self._interval_idle),
            config_entry=entry,
        )
        self.manager = manager
        self.fryer = fryer
        self.pending_temp: int = DEFAULT_TEMP_C
        self.pending_minutes: int = DEFAULT_MINUTES
        self.pending_preset: str = MANUAL_PRESET

    async def _async_update_data(self) -> None:
        try:
            await self.fryer.update()
        except Exception as err:
            raise UpdateFailed(
                f"Error updating {self.fryer.device_name}: {err}"
            ) from err
        # Poll fast during any mid-cook state (including paused / basket out /
        # queued), so manual starts and basket events surface quickly.
        active = (self.cook_status or "") in ACTIVE_STATUSES
        interval = self._interval_active if active else self._interval_idle
        self.update_interval = timedelta(seconds=interval)

    @property
    def cook_status(self) -> str | None:
        state = self.fryer.state
        status = getattr(state, "cook_status", None)
        if status is None:
            status = getattr(state, "_cook_status", None)
        if status is None:
            return None
        return str(getattr(status, "value", status))

    @property
    def is_running(self) -> bool:
        return (self.cook_status or "") in RUNNING_STATUSES

    def state_attr(self, name: str) -> Any:
        return getattr(self.fryer.state, name, None)

    def _last_response_detail(self) -> str:
        resp = getattr(self.fryer, "last_response", None)
        if resp is None:
            return ""
        code = getattr(resp, "code", None)
        message = getattr(resp, "message", None)
        return f" (device response: code={code}, {message})"

    async def async_start_cook(self, temp_c: int, minutes: int, preset: str) -> None:
        """Start a cook, mirroring pyvesync's set_mode() with preset overrides."""
        fryer = self.fryer
        prepared_temp = fryer.prepare_temperature(int(temp_c))
        if prepared_temp is None:
            raise HomeAssistantError(
                f"Temperature {temp_c} is out of range for this air fryer"
            )

        # The fryer rejects startCook unless it is fully idle. A lingering
        # session (paused, basket out, finished-but-not-dismissed) must be
        # ended first — the VeSync app does the same thing implicitly.
        status = self.cook_status
        if status is not None and status != "standby":
            _LOGGER.debug("Clearing lingering session (status %s) before start", status)
            try:
                await fryer.end()
            except Exception:  # a stale session may already be gone
                _LOGGER.debug("Pre-start end() failed; continuing", exc_info=True)

        mode, recipe_id = PRESETS.get(preset, PRESETS[MANUAL_PRESET])
        recipe = replace(fryer.default_preset)
        recipe.cook_time = fryer.convert_time_for_api(int(minutes) * 60)
        recipe.target_temp = prepared_temp
        recipe.cook_mode = mode
        recipe.recipe_name = preset
        recipe.recipe_id = recipe_id
        ok = await fryer.set_mode_from_recipe(recipe)
        if not ok:
            raise HomeAssistantError(
                "The air fryer rejected the start command"
                + self._last_response_detail()
            )
        await self.async_request_refresh()

    async def async_end_cook(self) -> None:
        """Stop the current cook."""
        ok = await self.fryer.end()
        if not ok:
            raise HomeAssistantError(
                "The air fryer rejected the stop command"
                + self._last_response_detail()
            )
        await self.async_request_refresh()
