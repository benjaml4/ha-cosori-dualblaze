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
    DEFAULT_MINUTES,
    DEFAULT_TEMP_C,
    DOMAIN,
    MANUAL_PRESET,
    PRESETS,
    RUNNING_STATUSES,
    SCAN_INTERVAL_COOKING,
    SCAN_INTERVAL_IDLE,
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
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN} {fryer.device_name}",
            update_interval=timedelta(seconds=SCAN_INTERVAL_IDLE),
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
        interval = SCAN_INTERVAL_COOKING if active else SCAN_INTERVAL_IDLE
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

    async def async_start_cook(self, temp_c: int, minutes: int, preset: str) -> None:
        """Start a cook, mirroring pyvesync's set_mode() with preset overrides."""
        fryer = self.fryer
        prepared_temp = fryer.prepare_temperature(int(temp_c))
        if prepared_temp is None:
            raise HomeAssistantError(
                f"Temperature {temp_c} is out of range for this air fryer"
            )
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
                "The air fryer rejected the start command "
                "(is the basket inserted and the appliance idle?)"
            )
        await self.async_request_refresh()

    async def async_end_cook(self) -> None:
        """Stop the current cook."""
        ok = await self.fryer.end()
        if not ok:
            raise HomeAssistantError(
                "The air fryer rejected the stop command (is anything cooking?)"
            )
        await self.async_request_refresh()
