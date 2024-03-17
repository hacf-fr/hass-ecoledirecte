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

from .ecoleDirecte_helper import ED_Eleve, ED_Devoir, ED_Note
from .coordinator import EDDataUpdateCoordinator
from .const import (
    DOMAIN,
    NOTES_TO_DISPLAY,
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: EDDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id][
        "coordinator"
    ]

    sensors = []

    for eleve in coordinator.data["session"].eleves:
        sensors.append(EDChildSensor(coordinator, eleve))
        if "CAHIER_DE_TEXTES" in eleve.modules:
            sensors.append(EDDevoirsSensor(coordinator, eleve))
        if "NOTES" in eleve.modules:
            sensors.append(EDNotesSensor(coordinator, eleve))

    async_add_entities(sensors, False)


class EDGenericSensor(CoordinatorEntity, SensorEntity):
    """Representation of a ED sensor."""

    def __init__(
        self,
        coordinator,
        name: str,
        eleve: ED_Eleve = None,
        state: str = None,
        device_class: str = None,
    ) -> None:
        """Initialize the ED sensor."""
        super().__init__(coordinator)

        identifiant = self.coordinator.data["session"].identifiant

        self._name = name
        self._state = state
        self._child_info = eleve
        self._attr_unique_id = f"ed_{identifiant}_{self._name}"
        self._attr_device_info = DeviceInfo(
            name=identifiant,
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, f"ED - {identifiant}")},
            manufacturer="Ecole Directe",
            model=str(f"ED - {identifiant}"),
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

    def __init__(self, coordinator: EDDataUpdateCoordinator, eleve: ED_Eleve) -> None:
        """Initialize the ED sensor."""
        super().__init__(coordinator, eleve.get_fullname(), eleve, "len")
        self._attr_unique_id = f"ed_{eleve.get_fullnameLower()}_{eleve.eleve_id}]"

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._child_info.get_fullname()

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self._child_info.get_fullname()

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return {
            "full_name": self._child_info.get_fullname(),
            "class_name": self._child_info.classe_name,
            "updated_at": self.coordinator.last_update_success_time,
        }

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success


class EDDevoirsSensor(EDGenericSensor):
    """Representation of a ED sensor."""

    def __init__(self, coordinator: EDDataUpdateCoordinator, eleve: ED_Eleve) -> None:
        """Initialize the ED sensor."""
        super().__init__(
            coordinator, "devoirs" + eleve.get_fullnameLower(), eleve, "len"
        )

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        attributes = []
        todo_counter = 0
        if f"devoirs{self._child_info.get_fullnameLower()}" in self.coordinator.data:
            for date in self.coordinator.data[
                f"devoirs{self._child_info.get_fullnameLower()}"
            ]:
                for devoirs in date:
                    for devoir_json in devoirs:
                        devoir = ED_Devoir(devoir_json, date)
                        if devoir is not None:
                            attributes.append(devoir.format())
                            if devoir.effectue is False:
                                todo_counter += 1
        else:
            attributes.append(
                {
                    "Erreur": f"devoirs{self._child_info.get_fullnameLower()} n'existe pas."
                }
            )

        return {
            "updated_at": self.coordinator.last_update_success_time,
            "devoirs": attributes,
            "todo_counter": todo_counter,
        }


class EDNotesSensor(EDGenericSensor):
    """Representation of a ED sensor."""

    def __init__(self, coordinator: EDDataUpdateCoordinator, eleve: ED_Eleve) -> None:
        """Initialize the ED sensor."""
        super().__init__(coordinator, "notes" + eleve.get_fullnameLower(), eleve, "len")

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        attributes = []
        notes = self.coordinator.data["notes" + self._child_info.get_fullnameLower()]
        index_note = 0
        if notes is not None:
            for note in notes:
                index_note += 1
                if index_note == NOTES_TO_DISPLAY:
                    break
                n = ED_Note(note)
                attributes.append(n.format())

        return {
            "updated_at": self.coordinator.last_update_success_time,
            "evaluations": attributes,
        }
