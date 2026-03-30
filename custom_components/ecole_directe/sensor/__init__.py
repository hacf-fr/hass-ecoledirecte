"""Sensor platform for ecole_directe."""

from __future__ import annotations

from typing import TYPE_CHECKING

from custom_components.ecole_directe.const import (
    DOMAIN,
    FAKE_ON,
    LOGGER,
)

from .absences import ENTITY_DESCRIPTIONS as ABSENCES_DESCRIPTIONS
from .absences import EDAbsencesSensor
from .child import ENTITY_DESCRIPTIONS as CHILD_DESCRIPTIONS
from .child import EDChildSensor
from .discipline import ENTITY_DESCRIPTIONS as DISCIPLINE_DESCRIPTIONS
from .discipline import EDDisciplineSensor
from .encouragements import ENTITY_DESCRIPTIONS as ENCOURAGEMENTS_DESCRIPTIONS
from .encouragements import EDEncouragementsSensor
from .evaluations import ENTITY_DESCRIPTIONS as EVALUATIONS_DESCRIPTIONS
from .evaluations import EDEvaluationsSensor
from .formulaires import ENTITY_DESCRIPTIONS as FORMULAIRES_DESCRIPTIONS
from .formulaires import EDFormulairesSensor
from .grades import ENTITY_DESCRIPTIONS as GRADES_DESCRIPTIONS
from .grades import EDGradesSensor
from .homeworks import ENTITY_DESCRIPTIONS as HOMEWORKS_DESCRIPTIONS
from .homeworks import EDHomeworksSensor
from .lessons import ENTITY_DESCRIPTIONS as LESSONS_DESCRIPTIONS
from .lessons import EDLessonsSensor
from .messagerie import ENTITY_DESCRIPTIONS as MESSAGERIE_DESCRIPTIONS
from .messagerie import EDMessagerieSensor
from .moyenne_generale import ENTITY_DESCRIPTIONS as MOYENNEGENERALE_DESCRIPTIONS
from .moyenne_generale import EDMoyenneGeneraleSensor
from .retards import ENTITY_DESCRIPTIONS as RETARDS_DESCRIPTIONS
from .retards import EDRetardsSensor
from .sanctions import ENTITY_DESCRIPTIONS as SANCTIONS_DESCRIPTIONS
from .sanctions import EDSanctionsSensor
from .wallet import ENTITY_DESCRIPTIONS as WALLETS_DESCRIPTIONS
from .wallet import EDWalletSensor

if TYPE_CHECKING:
    from homeassistant.components.sensor import SensorEntityDescription
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from custom_components.ecole_directe.coordinator.base import EDDataUpdateCoordinator
    from custom_components.ecole_directe.data import EDConfigEntry

