"""Discipline sensor for ecole_directe."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.components.sensor import (
    SensorEntityDescription,
    SensorStateClass,
)

from custom_components.ecole_directe.helpers import get_unique_id
from custom_components.ecole_directe.sensor.generic import EDGenericSensor

if TYPE_CHECKING:
    from custom_components.ecole_directe.api.client import EDEleve
    from custom_components.ecole_directe.coordinator import EDDataUpdateCoordinator

ENTITY_DESCRIPTIONS = (
    SensorEntityDescription(
        key="discipline",
        translation_key="discipline",
        icon="mdi:book-open-variant",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        has_entity_name=True,
    ),
)


class EDDisciplineSensor(EDGenericSensor):
    """Representation of a ED sensor."""

    def __init__(
        self,
        coordinator: EDDataUpdateCoordinator,
        entity_description: SensorEntityDescription,
        eleve: EDEleve,
        nom: str,
        note: Any,
    ) -> None:
        """Initialize the ED sensor."""
        super().__init__(
            coordinator,
            entity_description,
            f"{eleve.get_fullname_lower()}_{get_unique_id(nom)}",
            nom,
            eleve,
            note,
        )
        self.unique_id = f"ed_{eleve.get_fullname_lower()}_{get_unique_id(nom)}"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        discipline = self.coordinator.data[self._key]
        attributes = []
        attributes.append({"code": discipline["code"]})

        result = super().extra_state_attributes
        result.update(
            {
                "Code": discipline["code"],
                "Nom": discipline["nom"],
                "Moyenne classe": discipline["moyenneClasse"],
                "Moyenne minimum": discipline["moyenneMin"],
                "Moyenne maximum": discipline["moyenneMax"],
                "Appréciations": discipline["appreciations"],
            }
        )
        return result
