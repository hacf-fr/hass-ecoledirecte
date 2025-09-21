"""Module providing sensors to Home Assistant."""

import logging
import operator
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
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
    DEFAULT_LUNCH_BREAK_TIME,
    DOMAIN,
    FAKE_ON,
    MAX_STATE_ATTRS_BYTES,
)
from .coordinator import EDDataUpdateCoordinator
from .ecole_directe_helper import EDEleve

LOGGER = logging.getLogger(__name__)


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
        except Exception:
            LOGGER.exception("Error while creating generic sensors")

        for eleve in coordinator.data["session"].eleves:
            sensors.append(EDChildSensor(coordinator, eleve))
            # START: ADDED FOR WALLET SENSOR
            try:
                # We add the sensor regardless of modules, as it's often not listed.
                sensors.append(EDWalletSensor(coordinator, eleve))
            except Exception:
                LOGGER.exception("Error while creating wallet sensor: %s")
            # END: ADDED FOR WALLET SENSOR
            if FAKE_ON or "CAHIER_DE_TEXTES" in eleve.modules:
                try:
                    sensors.append(EDHomeworksSensor(coordinator, eleve, ""))
                    sensors.append(EDHomeworksSensor(coordinator, eleve, "_1"))
                    sensors.append(EDHomeworksSensor(coordinator, eleve, "_2"))
                    sensors.append(EDHomeworksSensor(coordinator, eleve, "_3"))
                except Exception:
                    LOGGER.exception("Error while creating homeworks sensors: %s")
            if FAKE_ON or "EDT" in eleve.modules:
                try:
                    sensors.append(EDLessonsSensor(coordinator, eleve, "today"))
                    sensors.append(EDLessonsSensor(coordinator, eleve, "tomorrow"))
                    sensors.append(EDLessonsSensor(coordinator, eleve, "next_day"))
                    sensors.append(EDLessonsSensor(coordinator, eleve, "period"))
                    sensors.append(EDLessonsSensor(coordinator, eleve, "period_1"))
                    sensors.append(EDLessonsSensor(coordinator, eleve, "period_2"))
                except Exception:
                    LOGGER.exception("Error while creating lessons sensors: %s")
            if FAKE_ON or "NOTES" in eleve.modules:
                try:
                    sensors.append(EDGradesSensor(coordinator, eleve))
                    sensors.append(EDEvaluationsSensor(coordinator, eleve))
                except Exception:
                    LOGGER.exception("Error while creating grades sensors: %s")
                try:
                    if f"{eleve.get_fullname_lower()}_disciplines" in coordinator.data:
                        disciplines = coordinator.data[
                            f"{eleve.get_fullname_lower()}_disciplines"
                        ]
                        for discipline in disciplines:
                            sensors.append(
                                EDDisciplineSensor(
                                    coordinator,
                                    eleve,
                                    discipline["name"],
                                    discipline["moyenne"],
                                )
                            )
                    if (
                        f"{eleve.get_fullname_lower()}_moyenne_generale"
                        in coordinator.data
                    ):
                        sensors.append(EDMoyenneSensor(coordinator, eleve))
                except Exception as e:
                    LOGGER.exception("Error while creating moyennes sensors: %s", e)

            if FAKE_ON or "VIE_SCOLAIRE" in eleve.modules:
                try:
                    sensors.append(EDAbsencesSensor(coordinator, eleve))
                    sensors.append(EDRetardsSensor(coordinator, eleve))
                    sensors.append(EDEncouragementsSensor(coordinator, eleve))
                    sensors.append(EDSanctionsSensor(coordinator, eleve))
                except Exception:
                    LOGGER.exception("Error while creating VIE_SCOLAIRE sensors: %s")
            if FAKE_ON or "MESSAGERIE" in coordinator.data["session"].modules:
                try:
                    sensors.append(EDMessagerieSensor(coordinator, eleve))
                except Exception:
                    LOGGER.exception(
                        "Error while creating student messagerie sensors: %s"
                    )

        async_add_entities(sensors, update_before_add=False)


