"""Generic sensor for ecole_directe."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.json import (
    json_bytes,
)

from custom_components.ecole_directe.api.client import get_unique_id
from custom_components.ecole_directe.const import DOMAIN, MAX_STATE_ATTRS_BYTES
from custom_components.ecole_directe.entity.base import EDEntity

if TYPE_CHECKING:
    from custom_components.ecole_directe.api.client import EDEleve
    from custom_components.ecole_directe.coordinator import EDDataUpdateCoordinator


def is_too_big(obj: Any) -> bool:
    """Calculate is_too_big."""
    bytes_result = json_bytes(obj)
    return len(bytes_result) > MAX_STATE_ATTRS_BYTES


class EDGenericSensor(SensorEntity, EDEntity):
    """Representation of a ED sensor."""

    def __init__(
        self,
        coordinator: EDDataUpdateCoordinator,
        entity_description: SensorEntityDescription,
        key: str,
        name: str,
        eleve: EDEleve | None = None,
        state: str | int | None = None,
    ) -> None:
        """Initialize the ED sensor."""
        super().__init__(coordinator, entity_description)

        identifiant = self.coordinator.data["session"].identifiant
        device = (
            f"ED - {identifiant}" if eleve is None else f"ED - {eleve.get_fullname()}"
        )

        self._key = get_unique_id(key)
        self._child_info = eleve
        self._state = state
        self.unique_id = (
            f"ed_{identifiant}_{self._key}" if eleve is None else f"ed_{self._key}"
        )
        self._attr_name = name
        self._attr_has_entity_name = True

        self._attr_device_info = DeviceInfo(
            name=device,
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, device)},
            manufacturer="Ecole Directe",
            model=device,
        )

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        if self._key not in self.coordinator.data:
            return "unavailable"
        if self._state is not None:
            if self._state == "len":
                if self.coordinator.data[self._key] is None:
                    return 0
                return len(self.coordinator.data[self._key])
            return self._state
        return self.coordinator.data[self._key]

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        if self._child_info is None:
            return {}

        return {"prenom": self._child_info.eleve_firstname}

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success and self._key in self.coordinator.data
        )
