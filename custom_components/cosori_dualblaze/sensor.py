"""Sensors for the Cosori Dual Blaze integration."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import DualBlazeCoordinator
from .entity import DualBlazeEntity


@dataclass(frozen=True, kw_only=True)
class DualBlazeSensorDescription(SensorEntityDescription):
    """Sensor description with a value extractor."""

    value_fn: Callable[[DualBlazeCoordinator], Any]


SENSORS: tuple[DualBlazeSensorDescription, ...] = (
    DualBlazeSensorDescription(
        key="cook_status",
        name="Cook status",
        icon="mdi:pot-steam",
        value_fn=lambda c: c.cook_status,
    ),
    DualBlazeSensorDescription(
        key="current_temperature",
        name="Current temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        # The device reports current temperature in Celsius regardless of its
        # configured display unit.
        value_fn=lambda c: c.state_attr("current_temp"),
    ),
    DualBlazeSensorDescription(
        key="set_temperature",
        name="Set temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_fn=lambda c: c.state_attr("cook_set_temp"),
    ),
    DualBlazeSensorDescription(
        key="time_remaining",
        name="Time remaining",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        value_fn=lambda c: c.state_attr("cook_last_time"),
    ),
    DualBlazeSensorDescription(
        key="set_time",
        name="Set time",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        value_fn=lambda c: c.state_attr("cook_set_time"),
    ),
    DualBlazeSensorDescription(
        key="cook_mode",
        name="Cook mode",
        icon="mdi:chef-hat",
        value_fn=lambda c: c.state_attr("cook_mode") or c.state_attr("recipe"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinators: list[DualBlazeCoordinator] = entry.runtime_data
    async_add_entities(
        DualBlazeSensor(coordinator, description)
        for coordinator in coordinators
        for description in SENSORS
    )


class DualBlazeSensor(DualBlazeEntity, SensorEntity):
    """A read-only air fryer state value."""

    entity_description: DualBlazeSensorDescription

    def __init__(
        self,
        coordinator: DualBlazeCoordinator,
        description: DualBlazeSensorDescription,
    ) -> None:
        self.entity_description = description
        super().__init__(coordinator, description.key)

    @property
    def native_value(self) -> Any:
        return self.entity_description.value_fn(self.coordinator)
