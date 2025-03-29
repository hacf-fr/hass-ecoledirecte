"""Module providing sensors to Home Assistant."""

from datetime import datetime
import operator

from homeassistant.components.sensor import (
    SensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.json import (
    json_bytes,
)
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
)

from .const import (
    FAKE_ON,
    DEFAULT_LUNCH_BREAK_TIME,
    DOMAIN,
    LOGGER,
    MAX_STATE_ATTRS_BYTES,
)
from .coordinator import EDDataUpdateCoordinator
from .ecole_directe_helper import EDEleve


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
        try:
            if "EDFORMS" in coordinator.data["session"].modules:
                sensors.append(EDFormulairesSensor(coordinator))
            if "MESSAGERIE" in coordinator.data["session"].modules:
                sensors.append(EDMessagerieSensor(coordinator, None))
        except Exception as e:
            LOGGER.error("Error while creating generic sensors: %s", e)

        for eleve in coordinator.data["session"].eleves:
            sensors.append(EDChildSensor(coordinator, eleve))
            if FAKE_ON or "CAHIER_DE_TEXTES" in eleve.modules:
                try:
                    sensors.append(EDHomeworksSensor(coordinator, eleve, ""))
                    sensors.append(EDHomeworksSensor(coordinator, eleve, "_1"))
                    sensors.append(EDHomeworksSensor(coordinator, eleve, "_2"))
                    sensors.append(EDHomeworksSensor(coordinator, eleve, "_3"))
                except Exception as e:
                    LOGGER.error("Error while creating homeworks sensors: %s", e)
            if FAKE_ON or "EDT" in eleve.modules:
                try:
                    sensors.append(EDLessonsSensor(coordinator, eleve, "today"))
                    sensors.append(EDLessonsSensor(coordinator, eleve, "tomorrow"))
                    sensors.append(EDLessonsSensor(coordinator, eleve, "next_day"))
                    sensors.append(EDLessonsSensor(coordinator, eleve, "period"))
                    sensors.append(EDLessonsSensor(coordinator, eleve, "period_1"))
                    sensors.append(EDLessonsSensor(coordinator, eleve, "period_2"))
                except Exception as e:
                    LOGGER.error("Error while creating lessons sensors: %s", e)
            if FAKE_ON or "NOTES" in eleve.modules:
                try:
                    sensors.append(EDGradesSensor(coordinator, eleve))
                    sensors.append(EDEvaluationsSensor(coordinator, eleve))
                except Exception as e:
                    LOGGER.error("Error while creating grades sensors: %s", e)
                try:
                    disciplines = coordinator.data[
                        f"{eleve.get_fullname_lower()}_disciplines"
                    ]
                    sensors.extend(disciplines)
                    if (
                        f"{eleve.get_fullname_lower()}_moyenne_generale"
                        in coordinator.data
                    ):
                        sensors.append(EDMoyenneSensor(coordinator, eleve))
                except Exception as e:
                    LOGGER.error("Error while creating moyennes sensors: %s", e)

            if FAKE_ON or "VIE_SCOLAIRE" in eleve.modules:
                try:
                    sensors.append(EDAbsencesSensor(coordinator, eleve))
                    sensors.append(EDRetardsSensor(coordinator, eleve))
                    sensors.append(EDEncouragementsSensor(coordinator, eleve))
                    sensors.append(EDSanctionsSensor(coordinator, eleve))
                except Exception as e:
                    LOGGER.error("Error while creating VIE_SCOLAIRE sensors: %s", e)
            if FAKE_ON or "MESSAGERIE" in coordinator.data["session"].modules:
                try:
                    sensors.append(EDMessagerieSensor(coordinator, eleve))
                except Exception as e:
                    LOGGER.error(
                        "Error while creating student messagerie sensors: %s", e
                    )

        async_add_entities(sensors, update_before_add=False)


class EDGenericSensor(CoordinatorEntity, SensorEntity):
    """Representation of a ED sensor."""

    def __init__(
        self,
        coordinator: Any,
        name: str,
        eleve: EDEleve | None = None,
        state: str | None = None,
        device_class: str | None = None,
    ) -> None:
        """Initialize the ED sensor."""
        super().__init__(coordinator)

        identifiant = self.coordinator.data["session"].identifiant

        if name == "":
            if eleve is None:
                self.name = identifiant
            else:
                self._name = eleve.get_fullname_lower()
        elif eleve is None:
            self._name = name
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
    def name(self) -> str:
        """Return the name of the sensor."""
        return f"{DOMAIN}_{self.name}"

    @property
    def native_value(self) -> int | Any | Literal["unavailable"]:
        """Return the state of the sensor."""
        if self.name not in self.coordinator.data:
            return "unavailable"
        if self.state == "len":
            return len(self.coordinator.data[self.name])
        if self.state is not None:
            return self.state
        return self.coordinator.data[self.name]

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        return {"updated_at": self.coordinator.last_update_success_time}

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success and self.name in self.coordinator.data
        )