class EDGenericSensor(CoordinatorEntity, SensorEntity):
    """Representation of a ED sensor."""

    def __init__(
        self,
        coordinator: EDDataUpdateCoordinator,
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
                self._name = identifiant
            else:
                self._name = eleve.get_fullname_lower()
        elif eleve is None:
            self._name = name
        else:
            self._name = f"{eleve.get_fullname_lower()}_{name}"
        self._child_info = eleve

        self._state = state
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
        return f"{DOMAIN}_{self._name}"

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        if self._name not in self.coordinator.data:
            return "unavailable"
        if self._state == "len":
            return len(self.coordinator.data[self._name])
        if self._state is not None:
            return self._state
        return self.coordinator.data[self._name]

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
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
        self._account_type = self.coordinator.data["session"].account_type

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return f"{DOMAIN}_{self._name}"

    @property
    def native_value(self) -> str:
        """Return the state of the sensor."""
        return self._child_info.get_fullname()

    @property
    def extra_state_attributes(self) -> dict[str, str]:
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


# START: NEW SENSOR CLASS FOR WALLET
class EDWalletSensor(EDGenericSensor):
    """Representation of an ED wallet sensor."""

    def __init__(self, coordinator: EDDataUpdateCoordinator, eleve: EDEleve) -> None:
        """Initialize the ED sensor."""
        super().__init__(coordinator, "wallet", eleve)
        self._child_info = eleve
        self._attr_device_class = SensorDeviceClass.MONETARY
        self._attr_native_unit_of_measurement = "EUR"
        self._attr_icon = "mdi:wallet"

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        key = f"{self._child_info.get_fullname_lower()}_wallet"
        wallet_data = self.coordinator.data.get(key)
        # Use the descriptive name from the API, e.g., "Restauration Noah"
        if wallet_data and wallet_data.get("libelle"):
            return wallet_data["libelle"]
        # Fallback name
        return f"{DOMAIN}_{self._child_info.get_fullname_lower()}_solde_cantine"

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the sensor."""
        return f"ed_{self.coordinator.data['session'].identifiant}_{self._child_info.get_fullname_lower()}_wallet"

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        key = f"{self._child_info.get_fullname_lower()}_wallet"
        wallet_data = self.coordinator.data.get(key)
        if wallet_data is not None:
            return wallet_data.get("solde")
        return None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        key = f"{self._child_info.get_fullname_lower()}_wallet"
        return (
            self.coordinator.last_update_success
            and key in self.coordinator.data
            and self.coordinator.data[key] is not None
        )


# END: NEW SENSOR CLASS FOR WALLET


class EDHomeworksSensor(EDGenericSensor):
    """Representation of a ED sensor."""

    def __init__(
        self, coordinator: EDDataUpdateCoordinator, eleve: EDEleve, suffix: str
    ) -> None:
        """Initialize the ED sensor."""
        super().__init__(
            coordinator,
            "homework" + suffix,
            eleve,
            "len",
        )
        self._child_info = eleve
        self._suffix = suffix

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        attributes = []
        todo_counter = 0
        if (
            f"{self._child_info.get_fullname_lower()}_homework{self._suffix}"
            in self.coordinator.data
        ):
            homeworks = self.coordinator.data[
                f"{self._child_info.get_fullname_lower()}_homework{self._suffix}"
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
            LOGGER.warning("[%s] attributes are too big! %s", self._name, attributes)

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
        self._child_info = eleve

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        attributes = []
        grades = self.coordinator.data[
            f"{self._child_info.get_fullname_lower()}_grades"
        ]
        for grade in grades:
            attributes.append(grade)

        return {
            "updated_at": self.coordinator.last_update_success_time,
            "grades": attributes,
        }


class EDDisciplineSensor(EDGenericSensor):
    """Representation of a ED sensor."""

    def __init__(
        self, coordinator: EDDataUpdateCoordinator, eleve: EDEleve, nom: str, note: Any
    ) -> None:
        """Initialize the ED sensor."""
        super().__init__(coordinator, nom, eleve, note)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        discipline = self.coordinator.data[self._name]

        return {
            "updated_at": self.coordinator.last_update_success_time,
            "code": discipline["code"],
            "nom": discipline["name"],
            "moyenneClasse": discipline["moyenneClasse"],
            "moyenneMin": discipline["moyenneMin"],
            "moyenneMax": discipline["moyenneMax"],
            "appreciations": discipline["appreciations"],
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
        lessons = self.coordinator.data[self._name]
        canceled_counter = None
        single_day = self._suffix in ["today", "tomorrow", "next_day"]
        lunch_break_time = datetime.strptime(
            DEFAULT_LUNCH_BREAK_TIME,
            "%H:%M",
        ).time()

        if lessons is not None:
            self._start_at = None
            self._end_at = None
            self._lunch_break_start_at = None
            self._lunch_break_end_at = None
            self._date = None
            canceled_counter = 0
            for lesson in lessons:
                index = lessons.index(lesson)

                if not (
                    lesson["start_time"] == lessons[index - 1]["start_time"]
                    and lesson["canceled"]
                ):
                    attributes.append(lesson)
                    self._date = lesson["start"].strftime("%Y-%m-%d")
                if lesson["canceled"]:
                    canceled_counter += 1
                if single_day and lesson["canceled"] is False:
                    start = lesson["start"].strftime("%H:%M")
                    if self._start_at is None or start < self._start_at:
                        self._start_at = start
                    end = lesson["end"].strftime("%H:%M")
                    if self._end_at is None or end > self._end_at:
                        self._end_at = end
                    if (
                        datetime.strptime(lesson["end_time"], "%H:%M").time()
                        < lunch_break_time
                    ):
                        self._lunch_break_start_at = lesson["end"]
                    if (
                        self._lunch_break_end_at is None
                        and datetime.strptime(lesson["start_time"], "%H:%M").time()
                        >= lunch_break_time
                    ):
                        self._lunch_break_end_at = lesson["start"]
        if is_too_big(attributes):
            LOGGER.warning("[%s] attributes are too big! %s", self._name, attributes)
            attributes = []
        result = {
            "updated_at": self.coordinator.last_update_success_time,
            "lessons": attributes,
            "canceled_lessons_counter": canceled_counter,
        }

        if single_day:
            result["lunch_break_start_at"] = self._lunch_break_start_at
            result["lunch_break_end_at"] = self._lunch_break_end_at
            result["day_start_at"] = self._start_at
            result["day_end_at"] = self._end_at
            result["date"] = self._date

        return result


class EDMoyenneSensor(EDGenericSensor):
    """Representation of a ED sensor."""

    def __init__(self, coordinator: EDDataUpdateCoordinator, eleve: EDEleve) -> None:
        """Initialize the ED sensor."""
        super().__init__(coordinator, "moyenne_generale", eleve)
        self._child_info = eleve
        self._state = self.coordinator.data[self._name]["moyenneGenerale"]

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        moyenne = self.coordinator.data[
            f"{self._child_info.get_fullname_lower()}_moyenne_generale"
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
        self._child_info = eleve

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        attributes = []
        evaluations = self.coordinator.data[
            f"{self._child_info.get_fullname_lower()}_evaluations"
        ]
        for evaluation in evaluations:
            attributes.append(evaluation)

        return {
            "updated_at": self.coordinator.last_update_success_time,
            "evaluations": attributes,
        }


class EDAbsencesSensor(EDGenericSensor):
    """Representation of a ED sensor."""

    def __init__(self, coordinator: EDDataUpdateCoordinator, eleve: EDEleve) -> None:
        """Initialize the ED sensor."""
        super().__init__(coordinator, "absences", eleve, "len")
        self._child_info = eleve

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        attributes = []
        absences = self.coordinator.data[
            f"{self._child_info.get_fullname_lower()}_absences"
        ]
        for absence in absences:
            attributes.append(absence)

        return {
            "updated_at": self.coordinator.last_update_success_time,
            "absences": attributes,
        }


class EDRetardsSensor(EDGenericSensor):
    """Representation of a ED sensor."""

    def __init__(self, coordinator: EDDataUpdateCoordinator, eleve: EDEleve) -> None:
        """Initialize the ED sensor."""
        super().__init__(coordinator, "retards", eleve, "len")
        self._child_info = eleve

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        attributes = []
        retards = self.coordinator.data[
            f"{self._child_info.get_fullname_lower()}_retards"
        ]
        for retard in retards:
            attributes.append(retard)

        return {
            "updated_at": self.coordinator.last_update_success_time,
            "delays": attributes,
        }


class EDSanctionsSensor(EDGenericSensor):
    """Representation of a ED sensor."""

    def __init__(self, coordinator: EDDataUpdateCoordinator, eleve: EDEleve) -> None:
        """Initialize the ED sensor."""
        super().__init__(coordinator, "sanctions", eleve, "len")
        self._child_info = eleve

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        attributes = []
        sanctions = self.coordinator.data[
            f"{self._child_info.get_fullname_lower()}_sanctions"
        ]
        for sanction in sanctions:
            attributes.append(sanction)

        return {
            "updated_at": self.coordinator.last_update_success_time,
            "sanctions": attributes,
        }


class EDEncouragementsSensor(EDGenericSensor):
    """Representation of a ED sensor."""

    def __init__(self, coordinator: EDDataUpdateCoordinator, eleve: EDEleve) -> None:
        """Initialize the ED sensor."""
        super().__init__(coordinator, "encouragements", eleve, "len")
        self._child_info = eleve

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        attributes = []
        encouragements = self.coordinator.data[
            f"{self._child_info.get_fullname_lower()}_encouragements"
        ]
        for encouragement in encouragements:
            attributes.append(encouragement)

        return {
            "updated_at": self.coordinator.last_update_success_time,
            "encouragements": attributes,
        }


class EDFormulairesSensor(EDGenericSensor):
    """Representation of a ED sensor."""

    def __init__(self, coordinator: EDDataUpdateCoordinator) -> None:
        """Initialize the ED sensor."""
        super().__init__(coordinator, "formulaires", None, "len")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        attributes = []
        forms = self.coordinator.data["formulaires"]
        for form in forms:
            attributes.append(form)

        return {
            "updated_at": self.coordinator.last_update_success_time,
            "formulaires": attributes,
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
        if self._child_info:
            messagerie = self.coordinator.data[
                f"{self._child_info.get_fullname_lower()}_messagerie"
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
