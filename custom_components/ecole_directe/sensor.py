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
from .ecole_directe_helper import EDEleve, get_unique_id

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
            # We add the sensor regardless of modules, as it's often not listed.
            if "wallets" in coordinator.data:
                wallets = coordinator.data["wallets"]
                for wallet in wallets:
                    sensors.append(
                        EDWalletSensor(
                            coordinator, wallet["libelle"], None, wallet["solde"]
                        )
                    )

        except Exception:
            LOGGER.exception("Error while creating generic sensors")

        for eleve in coordinator.data["session"].eleves:
            sensors.append(EDChildSensor(coordinator, eleve))
            # START: ADDED FOR WALLET SENSOR
            try:
                # We add the sensor regardless of modules, as it's often not listed.
                if f"{eleve.get_fullname_lower()}_wallets" in coordinator.data:
                    wallets = coordinator.data[f"{eleve.get_fullname_lower()}_wallets"]
                    for wallet in wallets:
                        sensors.append(
                            EDWalletSensor(
                                coordinator, wallet["libelle"], eleve, wallet["solde"]
                            )
                        )
            except Exception:
                LOGGER.exception("Error while creating wallet sensors")
            # END: ADDED FOR WALLET SENSOR
            if FAKE_ON or "CAHIER_DE_TEXTES" in eleve.modules:
                try:
                    sensors.append(EDHomeworksSensor(coordinator, eleve, "_1"))
                    sensors.append(EDHomeworksSensor(coordinator, eleve, "_2"))
                    sensors.append(EDHomeworksSensor(coordinator, eleve, "_3"))
                    sensors.append(EDHomeworksSensor(coordinator, eleve, "_today"))
                    sensors.append(EDHomeworksSensor(coordinator, eleve, "_tomorrow"))
                    sensors.append(EDHomeworksSensor(coordinator, eleve, "_next_day"))
                    sensors.append(EDHomeworksSensor(coordinator, eleve, ""))
                except Exception:
                    LOGGER.exception("Error while creating homeworks sensors")
            if FAKE_ON or "EDT" in eleve.modules:
                try:
                    sensors.append(EDLessonsSensor(coordinator, eleve, "_1"))
                    sensors.append(EDLessonsSensor(coordinator, eleve, "_2"))
                    sensors.append(EDLessonsSensor(coordinator, eleve, "_3"))
                    sensors.append(EDLessonsSensor(coordinator, eleve, "_today"))
                    sensors.append(EDLessonsSensor(coordinator, eleve, "_tomorrow"))
                    sensors.append(EDLessonsSensor(coordinator, eleve, "_next_day"))
                except Exception:
                    LOGGER.exception("Error while creating lessons sensors")
            if FAKE_ON or "NOTES" in eleve.modules:
                try:
                    sensors.append(EDGradesSensor(coordinator, eleve))
                    sensors.append(EDEvaluationsSensor(coordinator, eleve))
                except Exception:
                    LOGGER.exception("Error while creating grades sensors")
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
                        sensors.append(EDMoyenneGeneraleSensor(coordinator, eleve))
                except Exception:
                    LOGGER.exception("Error while creating moyennes sensors")

            if FAKE_ON or "VIE_SCOLAIRE" in eleve.modules:
                try:
                    sensors.append(EDAbsencesSensor(coordinator, eleve))
                    sensors.append(EDRetardsSensor(coordinator, eleve))
                    sensors.append(EDEncouragementsSensor(coordinator, eleve))
                    sensors.append(EDSanctionsSensor(coordinator, eleve))
                except Exception:
                    LOGGER.exception("Error while creating VIE_SCOLAIRE sensors")
            if FAKE_ON or "MESSAGERIE" in eleve.modules:
                try:
                    sensors.append(EDMessagerieSensor(coordinator, eleve))
                except Exception:
                    LOGGER.exception("Error while creating student messagerie sensors")

        async_add_entities(sensors, update_before_add=False)