class EDChildSensor(EDGenericSensor):
    """Representation of a ED child sensor."""

    def __init__(self, coordinator: EDDataUpdateCoordinator, eleve: EDEleve) -> None:
        """Initialize the ED sensor."""
        super().__init__(coordinator, "", eleve, "len")
        self._attr_unique_id = f"ed_{eleve.get_fullname_lower()}_{eleve.eleve_id}]"
        self._account_type = self.coordinator.data["session"].account_type

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return f"{DOMAIN}_{self.name}"

    @property
    def native_value(self) -> str:
        """Return the state of the sensor."""
        return self.child_info.get_fullname()

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        return {
            "firstname": self.child_info.eleve_firstname,
            "lastname": self.child_info.eleve_lastname,
            "full_name": self.child_info.get_fullname(),
            "class_name": self.child_info.classe_name,
            "establishment": self.child_info.establishment,
            "via_parent_account": self.account_type == "1",
            "updated_at": self.coordinator.last_update_success_time,
        }

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success


class EDHomeworksSensor(EDGenericSensor):
    """Representation of a ED sensor."""

    def __init__(
        self, coordinator: EDDataUpdateCoordinator, eleve: EDEleve, suffix: Any
    ) -> None:
        """Initialize the ED sensor."""
        super().__init__(
            coordinator,
            "homework" + suffix,
            eleve,
            "len",
        )
        self._suffix = suffix

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        attributes = []
        todo_counter = 0
        if (
            f"{self.child_info.get_fullname_lower()}_homework{self._suffix}"
            in self.coordinator.data
        ):
            homeworks = self.coordinator.data[
                f"{self.child_info.get_fullname_lower()}_homework{self._suffix}"
            ]
            for homework in homeworks:
                if not homework["done"]:
                    todo_counter += 1
                attributes.append(homework)
            if attributes is not None:
                attributes.sort(key=operator.itemgetter("date"))
        else:
            attributes.append({
                "Erreur": f"{self._child_info.get_fullname_lower()}_homework{self._suffix} n'existe pas."
            })

        if is_too_big(attributes):
            attributes = []
            LOGGER.warning("[%s] attributes are too big! %s", self.name, attributes)

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
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        return {
            "updated_at": self.coordinator.last_update_success_time,
            "grades": list(
                self.coordinator.data[f"{self.child_info.get_fullname_lower()}_grades"]
            ),
        }


class EDLessonsSensor(EDGenericSensor):
    """Representation of a ED sensor."""

    def __init__(
        self, coordinator: EDDataUpdateCoordinator, eleve: EDEleve, suffix: str
    ) -> None:
        """Initialize the ED sensor."""
        super().__init__(
            coordinator, name="timetable_" + suffix, eleve=eleve, state="len"
        )
        self._suffix = suffix
        self._start_at = None
        self._end_at = None
        self._lunch_break_start_at = None
        self._lunch_break_end_at = None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        attributes = []
        lessons = self.coordinator.data[self.name]
        canceled_counter = None
        single_day = self._suffix in ["today", "tomorrow", "next_day"]
        lunch_break_time = (
            datetime.strptime(
                DEFAULT_LUNCH_BREAK_TIME,
                "%H:%M",
            )
            .astimezone(self.hass.config.time_zone)
            .time()
        )

        if lessons is not None:
            self._start_at = None
            self._end_at = None
            self._lunch_break_start_at = None
            self._lunch_break_end_at = None
            canceled_counter = 0
            for lesson in lessons:
                index = lessons.index(lesson)

                if not (
                    lesson["start_time"] == lessons[index - 1]["start_time"]
                    and lesson["canceled"]
                ):
                    attributes.append(lesson)
                if lesson["canceled"] is False and self._start_at is None:
                    self._start_at = lesson["start"].strftime("%H:%M")
                if lesson["canceled"]:
                    canceled_counter += 1
                if single_day and not lesson["canceled"]:
                    self._end_at = lesson["end"].strftime("%H:%M")
                    if (
                        datetime.strptime(lesson["end_time"], "%H:%M")
                        .astimezone(self.hass.config.time_zone)
                        .time()
                        < lunch_break_time
                    ):
                        self._lunch_break_start_at = lesson["end"]
                    if (
                        self._lunch_break_end_at is None
                        and datetime.strptime(lesson["start_time"], "%H:%M")
                        .astimezone(self.hass.config.time_zone)
                        .time()
                        >= lunch_break_time
                    ):
                        self._lunch_break_end_at = lesson["start"]
        if is_too_big(attributes):
            LOGGER.warning("[%s] attributes are too big! %s", self.name, attributes)
            attributes = []
        result = {
            "updated_at": self.coordinator.last_update_success_time,
            "lessons": attributes,
            "canceled_lessons_counter": canceled_counter,
            "day_start_at": self._start_at,
            "day_end_at": self._end_at,
        }

        if single_day:
            result["lunch_break_start_at"] = self._lunch_break_start_at
            result["lunch_break_end_at"] = self._lunch_break_end_at

        return result


