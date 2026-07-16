"""Preset select entity."""
from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import MANUAL_PRESET, PRESETS
from .coordinator import DualBlazeCoordinator
from .entity import DualBlazeEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinators: list[DualBlazeCoordinator] = entry.runtime_data
    async_add_entities(
        DualBlazePresetSelect(coordinator) for coordinator in coordinators
    )


class DualBlazePresetSelect(DualBlazeEntity, SelectEntity, RestoreEntity):
    """Which preset the next cook will use."""

    _attr_name = "Preset"
    _attr_icon = "mdi:silverware-fork-knife"
    _attr_options = list(PRESETS)

    def __init__(self, coordinator: DualBlazeCoordinator) -> None:
        super().__init__(coordinator, "preset")

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if last_state is not None and last_state.state in PRESETS:
            self.coordinator.pending_preset = last_state.state

    @property
    def current_option(self) -> str:
        if self.coordinator.pending_preset not in PRESETS:
            return MANUAL_PRESET
        return self.coordinator.pending_preset

    async def async_select_option(self, option: str) -> None:
        self.coordinator.pending_preset = option
        self.async_write_ha_state()