class EDGenericSensor(CoordinatorEntity, SensorEntity):
    """Representation of a ED sensor."""

    def __init__(
        self,
        coordinator: EDDataUpdateCoordinator,
        key: str,
        name: str,
        eleve: EDEleve | None = None,
        state: str | int | None = None,
    ) -> None:
        """Initialize the ED sensor."""
        super().__init__(coordinator)

        identifiant = self.coordinator.data["session"].identifiant
        device = (
            f"ED - {identifiant}" if eleve is None else f"ED - {eleve.get_fullname()}"
        )

        self._key = get_unique_id(key)
        self._child_info = eleve
        self._state = state
        self.unique_id = (
            f"ed_{identifiant}_{self._key}" if eleve is None else f"ed_{self._key}"
        )
        self._attr_name = name
        self._attr_has_entity_name = True

        self._attr_device_info = DeviceInfo(
            name=device,
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, device)},
            manufacturer="Ecole Directe",
            model=device,
        )

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        if self._key not in self.coordinator.data:
            return "unavailable"
        if self._state is not None:
            if self._state == "len":
                return len(self.coordinator.data[self._key])
            return self._state
        return self.coordinator.data[self._key]

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        if self._child_info is None:
            return {}

        return {"prenom": self._child_info.eleve_firstname}

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success and self._key in self.coordinator.data
        )


class EDChildSensor(EDGenericSensor):
    """Representation of a ED child sensor."""

    def __init__(self, coordinator: EDDataUpdateCoordinator, eleve: EDEleve) -> None:
        """Initialize the ED sensor."""
        super().__init__(
            coordinator=coordinator,
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


class EDWalletSensor(EDGenericSensor):
    """Representation of an ED wallet sensor."""

    def __init__(
        self,
        coordinator: EDDataUpdateCoordinator,
        libelle: str = "wallet",
        eleve: EDEleve | None = None,
        solde: int = 0,
    ) -> None:
        """Initialize the ED sensor."""
        super().__init__(
            coordinator,
            "wallets" if eleve is None else f"{eleve.get_fullname_lower()}_wallets",
            libelle,
            eleve,
            solde,
        )
        self._attr_device_class = SensorDeviceClass.MONETARY
        self._attr_native_unit_of_measurement = "EUR"
        self._attr_icon = "mdi:wallet"

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        if self._key not in self.coordinator.data:
            return "unavailable"
        wallet = next(
            item
            for item in self.coordinator.data[self._key]
            if item.get("libelle") == self._attr_name
        )
        if wallet is None:
            return "unavailable"
        return wallet["solde"]

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success and self._key in self.coordinator.data
        )


