"""Moyenne générale sensor for ecole_directe."""

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
        key="moyenne_generale",
        translation_key="moyenne_generale",
        icon="mdi:chart-line",
        has_entity_name=True,
    ),
)


class EDMoyenneGeneraleSensor(EDGenericSensor):
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
            f"{eleve.get_fullname_lower()}_moyenne_generale",
            "Moyenne générale",
            eleve,
        )
        if "moyenneGenerale" in self.coordinator.data[self._key]:
            self._state = self.coordinator.data[self._key]["moyenneGenerale"]
        else:
            self._state = "unavailable"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        moyenne = self.coordinator.data[self._key]
        result = super().extra_state_attributes

        if moyenne is None or moyenne == {}:
            return result

        disciplines = self.coordinator.data[
            f"{self._child_info.get_fullname_lower()}_disciplines"
        ]

        result.update(
            {
                "Moyenne classe": moyenne["moyenneClasse"],
                "Moyenne minimum": moyenne["moyenneMin"],
                "Moyenne maximum": moyenne["moyenneMax"],
                "Date de calcul": moyenne["dateCalcul"],
                "Disciplines": disciplines,
            }
        )

        return result
