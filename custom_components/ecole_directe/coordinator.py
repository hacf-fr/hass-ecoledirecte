"""Data update coordinator for the Ecole Directe integration."""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta, tzinfo
from typing import TYPE_CHECKING, Any

from ecoledirecte_api.client import QCMException
from homeassistant.helpers.update_coordinator import TimestampDataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .const import (
    AUGUST,
    DEFAULT_LUNCH_BREAK_TIME,
    DEFAULT_REFRESH_INTERVAL,
    EVENT_TYPE,
    FAKE_ON,
    GRADES_TO_DISPLAY,
)
from .ecole_directe_helper import EDEleve, EDSession, get_unique_id

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

LOGGER = logging.getLogger(__name__)


class EDDataUpdateCoordinator(TimestampDataUpdateCoordinator):
    """Data update coordinator for the Ecole Directe integration."""

    config_entry: ConfigEntry
    timezone: tzinfo

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass=hass,
            logger=LOGGER,
            name=entry.title,
            config_entry=entry,
            update_interval=timedelta(
                minutes=entry.options.get("refresh_interval", DEFAULT_REFRESH_INTERVAL)
            ),
        )
        self.timezone = dt_util.get_default_time_zone()
        LOGGER.debug("timezone: %s", self.timezone)

    async def _async_update_data(self) -> dict[str, Any] | None:
        """Get the latest data from Ecole Directe and updates the state."""
        if FAKE_ON:
            LOGGER.info("DEBUG MODE ON")

        previous_data = None if self.data is None else self.data.copy()

        async with EDSession(
            self.config_entry.data["username"],
            self.config_entry.data["password"],
            self.hass.config.config_dir + "/" + self.config_entry.data["qcm_filename"],
            self.hass,
        ) as session:
            try:
                await session.login()
            except QCMException:
                LOGGER.exception("Unable to init ecole directe client")
                return None
            except Exception:
                LOGGER.critical("Unknow error on login")
                return None

            self.data = {}
            self.data["session"] = session

            current_year = datetime.now(self.timezone).year
            if datetime.now(self.timezone).month >= AUGUST:
                year_data = f"{current_year!s}-{(current_year + 1)!s}"
            else:
                year_data = f"{(current_year - 1)!s}-{current_year!s}"

            # EDT BODY
            today = datetime.now(self.timezone).date()
            tomorrow = datetime.now(self.timezone).date() + timedelta(days=1)

            current_week_begin = datetime.now(self.timezone).date() - timedelta(
                days=datetime.now(self.timezone).weekday()
            )

            current_week_plus_21 = current_week_begin + timedelta(days=21)
            current_week_end = current_week_begin + timedelta(days=6)
            next_week_begin = current_week_end + timedelta(days=1)
            next_week_end = next_week_begin + timedelta(days=6)
            after_next_week_begin = next_week_end + timedelta(days=1)

            if session.account_type == "P":  # professor ???
                try:
                    for classe in session.data["accounts"][0]["profile"]["classes"]:
                        await session.get_classe(
                            classe["id"],
                        )
                except Exception as ex:
                    LOGGER.warning("Error getting classes: %s", ex)

            if session.account_type == "1":  # famille
                if "MESSAGERIE" in session.modules:
                    try:
                        self.data["messagerie"] = await session.get_messages(
                            session.id,
                            None,
                            year_data,
                        )

                    except Exception as ex:
                        LOGGER.warning(
                            "Error getting messages for family from ecole directe: %s",
                            ex,
                        )

                if FAKE_ON or "EDFORMS" in session.modules:
                    try:
                        self.data["formulaires"] = await session.get_formulaires(
                            session.account_type,
                            session.id,
                        )
                        self.compare_data(
                            previous_data,
                            "formulaires",
                            ["created", "titre"],
                            "new_formulaires",
                            None,
                        )
                    except Exception as ex:
                        LOGGER.warning(
                            "Error getting formulaires from ecole directe: %s", ex
                        )

            # START: MODIFIED FOR WALLET BALANCE (SINGLE CALL)
            all_balances = None
            try:
                all_balances = await session.get_all_wallet_balances()
                if all_balances and f"{session.id}" in all_balances:
                    self.data["wallets"] = all_balances[f"{session.id}"]
            except Exception as ex:
                LOGGER.warning(
                    "Error getting all wallet balances from ecole directe: %s", ex
                )
            # END: MODIFIED FOR WALLET BALANCE (SINGLE CALL)

            for eleve in session.eleves:
                # START: DISTRIBUTE WALLET BALANCE DATA
                if all_balances and eleve.eleve_id in all_balances:
                    wallets_key = f"{eleve.get_fullname_lower()}_wallets"
                    self.data[wallets_key] = all_balances[eleve.eleve_id]
                # END: DISTRIBUTE WALLET BALANCE DATA

                if FAKE_ON or "CAHIER_DE_TEXTES" in eleve.modules:
                    try:
                        homeworks = await session.get_homeworks(
                            eleve,
                            self.config_entry.options.get("decode_html", False),
                        )

                        self.data[f"{eleve.get_fullname_lower()}_homeworks"] = homeworks

                        self.compare_data(
                            previous_data,
                            f"{eleve.get_fullname_lower()}_homeworks",
                            ["date", "matiere", "short_description"],
                            "new_homework",
                            eleve,
                        )

                        self.data[f"{eleve.get_fullname_lower()}_homeworks_today"] = (
                            list(
                                filter(
                                    lambda homework: homework["date"]
                                    .astimezone(self.timezone)
                                    .date()
                                    == today,
                                    homeworks,
                                )
                            )
                        )
                        homeworks_tomorrow = list(
                            filter(
                                lambda homework: homework["date"]
                                .astimezone(self.timezone)
                                .date()
                                == tomorrow,
                                homeworks,
                            )
                        )
                        self.data[
                            f"{eleve.get_fullname_lower()}_homeworks_tomorrow"
                        ] = homeworks_tomorrow
                        self.data[
                            f"{eleve.get_fullname_lower()}_homeworks_next_day"
                        ] = get_next_day_list(
                            homeworks,
                            homeworks_tomorrow,
                            tomorrow,
                            "date",
                        )

                        self.data[f"{eleve.get_fullname_lower()}_homeworks_1"] = list(
                            filter(
                                lambda homework: homework["date"]
                                .astimezone(self.timezone)
                                .date()
                                >= current_week_begin
                                and homework["date"].astimezone(self.timezone).date()
                                <= current_week_end,
                                homeworks,
                            )
                        )
                        self.data[f"{eleve.get_fullname_lower()}_homeworks_2"] = list(
                            filter(
                                lambda homework: homework["date"]
                                .astimezone(self.timezone)
                                .date()
                                >= next_week_begin
                                and homework["date"].astimezone(self.timezone).date()
                                <= next_week_end,
                                homeworks,
                            )
                        )
                        self.data[f"{eleve.get_fullname_lower()}_homeworks_3"] = list(
                            filter(
                                lambda homework: homework["date"]
                                .astimezone(self.timezone)
                                .date()
                                >= after_next_week_begin,
                                homeworks,
                            )
                        )

                    except Exception as ex:
                        LOGGER.warning(
                            "Error getting homeworks from ecole directe: %s", ex
                        )
                if FAKE_ON or "NOTES" in eleve.modules:
                    try:
                        grades_evaluations = await session.get_grades_evaluations(
                            eleve,
                            year_data,
                            self.config_entry.options.get(
                                "notes_affichees", GRADES_TO_DISPLAY
                            ),
                        )
                        if "disciplines" in grades_evaluations:
                            disciplines = grades_evaluations["disciplines"]
                            self.data[f"{eleve.get_fullname_lower()}_disciplines"] = (
                                disciplines
                            )
                            for discipline in disciplines:
                                self.data[
                                    f"{eleve.get_fullname_lower()}_{get_unique_id(discipline['name'])}"
                                ] = discipline

                        if "moyenne_generale" in grades_evaluations:
                            self.data[
                                f"{eleve.get_fullname_lower()}_moyenne_generale"
                            ] = grades_evaluations["moyenne_generale"]

                        self.data[f"{eleve.get_fullname_lower()}_notes"] = (
                            grades_evaluations["notes"]
                        )
                        self.compare_data(
                            previous_data,
                            f"{eleve.get_fullname_lower()}_notes",
                            ["date", "matiere", "commentaire"],
                            "new_grade",
                            eleve,
                        )

                        self.data[f"{eleve.get_fullname_lower()}_evaluations"] = (
                            grades_evaluations["evaluations"]
                        )
                        self.compare_data(
                            previous_data,
                            f"{eleve.get_fullname_lower()}_evaluations",
                            ["date", "matiere", "devoir"],
                            "new_evaluations",
                            eleve,
                        )
                    except Exception as ex:
                        LOGGER.warning(
                            "Error getting grades from ecole directe: %s", ex
                        )

                if FAKE_ON or "EDT" in eleve.modules:
                    try:
                        break_time = self.config_entry.options.get(
                            "lunch_break_time", DEFAULT_LUNCH_BREAK_TIME
                        )
                        lunch_break_time = datetime.strptime(
                            break_time,
                            "%H:%M",
                        ).time()

                        lessons = await session.get_lessons(
                            eleve,
                            today.strftime("%Y-%m-%d"),
                            current_week_plus_21.strftime("%Y-%m-%d"),
                            lunch_break_time,
                        )
                        self.data[f"{eleve.get_fullname_lower()}_timetable_today"] = (
                            list(
                                filter(
                                    lambda lesson: lesson["start"]
                                    .astimezone(self.timezone)
                                    .date()
                                    == today,
                                    lessons,
                                )
                            )
                        )
                        lessons_tomorrow = list(
                            filter(
                                lambda lesson: lesson["start"]
                                .astimezone(self.timezone)
                                .date()
                                == tomorrow,
                                lessons,
                            )
                        )
                        self.data[
                            f"{eleve.get_fullname_lower()}_timetable_tomorrow"
                        ] = lessons_tomorrow
                        self.data[
                            f"{eleve.get_fullname_lower()}_timetable_next_day"
                        ] = get_next_day_list(
                            lessons,
                            lessons_tomorrow,
                            tomorrow,
                            "start",
                        )
                        self.data[f"{eleve.get_fullname_lower()}_timetable_1"] = list(
                            filter(
                                lambda lesson: lesson["start"]
                                .astimezone(self.timezone)
                                .date()
                                >= today
                                and lesson["start"].astimezone(self.timezone).date()
                                <= current_week_end,
                                lessons,
                            )
                        )
                        self.data[f"{eleve.get_fullname_lower()}_timetable_2"] = list(
                            filter(
                                lambda lesson: lesson["start"]
                                .astimezone(self.timezone)
                                .date()
                                >= next_week_begin
                                and lesson["start"].astimezone(self.timezone).date()
                                <= next_week_end,
                                lessons,
                            )
                        )
                        self.data[f"{eleve.get_fullname_lower()}_timetable_3"] = list(
                            filter(
                                lambda lesson: lesson["start"]
                                .astimezone(self.timezone)
                                .date()
                                >= after_next_week_begin,
                                lessons,
                            )
                        )

                    except Exception as ex:
                        LOGGER.warning(
                            "Error getting Lessons from ecole directe: %s", ex
                        )

                if FAKE_ON or "VIE_SCOLAIRE" in eleve.modules:
                    try:
                        vie_scolaire = await session.get_vie_scolaire(eleve)
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
                            )
                        if "sanctions" in vie_scolaire:
                            self.data[f"{eleve.get_fullname_lower()}_sanctions"] = (
                                vie_scolaire["sanctions"]
                            )
                            self.compare_data(
                                previous_data,
                                f"{eleve.get_fullname_lower()}_sanctions",
                                ["date", "type_element", "display_date"],
                                "new_sanction",
                                eleve,
                            )
                        if "encouragements" in vie_scolaire:
                            self.data[
                                f"{eleve.get_fullname_lower()}_encouragements"
                            ] = vie_scolaire["encouragements"]
                            self.compare_data(
                                previous_data,
                                f"{eleve.get_fullname_lower()}_encouragements",
                                ["date", "type_element", "display_date"],
                                "new_encouragement",
                                eleve,
                            )
                    except Exception as ex:
                        LOGGER.warning(
                            "Error getting vie scolaire from ecole directe: %s", ex
                        )
                if FAKE_ON or "MESSAGERIE" in eleve.modules:
                    try:
                        self.data[
                            f"{eleve.get_fullname_lower()}_messagerie"
                        ] = await session.get_messages(
                            session.id,
                            eleve,
                            year_data,
                        )
                    except Exception as ex:
                        LOGGER.warning(
                            "Error getting messages from ecole directe: %s", ex
                        )

            return self.data

    def compare_data(
        self,
        previous_data: dict | None,
        data_key: str,
        compare_keys: list[str],
        event_type: str,
        eleve: EDEleve | None,
    ) -> None:
        """Compare data from previous session."""
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
                        if {key: previous_item[key] for key in compare_keys} == {
                            key: item[key] for key in compare_keys
                        }:
                            found = True
                            break
                    if found is False:
                        not_found_items.append(item)
                for not_found_item in not_found_items:
                    self.trigger_event(event_type, eleve, not_found_item)
        except Exception as ex:
            LOGGER.warning(
                "Error comparing data: self[%s] previous_data[%s] data_key[%s] ex[%s]",
                self,
                previous_data,
                data_key,
                ex,
            )

    def trigger_event(self, event_type: str, eleve: EDEleve | None, data: Any) -> None:
        """Trigger an event if there is new data."""
        name = "" if eleve is None else eleve.get_fullname()

        event_data = {
            "child_name": name,
            "type": event_type,
            "data": data,
        }
        self.hass.bus.fire(EVENT_TYPE, event_data)


def get_next_day_list(
    my_list: list, list_next_day: list, next_day: date, field: str = "start"
) -> list | None:
    """Get next day lessons."""
    if len(my_list) == 0:
        return None
    if my_list[-1][field].date() < next_day:
        return None
    if len(list_next_day) == 0:
        next_day = next_day + timedelta(days=1)
        list_next_day = list(
            filter(
                lambda lesson: lesson[field].date() == next_day,
                my_list,
            )
        )
        return get_next_day_list(my_list, list_next_day, next_day, field)
    return list_next_day