class EDHomeworksSensor(EDGenericSensor):
    """Representation of a ED sensor."""

    def __init__(
        self, coordinator: EDDataUpdateCoordinator, eleve: EDEleve, suffix: str
    ) -> None:
        """Initialize the ED sensor."""
        super().__init__(
            coordinator,
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


class EDGradesSensor(EDGenericSensor):
    """Representation of a ED sensor."""

    def __init__(self, coordinator: EDDataUpdateCoordinator, eleve: EDEleve) -> None:
        """Initialize the ED sensor."""
        super().__init__(
            coordinator, f"{eleve.get_fullname_lower()}_notes", "Notes", eleve, "len"
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        attributes = []
        if self._child_info is None:
            return {}
        if self._key in self.coordinator.data:
            grades = self.coordinator.data[self._key]
            for grade in grades:
                attributes.append(grade)
        result = super().extra_state_attributes
        result.update({"notes": attributes})
        return result


class EDDisciplineSensor(EDGenericSensor):
    """Representation of a ED sensor."""

    def __init__(
        self, coordinator: EDDataUpdateCoordinator, eleve: EDEleve, nom: str, note: Any
    ) -> None:
        """Initialize the ED sensor."""
        super().__init__(
            coordinator,
            f"{eleve.get_fullname_lower()}_{get_unique_id(nom)}",
            nom,
            eleve,
            note,
        )
        self.unique_id = f"ed_{eleve.get_fullname_lower()}_{get_unique_id(nom)}"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        discipline = self.coordinator.data[self._key]
        attributes = []
        attributes.append({"code": discipline["code"]})

        result = super().extra_state_attributes
        result.update(
            {
                "Code": discipline["code"],
                "Nom": discipline["name"],
                "Moyenne classe": discipline["moyenneClasse"],
                "Moyenne minimum": discipline["moyenneMin"],
                "Moyenne maximum": discipline["moyenneMax"],
                "Appréciations": discipline["appreciations"],
            }
        )
        return result


class EDLessonsSensor(EDGenericSensor):
    """Representation of a ED sensor."""

    def __init__(
        self, coordinator: EDDataUpdateCoordinator, eleve: EDEleve, suffix: str
    ) -> None:
        """Initialize the ED sensor."""
        super().__init__(
            coordinator,
            key=f"{eleve.get_fullname_lower()}_timetable{suffix}",
            name="Emploi du temps",
            eleve=eleve,
            state="len",
        )
        self._suffix = suffix
        self._attr_name = self.name
        self.unique_id = f"ed_{eleve.get_fullname_lower()}_edt{suffix}"
        self._start_at = None
        self._end_at = None
        self._lunch_break_start_at = None
        self._lunch_break_end_at = None

    @property
    def name(self) -> str | None:
        """Return the name of the sensor."""
        name = "Emploi du temps"
        match self._suffix:
            case "_1":
                name = "Emploi du temps - Semaine en cours"
            case "_2":
                name = "Emploi du temps - Semaine suivante"
            case "_3":
                name = "Emploi du temps - Semaine après suivante"
            case "_today":
                name = "Emploi du temps - Aujourd'hui"
            case "_tomorrow":
                name = "Emploi du temps - Demain"
            case "_next_day":
                name = "Emploi du temps - Jour suivant"
        return name

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        attributes = []
        single_day = self._suffix in ["today", "tomorrow", "next_day"]
        if self._key in self.coordinator.data:
            lessons = self.coordinator.data[self._key]
            canceled_counter = None
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
                        and lesson["is_annule"]
                    ):
                        attributes.append(lesson)
                        self._date = lesson["start"].strftime("%Y-%m-%d")
                    if lesson["is_annule"]:
                        canceled_counter += 1
                    if single_day and lesson["is_annule"] is False:
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
                LOGGER.warning(
                    "[%s] Les attributs sont trop volumineux! %s",
                    self._attr_name,
                    attributes,
                )
                attributes = []
                attributes.append(
                    {
                        "Erreur": "Les attributs sont trop volumineux. Essayez de désactiver les tags HTML. https://www.hacf.fr/ecole-directe/#retrait-des-tags-html"
                    }
                )

        result = super().extra_state_attributes
        result.update(
            {
                "Emploi du temps": attributes,
                "Cours annulés": canceled_counter,
            }
        )

        if single_day:
            result["Déjeuner début"] = self._lunch_break_start_at
            result["Déjeuner fin"] = self._lunch_break_end_at
            result["Journée début"] = self._start_at
            result["Journée fin"] = self._end_at
            result["Date"] = self._date

        return result


class EDMoyenneGeneraleSensor(EDGenericSensor):
    """Representation of a ED sensor."""

    def __init__(self, coordinator: EDDataUpdateCoordinator, eleve: EDEleve) -> None:
        """Initialize the ED sensor."""
        super().__init__(
            coordinator,
            f"{eleve.get_fullname_lower()}_moyenne_generale",
            "Moyenne générale",
            eleve,
        )
        if "moyenneGenerale" in self.coordinator.data[self._key]:
            self._state = self.coordinator.data[self._key]["moyenneGenerale"]
        else:
            self._state = "N/A"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        moyenne = self.coordinator.data[self._key]
        result = super().extra_state_attributes

        if moyenne is None or moyenne == {}:
            return result

        result.update(
            {
                "Moyenne classe": moyenne["moyenneClasse"],
                "Moyenne minimum": moyenne["moyenneMin"],
                "Moyenne maximum": moyenne["moyenneMax"],
                "Date de calcul": moyenne["dateCalcul"],
            }
        )

        return result


class EDEvaluationsSensor(EDGenericSensor):
    """Representation of a ED sensor."""

    def __init__(self, coordinator: EDDataUpdateCoordinator, eleve: EDEleve) -> None:
        """Initialize the ED sensor."""
        super().__init__(
            coordinator,
            f"{eleve.get_fullname_lower()}_evaluations",
            "Evaluations",
            eleve,
            "len",
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        attributes = []
        if self._key in self.coordinator.data:
            evaluations = self.coordinator.data[self._key]
            for evaluation in evaluations:
                attributes.append(evaluation)

        result = super().extra_state_attributes
        result.update(
            {
                "Evaluations": attributes,
            }
        )
        return result


class EDAbsencesSensor(EDGenericSensor):
    """Representation of a ED sensor."""

    def __init__(self, coordinator: EDDataUpdateCoordinator, eleve: EDEleve) -> None:
        """Initialize the ED sensor."""
        super().__init__(
            coordinator,
            f"{eleve.get_fullname_lower()}_absences",
            "Absences",
            eleve,
            "len",
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        attributes = []
        if self._key in self.coordinator.data:
            absences = self.coordinator.data[self._key]
            for absence in absences:
                attributes.append(absence)
        result = super().extra_state_attributes
        result.update(
            {
                "Absences": attributes,
            }
        )
        return result


class EDRetardsSensor(EDGenericSensor):
    """Representation of a ED sensor."""

    def __init__(self, coordinator: EDDataUpdateCoordinator, eleve: EDEleve) -> None:
        """Initialize the ED sensor."""
        super().__init__(
            coordinator,
            f"{eleve.get_fullname_lower()}_retards",
            "Retards",
            eleve,
            "len",
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        attributes = []
        if self._key in self.coordinator.data:
            retards = self.coordinator.data[self._key]
            for retard in retards:
                attributes.append(retard)
        result = super().extra_state_attributes
        result.update(
            {
                "Retards": attributes,
            }
        )
        return result


class EDSanctionsSensor(EDGenericSensor):
    """Representation of a ED sensor."""

    def __init__(self, coordinator: EDDataUpdateCoordinator, eleve: EDEleve) -> None:
        """Initialize the ED sensor."""
        super().__init__(
            coordinator,
            f"{eleve.get_fullname_lower()}_sanctions",
            "Sanctions",
            eleve,
            "len",
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        attributes = []
        if self._key in self.coordinator.data:
            sanctions = self.coordinator.data[self._key]
            for sanction in sanctions:
                attributes.append(sanction)

        result = super().extra_state_attributes
        result.update(
            {
                "Sanctions": attributes,
            }
        )
        return result


class EDEncouragementsSensor(EDGenericSensor):
    """Representation of a ED sensor."""

    def __init__(self, coordinator: EDDataUpdateCoordinator, eleve: EDEleve) -> None:
        """Initialize the ED sensor."""
        super().__init__(
            coordinator,
            f"{eleve.get_fullname_lower()}_encouragements",
            "Encouragements",
            eleve,
            "len",
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        attributes = []
        if self._key in self.coordinator.data:
            encouragements = self.coordinator.data[self._key]
            for encouragement in encouragements:
                attributes.append(encouragement)
        result = super().extra_state_attributes
        result.update(
            {
                "Encouragements": attributes,
            }
        )
        return result


class EDFormulairesSensor(EDGenericSensor):
    """Representation of a ED sensor."""

    def __init__(self, coordinator: EDDataUpdateCoordinator) -> None:
        """Initialize the ED sensor."""
        super().__init__(coordinator, "formulaires", "Formulaires", None, "len")

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


class EDMessagerieSensor(EDGenericSensor):
    """Representation of a ED sensor."""

    def __init__(
        self, coordinator: EDDataUpdateCoordinator, eleve: EDEleve | None
    ) -> None:
        """Initialize the ED sensor."""
        super().__init__(
            coordinator,
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


def is_too_big(obj: Any) -> bool:
    """Calculate is_too_big."""
    bytes_result = json_bytes(obj)
    return len(bytes_result) > MAX_STATE_ATTRS_BYTES
