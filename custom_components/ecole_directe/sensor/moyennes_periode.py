"""Moyennes par période sensor pour Ecole Directe."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.components.sensor import SensorEntityDescription

from custom_components.ecole_directe.sensor.generic import EDGenericSensor

if TYPE_CHECKING:
    from custom_components.ecole_directe.api.client import EDEleve
    from custom_components.ecole_directe.coordinator import EDDataUpdateCoordinator

ENTITY_DESCRIPTIONS = (
    SensorEntityDescription(
        key="periodes_moyennes",
        translation_key="periodes_moyennes",
        icon="mdi:calendar-range",
        has_entity_name=True,
    ),
)


class EDMoyennesPeriodeSensor(EDGenericSensor):
    """Représentation du capteur des moyennes par période."""

    def __init__(
        self,
        coordinator: EDDataUpdateCoordinator,
        entity_description: SensorEntityDescription,
        eleve: EDEleve,
    ) -> None:
        """Initialise le capteur."""
        super().__init__(
            coordinator,
            entity_description,
            f"{eleve.get_fullname_lower()}_periodes_moyennes",
            "Moyennes par période",
            eleve,
        )
        periodes = self.coordinator.data.get(self._key, [])
        # État principal : nombre de périodes récupérées (ex: 3 pour 3 trimestres)
        self._state = len(periodes) if periodes else 0

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Renvoie les attributs avec la liste des périodes."""
        result = super().extra_state_attributes
        periodes = self.coordinator.data.get(self._key, [])

        result.update(
            {
                "periodes": periodes,
            }
        )

        return result
