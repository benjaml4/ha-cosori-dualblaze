"""Number entities holding the pending cook settings."""
from __future__ import annotations

from homeassistant.components.number import NumberMode, RestoreNumber
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    MAX_MINUTES,
    MAX_TEMP_C,
    MIN_MINUTES,
    MIN_TEMP_C,
    TEMP_STEP_C,
)
from .coordinator import DualBlazeCoordinator
from .entity import DualBlazeEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinators: list[DualBlazeCoordinator] = entry.runtime_data
    entities: list[RestoreNumber] = []
    for coordinator in coordinators:
        entities.append(
            DualBlazePendingNumber(
                coordinator,
                key="cook_temperature",
                name="Cook temperature",
                pending_attr="pending_temp",
                minimum=MIN_TEMP_C,
                maximum=MAX_TEMP_C,
                step=TEMP_STEP_C,
                unit=UnitOfTemperature.CELSIUS,
                icon="mdi:thermometer",
            )
        )
        entities.append(
            DualBlazePendingNumber(
                coordinator,
                key="cook_minutes",
                name="Cook minutes",
                pending_attr="pending_minutes",
                minimum=MIN_MINUTES,
                maximum=MAX_MINUTES,
                step=1,
                unit=UnitOfTime.MINUTES,
                icon="mdi:timer-outline",
            )
        )
    async_add_entities(entities)


class DualBlazePendingNumber(DualBlazeEntity, RestoreNumber):
    """A locally-held cook setting, consumed by the start button/service."""

    _attr_mode = NumberMode.BOX

    def __init__(
        self,
        coordinator: DualBlazeCoordinator,
        *,
        key: str,
        name: str,
        pending_attr: str,
        minimum: int,
        maximum: int,
        step: int,
        unit: str,
        icon: str,
    ) -> None:
        super().__init__(coordinator, key)
        self._attr_name = name
        self._pending_attr = pending_attr
        self._attr_native_min_value = minimum
        self._attr_native_max_value = maximum
        self._attr_native_step = step
        self._attr_native_unit_of_measurement = unit
        self._attr_icon = icon

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        data = await self.async_get_last_number_data()
        if data is not None and data.native_value is not None:
            setattr(self.coordinator, self._pending_attr, int(data.native_value))

    @property
    def native_value(self) -> int:
        return getattr(self.coordinator, self._pending_attr)

    async def async_set_native_value(self, value: float) -> None:
        setattr(self.coordinator, self._pending_attr, int(value))
        self.async_write_ha_state()
