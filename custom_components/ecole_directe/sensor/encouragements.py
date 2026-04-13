"""Encouragements sensor for ecole_directe."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.components.sensor import (
    SensorEntityDescription,
)

from custom_components.ecole_directe.sensor.generic import EDGenericSensor

if TYPE_CHECKING:
    from custom_components.ecole_directe.api.client import EDEleve
    from custom_components.ecole_directe.coordinator import EDDataUpdateCoordinator

ENTITY_DESCRIPTIONS = (
    SensorEntityDescription(
        key="encouragements",
        translation_key="encouragements",
        icon="mdi:thumb-up",
        has_entity_name=True,
    ),
)


class EDEncouragementsSensor(EDGenericSensor):
    """Representation of a ED sensor."""

    def __init__(
        self,
        coordinator: EDDataUpdateCoordinator,
        entity_description: SensorEntityDescription,
        eleve: EDEleve,
    ) -> None:
        """Initialize the ED sensor."""
        super().__init__(
            coordinator,
            entity_description,
            f"{eleve.get_fullname_lower()}_encouragements",
            "Encouragements",
            eleve,
            "len",
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        attributes = []
        if self._key in self.coordinator.data:
            encouragements = self.coordinator.data[self._key]
            for encouragement in encouragements:
                attributes.append(encouragement)
        result = super().extra_state_attributes
        result.update(
            {
                "Encouragements": attributes,
            }
        )
        return result
