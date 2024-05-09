"""Module providing sensors to Home Assistant."""

import logging
import operator

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.components.sensor import (
    SensorEntity,
)

from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
)

from .ecole_directe_formatter import format_grade, format_homework
from .ecole_directe_helper import EDEleve
from .coordinator import EDDataUpdateCoordinator
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up a bridge from a config entry."""

    coordinator: EDDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id][
        "coordinator"
    ]

    sensors = []
    if (
        coordinator.data is not None
        and "session" in coordinator.data
        and coordinator.data["session"].eleves is not None
    ):
        for eleve in coordinator.data["session"].eleves:
            sensors.append(EDChildSensor(coordinator, eleve))
            if "CAHIER_DE_TEXTES" in eleve.modules:
                sensors.append(EDHomeworksSensor(coordinator, eleve))
            if "NOTES" in eleve.modules:
                sensors.append(EDGradesSensor(coordinator, eleve))

        async_add_entities(sensors, False)


class EDGenericSensor(CoordinatorEntity, SensorEntity):
    """Representation of a ED sensor."""

    def __init__(
        self,
        coordinator,
        name: str,
        eleve: EDEleve = None,
        state: str = None,
        device_class: str = None,
    ) -> None:
        """Initialize the ED sensor."""
        super().__init__(coordinator)

        identifiant = self.coordinator.data["session"].identifiant

        if name == "":
            self._name = eleve.get_fullname_lower()
        else:
            self._name = f"{eleve.get_fullname_lower()}_{name}"
        self._state = state
        self._child_info = eleve
        self._attr_unique_id = f"ed_{identifiant}_{self._name}"
        self._attr_device_info = DeviceInfo(
            name=identifiant,
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, f"ED - {identifiant}")},
            manufacturer="Ecole Directe",
            model=f"ED - {identifiant}",
        )

        if device_class is not None:
            self._attr_device_class = device_class

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"{DOMAIN}_{self._name}"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if self._name not in self.coordinator.data:
            return "unavailable"
        elif self._state == "len":
            return len(self.coordinator.data[self._name])
        elif self._state is not None:
            return self._state
        return self.coordinator.data[self._name]

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return {"updated_at": self.coordinator.last_update_success_time}

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success and self._name in self.coordinator.data
        )


class EDChildSensor(EDGenericSensor):
    """Representation of a ED child sensor."""

    def __init__(self, coordinator: EDDataUpdateCoordinator, eleve: EDEleve) -> None:
        """Initialize the ED sensor."""
        super().__init__(coordinator, "", eleve, "len")
        self._attr_unique_id = f"ed_{eleve.get_fullname_lower()}_{eleve.eleve_id}]"
        self._account_type = self.coordinator.data["session"]._account_type

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"{DOMAIN}_{self._name}"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self._child_info.get_fullname()

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return {
            "firstname": self._child_info.eleve_firstname,
            "lastname": self._child_info.eleve_lastname,
            "full_name": self._child_info.get_fullname(),
            "class_name": self._child_info.classe_name,
            "establishment": self._child_info.establishment,
            "via_parent_account": self._account_type == "1",
            "updated_at": self.coordinator.last_update_success_time,
        }

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success


class EDHomeworksSensor(EDGenericSensor):
    """Representation of a ED sensor."""

    def __init__(self, coordinator: EDDataUpdateCoordinator, eleve: EDEleve) -> None:
        """Initialize the ED sensor."""
        super().__init__(
            coordinator,
            "homework",
            eleve,
            "len",
        )

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        attributes = []
        todo_counter = 0
        if f"{self._child_info.get_fullname_lower()}_homework" in self.coordinator.data:
            homeworks = self.coordinator.data[
                f"{self._child_info.get_fullname_lower()}_homework"
            ]
            for homework in homeworks:
                if not homework.effectue:
                    todo_counter += 1
                    attributes.append(format_homework(homework))
            if attributes is not None:
                attributes.sort(key=operator.itemgetter("date"))
        else:
            attributes.append(
                {
                    "Erreur": f"{self._child_info.get_fullname_lower()}_homework n'existe pas."
                }
            )

        return {
            "updated_at": self.coordinator.last_update_success_time,
            "homework": attributes,
            "todo_counter": todo_counter,
        }


class EDGradesSensor(EDGenericSensor):
    """Representation of a ED sensor."""

    def __init__(self, coordinator: EDDataUpdateCoordinator, eleve: EDEleve) -> None:
        """Initialize the ED sensor."""
        super().__init__(coordinator, "grades", eleve, "len")

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        attributes = []
        grades = self.coordinator.data[
            f"{self._child_info.get_fullname_lower()}_grades"
        ]
        for grade in grades:
            attributes.append(format_grade(grade))

        return {
            "updated_at": self.coordinator.last_update_success_time,
            "grades": attributes,
        }