# Combine all entity descriptions from different modules
ENTITY_DESCRIPTIONS: tuple[SensorEntityDescription, ...] = (
    *ABSENCES_DESCRIPTIONS,
    *CHILD_DESCRIPTIONS,
    *DISCIPLINE_DESCRIPTIONS,
    *ENCOURAGEMENTS_DESCRIPTIONS,
    *EVALUATIONS_DESCRIPTIONS,
    *FORMULAIRES_DESCRIPTIONS,
    *GRADES_DESCRIPTIONS,
    *HOMEWORKS_DESCRIPTIONS,
    *LESSONS_DESCRIPTIONS,
    *MESSAGERIE_DESCRIPTIONS,
    *MOYENNEGENERALE_DESCRIPTIONS,
    *RETARDS_DESCRIPTIONS,
    *SANCTIONS_DESCRIPTIONS,
    *WALLETS_DESCRIPTIONS,
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: EDConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    coordinator: EDDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id][
        "coordinator"
    ]

    if (
        coordinator.data is not None
        and "session" in coordinator.data
        and coordinator.data["session"].eleves is not None
    ):
        try:
            if "EDFORMS" in coordinator.data["session"].modules:
                async_add_entities(
                    EDFormulairesSensor(
                        coordinator=config_entry.runtime_data.coordinator,
                        entity_description=entity_description,
                    )
                    for entity_description in FORMULAIRES_DESCRIPTIONS
                )
            if "MESSAGERIE" in coordinator.data["session"].modules:
                async_add_entities(
                    EDMessagerieSensor(
                        coordinator=config_entry.runtime_data.coordinator,
                        entity_description=entity_description,
                        eleve=None,
                    )
                    for entity_description in MESSAGERIE_DESCRIPTIONS
                )
            # We add the sensor regardless of modules, as it's often not listed.
            if "wallets" in coordinator.data:
                wallets = coordinator.data["wallets"]
                for wallet in wallets:
                    async_add_entities(
                        EDWalletSensor(
                            coordinator=config_entry.runtime_data.coordinator,
                            entity_description=entity_description,
                            libelle=wallet["libelle"],
                            eleve=None,
                            solde=wallet["solde"],
                        )
                        for entity_description in WALLETS_DESCRIPTIONS
                    )
        except Exception:
            LOGGER.exception("Error while creating generic sensors")

        for eleve in coordinator.data["session"].eleves:
            async_add_entities(
                EDChildSensor(
                    coordinator=config_entry.runtime_data.coordinator,
                    eleve=eleve,
                    entity_description=entity_description,
                )
                for entity_description in CHILD_DESCRIPTIONS
            )
            # START: ADDED FOR WALLET SENSOR
            try:
                # We add the sensor regardless of modules, as it's often not listed.
                if f"{eleve.get_fullname_lower()}_wallets" in coordinator.data:
                    wallets = coordinator.data[f"{eleve.get_fullname_lower()}_wallets"]
                    for wallet in wallets:
                        async_add_entities(
                            EDWalletSensor(
                                coordinator=config_entry.runtime_data.coordinator,
                                entity_description=entity_description,
                                libelle=wallet["libelle"],
                                eleve=eleve,
                                solde=wallet["solde"],
                            )
                            for entity_description in WALLETS_DESCRIPTIONS
                        )
            except Exception:
                LOGGER.exception("Error while creating wallet sensors")
            # END: ADDED FOR WALLET SENSOR
            if FAKE_ON or "CAHIER_DE_TEXTES" in eleve.modules:
                try:
                    async_add_entities(
                        EDHomeworksSensor(
                            coordinator=coordinator,
                            entity_description=entity_description,
                            eleve=eleve,
                            homework_id="_1",
                        )
                        for entity_description in HOMEWORKS_DESCRIPTIONS
                    )
                    async_add_entities(
                        EDHomeworksSensor(
                            coordinator=coordinator,
                            entity_description=entity_description,
                            eleve=eleve,
                            homework_id="_2",
                        )
                        for entity_description in HOMEWORKS_DESCRIPTIONS
                    )
                    async_add_entities(
                        EDHomeworksSensor(
                            coordinator=coordinator,
                            entity_description=entity_description,
                            eleve=eleve,
                            homework_id="_3",
                        )
                        for entity_description in HOMEWORKS_DESCRIPTIONS
                    )
                    async_add_entities(
                        EDHomeworksSensor(
                            coordinator=coordinator,
                            entity_description=entity_description,
                            eleve=eleve,
                            homework_id="_today",
                        )
                        for entity_description in HOMEWORKS_DESCRIPTIONS
                    )
                    async_add_entities(
                        EDHomeworksSensor(
                            coordinator=coordinator,
                            entity_description=entity_description,
                            eleve=eleve,
                            homework_id="_tomorrow",
                        )
                        for entity_description in HOMEWORKS_DESCRIPTIONS
                    )
                    async_add_entities(
                        EDHomeworksSensor(
                            coordinator=coordinator,
                            entity_description=entity_description,
                            eleve=eleve,
                            homework_id="_next_day",
                        )
                        for entity_description in HOMEWORKS_DESCRIPTIONS
                    )
                    async_add_entities(
                        EDHomeworksSensor(
                            coordinator=coordinator,
                            entity_description=entity_description,
                            eleve=eleve,
                            homework_id="",
                        )
                        for entity_description in HOMEWORKS_DESCRIPTIONS
                    )
                except Exception:
                    LOGGER.exception("Error while creating homeworks sensors")
            if FAKE_ON or "EDT" in eleve.modules:
                try:
                    async_add_entities(
                        EDLessonsSensor(
                            coordinator=coordinator,
                            entity_description=entity_description,
                            eleve=eleve,
                            lesson_id="_1",
                        )
                        for entity_description in LESSONS_DESCRIPTIONS
                    )
                    async_add_entities(
                        EDLessonsSensor(
                            coordinator=coordinator,
                            entity_description=entity_description,
                            eleve=eleve,
                            lesson_id="_2",
                        )
                        for entity_description in LESSONS_DESCRIPTIONS
                    )
                    async_add_entities(
                        EDLessonsSensor(
                            coordinator=coordinator,
                            entity_description=entity_description,
                            eleve=eleve,
                            lesson_id="_3",
                        )
                        for entity_description in LESSONS_DESCRIPTIONS
                    )
                    async_add_entities(
                        EDLessonsSensor(
                            coordinator=coordinator,
                            entity_description=entity_description,
                            eleve=eleve,
                            lesson_id="_today",
                        )
                        for entity_description in LESSONS_DESCRIPTIONS
                    )
                    async_add_entities(
                        EDLessonsSensor(
                            coordinator=coordinator,
                            entity_description=entity_description,
                            eleve=eleve,
                            lesson_id="_tomorrow",
                        )
                        for entity_description in LESSONS_DESCRIPTIONS
                    )
                    async_add_entities(
                        EDLessonsSensor(
                            coordinator=coordinator,
                            entity_description=entity_description,
                            eleve=eleve,
                            lesson_id="_next_day",
                        )
                        for entity_description in LESSONS_DESCRIPTIONS
                    )
                except Exception:
                    LOGGER.exception("Error while creating lessons sensors")
            if FAKE_ON or "NOTES" in eleve.modules:
                try:
                    async_add_entities(
                        EDGradesSensor(
                            coordinator=coordinator,
                            entity_description=entity_description,
                            eleve=eleve,
                        )
                        for entity_description in GRADES_DESCRIPTIONS
                    )
                    async_add_entities(
                        EDEvaluationsSensor(
                            coordinator=coordinator,
                            entity_description=entity_description,
                            eleve=eleve,
                        )
                        for entity_description in EVALUATIONS_DESCRIPTIONS
                    )
                except Exception:
                    LOGGER.exception("Error while creating grades sensors")
                try:
                    if f"{eleve.get_fullname_lower()}_disciplines" in coordinator.data:
                        disciplines = coordinator.data[
                            f"{eleve.get_fullname_lower()}_disciplines"
                        ]
                        for discipline in disciplines:
                            async_add_entities(
                                EDDisciplineSensor(
                                    coordinator=coordinator,
                                    entity_description=entity_description,
                                    eleve=eleve,
                                    nom=discipline["nom"],
                                    moyenne=discipline["moyenne"],
                                )
                                for entity_description in DISCIPLINE_DESCRIPTIONS
                            )
                    if (
                        f"{eleve.get_fullname_lower()}_moyenne_generale"
                        in coordinator.data
                    ):
                        async_add_entities(
                            EDMoyenneGeneraleSensor(
                                coordinator=coordinator,
                                entity_description=entity_description,
                                eleve=eleve,
                            )
                            for entity_description in MOYENNEGENERALE_DESCRIPTIONS
                        )
                except Exception:
                    LOGGER.exception("Error while creating moyennes sensors")

            if FAKE_ON or "VIE_SCOLAIRE" in eleve.modules:
                try:
                    async_add_entities(
                        EDAbsencesSensor(
                            coordinator=coordinator,
                            entity_description=entity_description,
                            eleve=eleve,
                        )
                        for entity_description in ABSENCES_DESCRIPTIONS
                    )
                    async_add_entities(
                        EDRetardsSensor(
                            coordinator=coordinator,
                            entity_description=entity_description,
                            eleve=eleve,
                        )
                        for entity_description in RETARDS_DESCRIPTIONS
                    )
                    async_add_entities(
                        EDEncouragementsSensor(
                            coordinator=coordinator,
                            entity_description=entity_description,
                            eleve=eleve,
                        )
                        for entity_description in ENCOURAGEMENTS_DESCRIPTIONS
                    )
                    async_add_entities(
                        EDSanctionsSensor(
                            coordinator=coordinator,
                            entity_description=entity_description,
                            eleve=eleve,
                        )
                        for entity_description in SANCTIONS_DESCRIPTIONS
                    )
                except Exception:
                    LOGGER.exception("Error while creating VIE_SCOLAIRE sensors")
            if FAKE_ON or "MESSAGERIE" in eleve.modules:
                try:
                    async_add_entities(
                        EDMessagerieSensor(
                            coordinator=coordinator,
                            entity_description=entity_description,
                            eleve=eleve,
                        )
                        for entity_description in MESSAGERIE_DESCRIPTIONS
                    )
                except Exception:
                    LOGGER.exception("Error while creating student messagerie sensors")
