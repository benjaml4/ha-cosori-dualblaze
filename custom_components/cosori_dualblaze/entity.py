"""Base entity for the Cosori Dual Blaze integration."""
from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import DualBlazeCoordinator


class DualBlazeEntity(CoordinatorEntity[DualBlazeCoordinator]):
    """Base entity tied to one air fryer."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: DualBlazeCoordinator, key: str) -> None:
        super().__init__(coordinator)
        fryer = coordinator.fryer
        self._attr_unique_id = f"{fryer.cid}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, fryer.cid)},
            manufacturer="Cosori",
            model=getattr(fryer, "device_type", None),
            name=fryer.device_name,
            sw_version=getattr(fryer, "current_firm_version", None),
        )

    @property
    def connection_online(self) -> bool | None:
        conn = getattr(self.coordinator.fryer.state, "connection_status", None)
        if conn is None:
            return None
        return str(getattr(conn, "value", conn)) == "online"

    @property
    def available(self) -> bool:
        if self.connection_online is False:
            return False
        return super().available
