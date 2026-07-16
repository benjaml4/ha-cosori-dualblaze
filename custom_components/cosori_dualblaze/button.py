"""Start / stop buttons."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import DualBlazeCoordinator
from .entity import DualBlazeEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinators: list[DualBlazeCoordinator] = entry.runtime_data
    entities: list[ButtonEntity] = []
    for coordinator in coordinators:
        entities.append(DualBlazeStartButton(coordinator))
        entities.append(DualBlazeStopButton(coordinator))
    async_add_entities(entities)


class DualBlazeStartButton(DualBlazeEntity, ButtonEntity):
    """Start cooking with the pending temperature/minutes/preset."""

    _attr_name = "Start cook"
    _attr_icon = "mdi:play-circle"

    def __init__(self, coordinator: DualBlazeCoordinator) -> None:
        super().__init__(coordinator, "start_cook")

    async def async_press(self) -> None:
        coordinator = self.coordinator
        await coordinator.async_start_cook(
            coordinator.pending_temp,
            coordinator.pending_minutes,
            coordinator.pending_preset,
        )


class DualBlazeStopButton(DualBlazeEntity, ButtonEntity):
    """Stop the current cook."""

    _attr_name = "Stop cook"
    _attr_icon = "mdi:stop-circle"

    def __init__(self, coordinator: DualBlazeCoordinator) -> None:
        super().__init__(coordinator, "stop_cook")

    async def async_press(self) -> None:
        await self.coordinator.async_end_cook()
