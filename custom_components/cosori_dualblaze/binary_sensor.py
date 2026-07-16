"""Binary sensors for the Cosori Dual Blaze integration."""
from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
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
    entities: list[BinarySensorEntity] = []
    for coordinator in coordinators:
        entities.append(DualBlazeRunningSensor(coordinator))
        entities.append(DualBlazeConnectivitySensor(coordinator))
    async_add_entities(entities)


class DualBlazeRunningSensor(DualBlazeEntity, BinarySensorEntity):
    """On while the fryer is cooking, heating or preheating."""

    _attr_name = "Cooking"
    _attr_device_class = BinarySensorDeviceClass.RUNNING

    def __init__(self, coordinator: DualBlazeCoordinator) -> None:
        super().__init__(coordinator, "running")

    @property
    def is_on(self) -> bool:
        return self.coordinator.is_running


class DualBlazeConnectivitySensor(DualBlazeEntity, BinarySensorEntity):
    """Whether the fryer is reachable by the VeSync cloud."""

    _attr_name = "Connectivity"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: DualBlazeCoordinator) -> None:
        super().__init__(coordinator, "connectivity")

    @property
    def is_on(self) -> bool:
        return self.connection_online is True

    @property
    def available(self) -> bool:
        # This sensor must stay available while the device itself is offline —
        # that is exactly what it reports.
        return self.coordinator.last_update_success
