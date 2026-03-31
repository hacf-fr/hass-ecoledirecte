"""Child sensor for ecole_directe."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.sensor import (
    SensorEntityDescription,
)

from custom_components.ecole_directe.sensor.generic import EDGenericSensor

if TYPE_CHECKING:
    from custom_components.ecole_directe.api import EDEleve
    from custom_components.ecole_directe.coordinator import EDDataUpdateCoordinator

ENTITY_DESCRIPTIONS = (
    SensorEntityDescription(
        key="child",
        translation_key="child",
        icon="mdi:account-school",
        has_entity_name=True,
    ),
)


class EDChildSensor(EDGenericSensor):
    """Representation of a ED child sensor."""

    def __init__(
        self,
        coordinator: EDDataUpdateCoordinator,
        entity_description: SensorEntityDescription,
        eleve: EDEleve,
    ) -> None:
        """Initialize the ED sensor."""
        super().__init__(
            coordinator=coordinator,
            entity_description=entity_description,
            key=eleve.get_fullname_lower(),
            name=f"Profil {eleve.eleve_firstname}",
            eleve=eleve,
        )
        self._account_type = self.coordinator.data["session"].account_type

    @property
    def native_value(self) -> str:
        """Return the state of the sensor."""
        if self._child_info is None:
            return "unavailable"
        return self._child_info.get_fullname()

    @property
    def extra_state_attributes(self) -> dict[str, str]:
        """Return the state attributes."""
        if self._child_info is None:
            return {}

        return {
            "prenom": self._child_info.eleve_firstname,
            "nom": self._child_info.eleve_lastname,
            "nom complet": self._child_info.get_fullname(),
            "classe": self._child_info.classe_name,
            "etablissement": self._child_info.establishment,
            "via_parent_account": self._account_type == "1",
        }

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success
