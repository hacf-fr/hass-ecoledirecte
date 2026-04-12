"""Homeworks sensor for ecole_directe."""

from __future__ import annotations

import operator
from typing import TYPE_CHECKING, Any

from homeassistant.components.sensor import (
    SensorEntityDescription,
)

from custom_components.ecole_directe.const import LOGGER
from custom_components.ecole_directe.sensor.generic import EDGenericSensor, is_too_big

if TYPE_CHECKING:
    from custom_components.ecole_directe.api.client import EDEleve
    from custom_components.ecole_directe.coordinator import EDDataUpdateCoordinator

ENTITY_DESCRIPTIONS = (
    SensorEntityDescription(
        key="homeworks",
        translation_key="homeworks",
        icon="mdi:book-open",
        has_entity_name=True,
    ),
)


class EDHomeworksSensor(EDGenericSensor):
    """Representation of a ED sensor."""

    def __init__(
        self,
        coordinator: EDDataUpdateCoordinator,
        entity_description: SensorEntityDescription,
        eleve: EDEleve,
        suffix: str,
    ) -> None:
        """Initialize the ED sensor."""
        super().__init__(
            coordinator,
            entity_description,
            f"{eleve.get_fullname_lower()}_homeworks{suffix}",
            "Devoirs",
            eleve,
            "len",
        )
        self._suffix = suffix
        self._attr_name = self.name
        self.unique_id = f"ed_{eleve.get_fullname_lower()}_devoirs{suffix}"

    @property
    def name(self) -> str | None:
        """Return the name of the sensor."""
        name = "Devoirs"
        match self._suffix:
            case "_1":
                name = "Devoirs - Semaine en cours"
            case "_2":
                name = "Devoirs - Semaine suivante"
            case "_3":
                name = "Devoirs - Semaine après suivante"
            case "_today":
                name = "Devoirs - Aujourd'hui"
            case "_tomorrow":
                name = "Devoirs - Demain"
            case "_next_day":
                name = "Devoirs - Jour suivant"
        return name

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        attributes = []
        todo_counter = 0
        if self._child_info is None:
            return {}
        if self._key in self.coordinator.data:
            homeworks = self.coordinator.data[self._key]
            if homeworks is not None:
                for homework in homeworks:
                    if not homework["effectue"]:
                        todo_counter += 1
                    attributes.append(homework)
                if attributes is not None:
                    attributes.sort(key=operator.itemgetter("date"))
        else:
            attributes.append({"Erreur": f"{self._key} n'existe pas."})

        if is_too_big(attributes):
            attributes = []
            attributes.append(
                {
                    "Erreur": "Les attributs sont trop volumineux. Essayez de désactiver les tags HTML. https://www.hacf.fr/ecole-directe/#retrait-des-tags-html"
                }
            )
            LOGGER.warning("[%s] Les attributs sont trop volumineux!", self._attr_name)
        result = super().extra_state_attributes
        result.update(
            {
                "Devoirs": attributes,
                "A faire": todo_counter,
            }
        )
        return result
