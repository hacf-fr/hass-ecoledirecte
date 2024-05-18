"""Data update coordinator for the Ecole Directe integration."""

from __future__ import annotations

import datetime
import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import TimestampDataUpdateCoordinator

from .ecole_directe_formatter import (
    format_evaluation,
    format_grade,
    format_vie_scolaire,
)

from .ecole_directe_helper import (
    EDEleve,
    get_ecoledirecte_session,
    get_homeworks,
    get_lessons,
    get_grades_evaluations,
    get_vie_scolaire,
)

from .const import (
    DEFAULT_REFRESH_INTERVAL,
    EVENT_TYPE,
)

_LOGGER = logging.getLogger(__name__)


class EDDataUpdateCoordinator(TimestampDataUpdateCoordinator):
    """Data update coordinator for the Ecole Directe integration."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass=hass,
            logger=_LOGGER,
            name=entry.title,
            update_interval=timedelta(
                minutes=entry.options.get("refresh_interval", DEFAULT_REFRESH_INTERVAL)
            ),
        )
        self.config_entry = entry

    async def _async_update_data(self) -> dict[Platform, dict[str, Any]]:
        """Get the latest data from Ecole Directe and updates the state."""

        previous_data = None if self.data is None else self.data.copy()

        data = self.config_entry.data

        session = await self.hass.async_add_executor_job(
            get_ecoledirecte_session, data, self.hass.config.config_dir, self.hass
        )

        if session is None:
            _LOGGER.error("Unable to init ecole directe client")
            return None

        self.data = {}
        self.data["session"] = session

        current_year = datetime.datetime.now().year
        if (current_year % 2) == 0:
            year_data = f"{str(current_year-1)}-{str(current_year)}"
        else:
            year_data = f"{str(current_year)}-{str(current_year + 1)}"

        # EDT BODY
        today = datetime.datetime.today().strftime("%Y-%m-%d")
        tomorrow = (datetime.datetime.today() + timedelta(days=1)).strftime("%Y-%m-%d")
        today_plus_15 = (datetime.datetime.today() + timedelta(days=15)).strftime(
            "%Y-%m-%d"
        )

        # if session._account_type == "1":  # famille
        #     if "MESSAGERIE" in session.modules:
        #         try:
        #             self.data["messages"] = await self.hass.async_add_executor_job(
        #                 get_messages, session, None, year_data
        #             )
        #         except Exception as ex:
        #             _LOGGER.warning(
        #                 "Error getting messages for family from ecole directe: %s", ex
        #             )

        for eleve in session.eleves:
            if "CAHIER_DE_TEXTES" in eleve.modules:
                try:
                    self.data[
                        f"{eleve.get_fullname_lower()}_homework"
                    ] = await self.hass.async_add_executor_job(
                        get_homeworks, session.token, eleve, self.hass.config.config_dir
                    )
                except Exception as ex:
                    _LOGGER.warning(
                        "Error getting homeworks from ecole directe: %s", ex
                    )
            if "NOTES" in eleve.modules:
                try:
                    grades_evaluations = await self.hass.async_add_executor_job(
                        get_grades_evaluations,
                        session.token,
                        eleve,
                        year_data,
                        self.hass.config.config_dir,
                    )

                    self.data[f"{eleve.get_fullname_lower()}_grades"] = (
                        grades_evaluations["grades"]
                    )
                    self.compare_data(
                        previous_data,
                        f"{eleve.get_fullname_lower()}_grades",
                        ["date", "libelle_matiere", "devoir"],
                        "new_grade",
                        eleve,
                        format_grade,
                    )

                    self.data[f"{eleve.get_fullname_lower()}_evaluations"] = (
                        grades_evaluations["evaluations"]
                    )
                    self.compare_data(
                        previous_data,
                        f"{eleve.get_fullname_lower()}_evaluations",
                        ["date", "libelle_matiere", "devoir"],
                        "new_evaluations",
                        eleve,
                        format_evaluation,
                    )
                except Exception as ex:
                    _LOGGER.warning("Error getting grades from ecole directe: %s", ex)

            if "EDT" in eleve.modules:
                try:
                    lessons = await self.hass.async_add_executor_job(
                        get_lessons,
                        session.token,
                        eleve,
                        today,
                        today_plus_15,
                        self.hass.config.config_dir,
                    )
                    lessons_today = list(
                        filter(
                            lambda lesson: lesson.start_date.strftime("%Y-%m-%d")
                            == today,
                            lessons,
                        )
                    )
                    self.data[f"{eleve.get_fullname_lower()}_timetable_today"] = (
                        lessons_today
                    )
                    lessons_tomorrow = list(
                        filter(
                            lambda lesson: lesson.start_date.strftime("%Y-%m-%d")
                            == tomorrow,
                            lessons,
                        )
                    )
                    self.data[f"{eleve.get_fullname_lower()}_timetable_tomorrow"] = (
                        lessons_tomorrow
                    )
                    lessons_next_day = get_next_day_lessons(
                        lessons,
                        lessons_tomorrow,
                        datetime.datetime.strptime(tomorrow, "%Y-%m-%d"),
                    )
                    self.data[f"{eleve.get_fullname_lower()}_timetable_next_day"] = (
                        lessons_next_day
                    )
                    self.data[f"{eleve.get_fullname_lower()}_timetable_period"] = (
                        lessons
                    )

                except Exception as ex:
                    _LOGGER.warning("Error getting Lessons from ecole directe: %s", ex)

            if "VIE_SCOLAIRE" in eleve.modules:
                try:
                    vie_scolaire = await self.hass.async_add_executor_job(
                        get_vie_scolaire,
                        session.token,
                        eleve,
                        self.hass.config.config_dir,
                    )
                    if "absences" in vie_scolaire:
                        self.data[f"{eleve.get_fullname_lower()}_absences"] = (
                            vie_scolaire["absences"]
                        )

                        self.compare_data(
                            previous_data,
                            f"{eleve.get_fullname_lower()}_absences",
                            ["date", "type_element", "display_date"],
                            "new_absence",
                            eleve,
                            format_vie_scolaire,
                        )
                    if "retards" in vie_scolaire:
                        self.data[f"{eleve.get_fullname_lower()}_retards"] = (
                            vie_scolaire["retards"]
                        )
                        self.compare_data(
                            previous_data,
                            f"{eleve.get_fullname_lower()}_retards",
                            ["date", "type_element", "display_date"],
                            "new_retard",
                            eleve,
                            format_vie_scolaire,
                        )
                    if "sanctions" in vie_scolaire:
                        self.data[f"{eleve.get_fullname_lower()}_sanctions"] = (
                            vie_scolaire["sanctions"]
                        )
                        self.compare_data(
                            previous_data,
                            f"{eleve.get_fullname_lower()}_sanctions",
                            ["date", "type_element", "display_date"],
                            "new_punishment",
                            eleve,
                            format_vie_scolaire,
                        )
                    if "encouragements" in vie_scolaire:
                        self.data[f"{eleve.get_fullname_lower()}_encouragements"] = (
                            vie_scolaire["encouragements"]
                        )
                        self.compare_data(
                            previous_data,
                            f"{eleve.get_fullname_lower()}_encouragements",
                            ["date", "type_element", "display_date"],
                            "new_encouragement",
                            eleve,
                            format_vie_scolaire,
                        )
                except Exception as ex:
                    _LOGGER.warning(
                        "Error getting vie scolaire from ecole directe: %s", ex
                    )
            # if "MESSAGERIE" in eleve.modules:
            #     try:
            #         self.data[
            #             "messages" + eleve.eleve_id
            #         ] = await self.hass.async_add_executor_job(
            #             get_messages, session, eleve, year_data
            #         )
            #     except Exception as ex:
            #         _LOGGER.warning("Error getting messages from ecole directe: %s", ex)

            # fake event new_grade
            # grade = EDGrade(
            #     data={
            #         "codeMatiere": "FRANC",
            #         "codePeriode": "A001",
            #         "codeSousMatiere": "",
            #         "coef": "1",
            #         "commentaire": "",
            #         "date": "2023-09-23",
            #         "dateSaisie": "2023-10-04",
            #         "devoir": "Rédaction : randonnée de début d'année",
            #         "enLettre": False,
            #         "id": 8388851,
            #         "libelleMatiere": "FRANCAIS",
            #         "moyenneClasse": "12.61",
            #         "nonSignificatif": False,
            #         "noteSur": "20",
            #         "typeDevoir": "ECRIT",
            #         "uncCorrige": "",
            #         "uncSujet": "",
            #         "valeur": "14,5",
            #         "valeurisee": False,
            #     }
            # )
            # self.trigger_event(
            #     "new_grade",
            #     eleve,
            #     format_grade(grade),
            # )

        return self.data

    def compare_data(
        self,
        previous_data,
        data_key,
        compare_keys,
        event_type,
        eleve: EDEleve,
        format_func,
    ):
        """Compare data from previous session"""

        try:
            if (
                previous_data is not None
                and data_key in previous_data
                and data_key in self.data
            ):
                not_found_items = []
                for item in self.data[data_key]:
                    found = False
                    for previous_item in previous_data[data_key]:
                        if {
                            key: format_func(previous_item)[key] for key in compare_keys
                        } == {key: format_func(item)[key] for key in compare_keys}:
                            found = True
                            break
                    if found is False:
                        not_found_items.append(item)
                for not_found_item in not_found_items:
                    self.trigger_event(event_type, eleve, format_func(not_found_item))
        except Exception as ex:
            _LOGGER.warning(
                "Error comparing data: self[%s] previous_data[%s] data_key[%s] ex[%s]",
                self,
                previous_data,
                data_key,
                ex,
            )

    def trigger_event(self, event_type, eleve: EDEleve, event_data):
        """Trigger an event if there is new data"""

        event_data = {
            "child_name": eleve.get_fullname(),
            "type": event_type,
            "data": event_data,
        }
        self.hass.bus.fire(EVENT_TYPE, event_data)


def get_next_day_lessons(lessons, lessons_next_day, next_day):
    """get next day lessons"""
    if len(lessons) == 0:
        return None
    if lessons[-1].start_date < next_day:
        return None
    if len(lessons_next_day) == 0:
        next_day = next_day + timedelta(days=1)
        lessons_next_day = list(
            filter(
                lambda lesson: lesson.start_date.strftime("%Y-%m-%d")
                == next_day.strftime("%Y-%m-%d"),
                lessons,
            )
        )
        return get_next_day_lessons(lessons, lessons_next_day, next_day)
    return lessons_next_day
