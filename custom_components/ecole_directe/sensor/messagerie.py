"""Messagerie sensor for ecole_directe."""

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
        key="messagerie",
        translation_key="messagerie",
        icon="mdi:email",
        has_entity_name=True,
    ),
)


class EDMessagerieSensor(EDGenericSensor):
    """Representation of a ED sensor."""

    def __init__(
        self,
        coordinator: EDDataUpdateCoordinator,
        entity_description: SensorEntityDescription,
        eleve: EDEleve | None,
    ) -> None:
        """Initialize the ED sensor."""
        super().__init__(
            coordinator,
            entity_description,
            "messagerie"
            if eleve is None
            else f"{eleve.get_fullname_lower()}_messagerie",
            "Messagerie",
            eleve,
            "len",
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        messagerie = {}
        if (
            self._child_info
            and f"{self._child_info.get_fullname_lower()}_messagerie"
            in self.coordinator.data
        ):
            messagerie = self.coordinator.data[
                f"{self._child_info.get_fullname_lower()}_messagerie"
            ]
        elif "messagerie" in self.coordinator.data:
            messagerie = self.coordinator.data["messagerie"]
        else:
            messagerie = {
                "messagesRecusCount": 0,
                "messagesEnvoyesCount": 0,
                "messagesArchivesCount": 0,
                "messagesRecusNotReadCount": 0,
                "messagesDraftCount": 0,
            }

        result = super().extra_state_attributes
        result.update(
            {
                "Reçus": messagerie["messagesRecusCount"],
                "Envoyés": messagerie["messagesEnvoyesCount"],
                "Archivés": messagerie["messagesArchivesCount"],
                "Non lu": messagerie["messagesRecusNotReadCount"],
                "Brouillons": messagerie["messagesDraftCount"],
            }
        )
        return result

    @property
    def native_value(self) -> str:
        """Return the state of the sensor."""
        messagerie = {}
        if (
            self._child_info
            and f"{self._child_info.get_fullname_lower()}_messagerie"
            in self.coordinator.data
        ):
            messagerie = self.coordinator.data[
                f"{self._child_info.get_fullname_lower()}_messagerie"
            ]
        elif "messagerie" in self.coordinator.data:
            messagerie = self.coordinator.data["messagerie"]
        else:
            return "0"

        return (
            str(messagerie["messagesRecusNotReadCount"])
            + "/"
            + str(messagerie["messagesRecusCount"])
        )
