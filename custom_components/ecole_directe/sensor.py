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

from .ecoleDirecte_helper import *
from .coordinator import EDDataUpdateCoordinator
from .const import (
    DOMAIN,
)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: EDDataUpdateCoordinator = hass.data[DOMAIN][
        config_entry.entry_id
    ]["coordinator"]

    sensors = []

    eleves = coordinator.data["session"].eleves
    for eleve in eleves:
        sensors.append(EDChildSensor(coordinator, eleve))
        if "CAHIER_DE_TEXTES" in eleve.modules:
            sensors.append(EDHomeworkSensor(coordinator, eleve))
        if "NOTES" in eleve.modules:
            sensors.append(EDNotesSensor(coordinator, eleve))

    async_add_entities(sensors, False)

class EDGenericSensor(CoordinatorEntity, SensorEntity):
    """Representation of a ED sensor."""

    def __init__(self, coordinator, coordinator_key: str, name: str, eleve: ED_Eleve = None, state: str = None, device_class: str = None) -> None:
        """Initialize the ED sensor."""
        super().__init__(coordinator)
        self._coordinator_key = coordinator_key
        self._name = f"{eleve.get_fullnameLower()}_{name}" if eleve != None else name
        self._state = state
        self._attr_unique_id = f"ed-{self.coordinator.data["session"].identifiant}-{self._name}"
        id = eleve.get_fullname() if eleve != None else self.coordinator.data["session"].identifiant
        self._attr_device_info = DeviceInfo(
            name = f"ED - {id}",
            entry_type = DeviceEntryType.SERVICE,
            identifiers = {
                (DOMAIN, f"ED - {id}")
            },
            manufacturer = "EcoleDirecte",
            model = id,
        )
        if (device_class is not None):
            self._attr_device_class = device_class

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"{DOMAIN}_{self._name}"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if self.coordinator.data[self._coordinator_key] is None:
            return 'unavailable'
        elif self._state == 'len':
            return len(self.coordinator.data[self._coordinator_key])
        elif self._state is not None:
            return self._state
        return self.coordinator.data[self._coordinator_key]

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return {
            'updated_at': self.coordinator.last_update_success_time
        }

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success and self._coordinator_key in self.coordinator.data

class EDChildSensor(CoordinatorEntity, SensorEntity):
    """Representation of a ED child sensor."""

    def __init__(self, coordinator, eleve: ED_Eleve) -> None:
        """Initialize the ED sensor."""
        super().__init__(coordinator)
        self._child_info = eleve
        self._attr_unique_id = f"ed-{eleve.get_fullnameLower()}-{eleve.eleve_id}]"
        self._attr_device_info = DeviceInfo(
            name=f"ED - {eleve.get_fullname()}",
            entry_type=DeviceEntryType.SERVICE,
            identifiers={
                (DOMAIN, f"ED - {eleve.get_fullname()}")
            },
            manufacturer="Ecole Directe",
            model=eleve.get_fullname(),
        )

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"{DOMAIN}_{self._child_info.get_fullname()}"

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
            "updated_at": self.coordinator.last_update_success_time
        }

class EDHomeworkSensor(EDGenericSensor):
    """Representation of a ED sensor."""

    def __init__(self, coordinator: EDDataUpdateCoordinator, eleve: ED_Eleve) -> None:
        """Initialize the ED sensor."""
        super().__init__(coordinator, 'homework' + str(eleve.eleve_id), 'homework' + str(eleve.eleve_id), eleve, 'len')
        self._suffix = eleve.eleve_id


class EDNotesSensor(EDGenericSensor):
    """Representation of a ED sensor."""

    def __init__(self, coordinator: EDDataUpdateCoordinator, eleve: ED_Eleve) -> None:
        """Initialize the ED sensor."""
        super().__init__(coordinator, 'notes' + str(eleve.eleve_id), 'notes' + str(eleve.eleve_id), eleve, 'len')
        self._suffix = eleve.eleve_id
