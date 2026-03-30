"""Formulaires sensor for ecole_directe."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.components.sensor import (
    SensorEntityDescription,
    SensorStateClass,
)

from custom_components.ecole_directe.sensor.generic import EDGenericSensor

if TYPE_CHECKING:
    from custom_components.ecole_directe.coordinator import EDDataUpdateCoordinator

ENTITY_DESCRIPTIONS = (
    SensorEntityDescription(
        key="formulaires",
        translation_key="formulaires",
        icon="mdi:form-select",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        has_entity_name=True,
    ),
)


class EDFormulairesSensor(EDGenericSensor):
    """Representation of a ED sensor."""

    def __init__(
        self,
        coordinator: EDDataUpdateCoordinator,
        entity_description: SensorEntityDescription,
    ) -> None:
        """Initialize the ED sensor."""
        super().__init__(
            coordinator, entity_description, "formulaires", "Formulaires", None, "len"
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        attributes = []
        if "formulaires" in self.coordinator.data:
            forms = self.coordinator.data["formulaires"]
            for form in forms:
                attributes.append(form)

        result = super().extra_state_attributes
        result.update(
            {
                "Formulaires": attributes,
            }
        )
        return result