class EDMoyenneSensor(EDGenericSensor):
    """Representation of a ED sensor."""

    def __init__(self, coordinator: EDDataUpdateCoordinator, eleve: EDEleve) -> None:
        """Initialize the ED sensor."""
        super().__init__(coordinator, "moyenne_generale", eleve)
        self._state = self.coordinator.data[self.name]["moyenneGenerale"]

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        moyenne = self.coordinator.data[
            f"{self.child_info.get_fullname_lower()}_moyenne_generale"
        ]

        return {
            "updated_at": self.coordinator.last_update_success_time,
            "moyenneClasse": moyenne["moyenneClasse"],
            "moyenneMin": moyenne["moyenneMin"],
            "moyenneMax": moyenne["moyenneMax"],
            "dateCalcul": moyenne["dateCalcul"],
        }


class EDEvaluationsSensor(EDGenericSensor):
    """Representation of a ED sensor."""

    def __init__(self, coordinator: EDDataUpdateCoordinator, eleve: EDEleve) -> None:
        """Initialize the ED sensor."""
        super().__init__(coordinator, "evaluations", eleve, "len")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        return {
            "updated_at": self.coordinator.last_update_success_time,
            "evaluations": list(
                self.coordinator.data[
                    f"{self.child_info.get_fullname_lower()}_evaluations"
                ]
            ),
        }


class EDAbsencesSensor(EDGenericSensor):
    """Representation of a ED sensor."""

    def __init__(self, coordinator: EDDataUpdateCoordinator, eleve: EDEleve) -> None:
        """Initialize the ED sensor."""
        super().__init__(coordinator, "absences", eleve, "len")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        return {
            "updated_at": self.coordinator.last_update_success_time,
            "absences": list(
                self.coordinator.data[
                    f"{self.child_info.get_fullname_lower()}_absences"
                ]
            ),
        }


class EDRetardsSensor(EDGenericSensor):
    """Representation of a ED sensor."""

    def __init__(self, coordinator: EDDataUpdateCoordinator, eleve: EDEleve) -> None:
        """Initialize the ED sensor."""
        super().__init__(coordinator, "retards", eleve, "len")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        return {
            "updated_at": self.coordinator.last_update_success_time,
            "delays": list(
                self.coordinator.data[f"{self.child_info.get_fullname_lower()}_retards"]
            ),
        }


class EDSanctionsSensor(EDGenericSensor):
    """Representation of a ED sensor."""

    def __init__(self, coordinator: EDDataUpdateCoordinator, eleve: EDEleve) -> None:
        """Initialize the ED sensor."""
        super().__init__(coordinator, "sanctions", eleve, "len")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        return {
            "updated_at": self.coordinator.last_update_success_time,
            "sanctions": list(
                self.coordinator.data[
                    f"{self.child_info.get_fullname_lower()}_sanctions"
                ]
            ),
        }


class EDEncouragementsSensor(EDGenericSensor):
    """Representation of a ED sensor."""

    def __init__(self, coordinator: EDDataUpdateCoordinator, eleve: EDEleve) -> None:
        """Initialize the ED sensor."""
        super().__init__(coordinator, "encouragements", eleve, "len")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        return {
            "updated_at": self.coordinator.last_update_success_time,
            "encouragements": list(
                self.coordinator.data[
                    f"{self.child_info.get_fullname_lower()}_encouragements"
                ]
            ),
        }


class EDFormulairesSensor(EDGenericSensor):
    """Representation of a ED sensor."""

    def __init__(self, coordinator: EDDataUpdateCoordinator) -> None:
        """Initialize the ED sensor."""
        super().__init__(coordinator, "formulaires", None, "len")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        return {
            "updated_at": self.coordinator.last_update_success_time,
            "formulaires": list(self.coordinator.data["formulaires"]),
        }


class EDMessagerieSensor(EDGenericSensor):
    """Representation of a ED sensor."""

    def __init__(
        self, coordinator: EDDataUpdateCoordinator, eleve: EDEleve | None
    ) -> None:
        """Initialize the ED sensor."""
        super().__init__(coordinator, "messagerie", eleve, "len")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        if self.child_info:
            messagerie = self.coordinator.data[
                f"{self.child_info.get_fullname_lower()}_messagerie"
            ]
        else:
            messagerie = self.coordinator.data["messagerie"]

        return {
            "updated_at": self.coordinator.last_update_success_time,
            "reçus": messagerie["messagesRecusCount"],
            "envoyés": messagerie["messagesEnvoyesCount"],
            "archivés": messagerie["messagesArchivesCount"],
            "non lu": messagerie["messagesRecusNotReadCount"],
            "brouillons": messagerie["messagesDraftCount"],
        }


def is_too_big(obj: Any) -> bool:
    """Calculate is_too_big."""
    bytes_result = json_bytes(obj)
    return len(bytes_result) > MAX_STATE_ATTRS_BYTES
