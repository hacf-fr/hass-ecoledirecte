"""
Core DataUpdateCoordinator implementation for ecole_directe.

This module contains the main coordinator class that manages data fetching
and updates for all entities in the integration. It handles refresh cycles,
error handling, and triggers reauthentication when needed.

For more information on coordinators:
https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
"""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta, tzinfo
from typing import TYPE_CHECKING, Any

import anyio
from ecoledirecte_api.client import QCMException
from homeassistant.core import Event, callback
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import (
    TimestampDataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.util import dt as dt_util

from custom_components.ecole_directe.api import (
    EDApiClientAuthenticationError,
    EDApiClientError,
)
from custom_components.ecole_directe.api.client import (
    EDApiClient,
)
from custom_components.ecole_directe.const import (
    AUGUST,
    DEFAULT_LUNCH_BREAK_TIME,
    DOMAIN,
    EVENT_TYPE,
    FAKE_ON,
    FILENAME_QCM,
    GRADES_TO_DISPLAY,
    LOGGER,
    MAX_QUESTIONS,
)
from custom_components.ecole_directe.helpers import get_unique_id

if TYPE_CHECKING:
    from logging import Logger

    from homeassistant.core import HomeAssistant

    from custom_components.ecole_directe.api.client import EDEleve
    from custom_components.ecole_directe.data import EDConfigEntry


class EDDataUpdateCoordinator(TimestampDataUpdateCoordinator):
    """
    Class to manage fetching data from the API.

    This coordinator handles all data fetching for the integration and distributes
    updates to all entities. It manages:
    - Periodic data updates based on update_interval
    - Error handling and recovery
    - Authentication failure detection and reauthentication triggers
    - Data distribution to all entities
    - Context-based data fetching (only fetch data for active entities)

    For more information:
    https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities

    Attributes:
        config_entry: The config entry for this integration instance.

    """

    config_entry: EDConfigEntry
    timezone: tzinfo

    def __init__(
        self,
        hass: HomeAssistant,
        entry: EDConfigEntry,
        logger: Logger,
        name: str,
        update_interval: timedelta,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass=hass,
            logger=logger,
            name=name,
            config_entry=entry,
            update_interval=update_interval,
            always_update=False,
        )
        self.timezone = dt_util.get_default_time_zone()
        LOGGER.debug("timezone: %s", self.timezone)
        # Initialize QCM data store for persistence
        self._qcm_store = Store(hass, 1, f"ecole_directe_qcm_{entry.entry_id}")

    async def _async_setup(self) -> None:
        """
        Set up the coordinator.

        This method is called automatically during async_config_entry_first_refresh()
        and is the ideal place for one-time initialization tasks such as:
        - Loading device information
        - Setting up event listeners
        - Initializing caches

        This runs before the first data fetch, ensuring any required setup
        is complete before entities start requesting data.

        Example: Fetch device info once at startup
        device_info = await self.config_entry.runtime_data.client.get_device_info()
        self._device_id = device_info["id"]
        """
        self.data = {
            "qcm_questions": {},
            "qcm_selected_options": {},
        }

        # Load saved QCM data from disk
        saved_qcm = await self._qcm_store.async_load()
        if isinstance(saved_qcm, dict):
            self.data["qcm_questions"] = saved_qcm.get("qcm_questions", {})
            self.data["qcm_selected_options"] = saved_qcm.get(
                "qcm_selected_options", {}
            )
            LOGGER.debug("Loaded saved QCM data: %s", saved_qcm)

        # Check for legacy ecoledirecte_qcm.json file, migrate and delete it
        await self.async_migrate_legacy_qcm_file()

        LOGGER.debug("Coordinator setup complete for %s", self.config_entry.entry_id)

        @callback
        def _handle_new_qcm_event(event: Event) -> None:
            if event.data.get("type") != "new_qcm":
                return

            qcm_json = event.data.get("qcm_json", {})
            self.hass.async_create_task(self._async_handle_new_qcm_event(qcm_json))

        self.config_entry.async_on_unload(
            self.hass.bus.async_listen(EVENT_TYPE, _handle_new_qcm_event)
        )

    async def _async_handle_new_qcm_event(self, qcm_json: dict[str, list[str]]) -> None:
        """Handle incoming QCM events and update stored questions."""
        LOGGER.debug("Handling new QCM event with data: %s", qcm_json)
        self._update_qcm_data(qcm_json)
        self.async_set_updated_data(self.data)

    def _update_qcm_data(self, qcm_json: dict[str, list[str]]) -> None:
        """Update coordinator data from the latest QCM challenge."""
        LOGGER.debug("Updating QCM data with new challenge: %s", qcm_json)
        questions: dict[str, list[str]] = {}
        for question, propositions in qcm_json.items():
            if not isinstance(question, str) or not isinstance(propositions, list):
                continue
            if len(propositions) < MAX_QUESTIONS:
                continue

            questions[question] = [str(option) for option in propositions]

        if questions:
            # Merge new questions with existing ones instead of replacing
            self.data["qcm_questions"].update(questions)
            # Preserve all selected options (both old and new)
            # Only remove answers for questions that no longer exist
            self.data["qcm_selected_options"] = {
                question: answer
                for question, answer in self.data.get(
                    "qcm_selected_options", {}
                ).items()
                if question in self.data["qcm_questions"]
            }
        else:
            self.data["qcm_questions"] = {}
            self.data["qcm_selected_options"] = {}

        LOGGER.debug("Updated QCM data questions: %s", self.data["qcm_questions"])
        LOGGER.debug(
            "Updated QCM data selected options: %s", self.data["qcm_selected_options"]
        )

        # Persist updated QCM data to disk
        self.hass.async_create_task(self._async_save_qcm_data())

    def set_qcm_answer(self, question: str, option: str) -> None:
        """Store the selected QCM answer for the next login attempt."""
        LOGGER.debug(
            "Setting QCM answer for question '%s' to option '%s'", question, option
        )
        if self.data is None:
            return

        if question not in self.data.get("qcm_questions", {}):
            return

        self.data.setdefault("qcm_selected_options", {})[question] = option
        # Persist QCM data to disk
        self.hass.async_create_task(self._async_save_qcm_data())

    async def _async_save_qcm_data(self) -> None:
        """Save QCM data to disk for persistence."""
        if self.data is None:
            return

        qcm_data = {
            "qcm_questions": self.data.get("qcm_questions", {}),
            "qcm_selected_options": self.data.get("qcm_selected_options", {}),
        }
        await self._qcm_store.async_save(qcm_data)
        LOGGER.debug("Saved QCM data to store: %s", qcm_data)

    async def async_migrate_legacy_qcm_file(self) -> None:
        """Check if legacy QCM file exists, read it, convert it to current usage and delete it."""
        filename = self.config_entry.data.get("qcm_filename", FILENAME_QCM)
        candidate_paths = [self.hass.config.path(filename)]
        if filename != FILENAME_QCM:
            candidate_paths.append(self.hass.config.path(FILENAME_QCM))

        for file_path_str in candidate_paths:
            file_path = anyio.Path(file_path_str)
            try:
                if not await file_path.is_file():
                    continue

                LOGGER.debug("Found legacy QCM file at %s, migrating", file_path_str)
                content = await file_path.read_text(encoding="utf-8")
                legacy_data: Any = json.loads(content)

                if isinstance(legacy_data, dict):
                    if self.data is None:
                        self.data = {
                            "qcm_questions": {},
                            "qcm_selected_options": {},
                        }

                    migrated = False
                    for question, propositions in legacy_data.items():
                        if not isinstance(question, str):
                            continue
                        if isinstance(propositions, list):
                            options = [str(opt) for opt in propositions]
                        elif isinstance(propositions, str):
                            options = [propositions]
                        else:
                            continue

                        if not options:
                            continue

                        if question not in self.data["qcm_questions"]:
                            self.data["qcm_questions"][question] = options
                            migrated = True
                        else:
                            for opt in options:
                                if opt not in self.data["qcm_questions"][question]:
                                    self.data["qcm_questions"][question].append(opt)
                                    migrated = True

                        if question not in self.data["qcm_selected_options"]:
                            self.data["qcm_selected_options"][question] = options[0]
                            migrated = True

                    if migrated:
                        await self._async_save_qcm_data()
                        LOGGER.debug(
                            "Migrated QCM data from %s into coordinator data",
                            file_path_str,
                        )

                        # Sync migrated data to any other ecole_directe config entries without QCM data
                        for entry in self.hass.config_entries.async_entries(DOMAIN):
                            if entry.entry_id != self.config_entry.entry_id:
                                other_store = Store(
                                    self.hass, 1, f"ecole_directe_qcm_{entry.entry_id}"
                                )
                                other_data = await other_store.async_load()
                                if not other_data:
                                    await other_store.async_save(
                                        {
                                            "qcm_questions": dict(
                                                self.data["qcm_questions"]
                                            ),
                                            "qcm_selected_options": dict(
                                                self.data["qcm_selected_options"]
                                            ),
                                        }
                                    )

                await file_path.unlink(missing_ok=True)
                LOGGER.info(
                    "Legacy QCM file '%s' migrated and deleted successfully",
                    file_path_str,
                )
            except Exception as err:
                LOGGER.warning(
                    "Error while migrating legacy QCM file '%s': %s", file_path_str, err
                )

    async def _async_update_data(self) -> Any:
        """
        Fetch data from API endpoint.

        This is the only method that should be implemented in a DataUpdateCoordinator.
        It is called automatically based on the update_interval.

        Context-based fetching:
        The coordinator tracks which entities are currently listening via async_contexts().
        This allows optimizing API calls to only fetch data that's actually needed.
        For example, if only sensor entities are enabled, we can skip fetching switch data.

        The API client uses the credentials from config_entry to authenticate:
        - username: from config_entry.data["username"]
        - password: from config_entry.data["password"]

        Expected API response structure (example):
        {
            "userId": 1,      # Used as device identifier
            "id": 1,          # Data record ID
            "title": "...",   # Additional metadata
            "body": "...",    # Additional content
            # In production, would include:
            # "air_quality": {"aqi": 45, "pm25": 12.3},
            # "filter": {"life_remaining": 75, "runtime_hours": 324},
            # "settings": {"fan_speed": "medium", "humidity": 55}
        }

        Returns:
            The data from the API as a dictionary.

        Raises:
            ConfigEntryAuthFailed: If authentication fails, triggers reauthentication.
            UpdateFailed: If data fetching fails for other reasons, optionally with retry_after.

        """
        try:
            if FAKE_ON:
                LOGGER.info("DEBUG MODE ON")

            previous_data = None if self.data is None else self.data.copy()

            async with EDApiClient(
                self.config_entry.data["username"],
                self.config_entry.data["password"],
                self.hass,
            ) as client:
                if self.data is not None:
                    for question, selected_option in self.data.get(
                        "qcm_selected_options", {}
                    ).items():
                        if selected_option is None:
                            continue
                        client.qcm_json[question] = [selected_option]

                try:
                    await client.login()
                except QCMException:
                    LOGGER.warning("QCM verification pending for ecole directe client")
                    return self.data
                except Exception:
                    LOGGER.critical("Unknown error on login")
                    return self.data

                # Preserve QCM data across updates so saved questions persist
                previous_qcm_questions = (self.data or {}).get("qcm_questions", {})
                previous_qcm_selected_options = (self.data or {}).get(
                    "qcm_selected_options", {}
                )

                self.data = {
                    "session": client,
                    "qcm_questions": previous_qcm_questions,
                    "qcm_selected_options": previous_qcm_selected_options,
                }

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

                if client.account_type == "P":  # professor ???
                    try:
                        for classe in client.data["accounts"][0]["profile"]["classes"]:
                            await client.get_classe(
                                classe["id"],
                            )
                    except Exception:
                        LOGGER.exception("Error getting classes")

                if client.account_type == "1":  # famille
                    if "MESSAGERIE" in client.modules:
                        try:
                            self.data["messagerie"] = await client.get_messages(
                                client.id,
                                None,
                                year_data,
                            )

                        except Exception:
                            LOGGER.exception(
                                "Error getting messages for family from ecole directe"
                            )

                    if FAKE_ON or "EDFORMS" in client.modules:
                        try:
                            self.data["formulaires"] = await client.get_formulaires(
                                client.account_type,
                                client.id,
                            )
                            self.compare_data(
                                previous_data,
                                "formulaires",
                                ["created", "titre"],
                                "new_formulaire",
                                None,
                            )
                        except Exception:
                            LOGGER.exception(
                                "Error getting formulaires from ecole directe"
                            )

                # START: MODIFIED FOR WALLET BALANCE (SINGLE CALL)
                all_balances = None
                try:
                    all_balances = await client.get_all_wallet_balances()
                    if all_balances and f"{client.id}" in all_balances:
                        self.data["wallets"] = all_balances[f"{client.id}"]
                except Exception:
                    LOGGER.exception(
                        "Error getting all wallet balances from ecole directe"
                    )
                # END: MODIFIED FOR WALLET BALANCE (SINGLE CALL)

                for eleve in client.eleves:
                    # Switch account context if this child belongs to a different account
                    if eleve.account_id_login is not None:
                        try:
                            await client.switch_account(eleve.account_id_login)
                        except Exception:
                            LOGGER.exception(
                                "Error switching account for %s",
                                eleve.get_fullname(),
                            )
                            continue

                    # START: DISTRIBUTE WALLET BALANCE DATA
                    if all_balances and eleve.eleve_id in all_balances:
                        wallets_key = f"{eleve.get_fullname_lower()}_wallets"
                        self.data[wallets_key] = all_balances[eleve.eleve_id]
                    # END: DISTRIBUTE WALLET BALANCE DATA

                    if FAKE_ON or "CAHIER_DE_TEXTES" in eleve.modules:
                        try:
                            homeworks = await client.get_homeworks(
                                eleve,
                                self.config_entry.options.get("decode_html", False),
                            )

                            self.data[f"{eleve.get_fullname_lower()}_homeworks"] = (
                                homeworks
                            )

                            self.compare_data(
                                previous_data,
                                f"{eleve.get_fullname_lower()}_homeworks",
                                ["date", "matiere", "short_description"],
                                "new_devoir",
                                eleve,
                            )

                            self.data[
                                f"{eleve.get_fullname_lower()}_homeworks_today"
                            ] = list(
                                filter(
                                    lambda homework: (
                                        homework["date"]
                                        .astimezone(self.timezone)
                                        .date()
                                        == today
                                    ),
                                    homeworks,
                                )
                            )
                            homeworks_tomorrow = list(
                                filter(
                                    lambda homework: (
                                        homework["date"]
                                        .astimezone(self.timezone)
                                        .date()
                                        == tomorrow
                                    ),
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

                            self.data[f"{eleve.get_fullname_lower()}_homeworks_1"] = (
                                list(
                                    filter(
                                        lambda homework: (
                                            homework["date"]
                                            .astimezone(self.timezone)
                                            .date()
                                            >= current_week_begin
                                            and homework["date"]
                                            .astimezone(self.timezone)
                                            .date()
                                            <= current_week_end
                                        ),
                                        homeworks,
                                    )
                                )
                            )
                            self.data[f"{eleve.get_fullname_lower()}_homeworks_2"] = (
                                list(
                                    filter(
                                        lambda homework: (
                                            homework["date"]
                                            .astimezone(self.timezone)
                                            .date()
                                            >= next_week_begin
                                            and homework["date"]
                                            .astimezone(self.timezone)
                                            .date()
                                            <= next_week_end
                                        ),
                                        homeworks,
                                    )
                                )
                            )
                            self.data[f"{eleve.get_fullname_lower()}_homeworks_3"] = (
                                list(
                                    filter(
                                        lambda homework: (
                                            homework["date"]
                                            .astimezone(self.timezone)
                                            .date()
                                            >= after_next_week_begin
                                        ),
                                        homeworks,
                                    )
                                )
                            )

                        except Exception:
                            LOGGER.exception(
                                "Error getting homeworks from ecole directe"
                            )
                    if FAKE_ON or "NOTES" in eleve.modules:
                        try:
                            grades_evaluations = await client.get_grades_evaluations(
                                eleve,
                                year_data,
                                self.config_entry.options.get(
                                    "notes_affichees", GRADES_TO_DISPLAY
                                ),
                            )
                            if "disciplines" in grades_evaluations:
                                disciplines = grades_evaluations["disciplines"]
                                self.data[
                                    f"{eleve.get_fullname_lower()}_disciplines"
                                ] = disciplines
                                for discipline in disciplines:
                                    self.data[
                                        f"{eleve.get_fullname_lower()}_{get_unique_id(discipline['nom'])}"
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
                                "new_note",
                                eleve,
                            )

                            self.data[f"{eleve.get_fullname_lower()}_evaluations"] = (
                                grades_evaluations["evaluations"]
                            )
                            self.compare_data(
                                previous_data,
                                f"{eleve.get_fullname_lower()}_evaluations",
                                ["date", "matiere", "devoir"],
                                "new_evaluation",
                                eleve,
                            )
                        except Exception:
                            LOGGER.exception("Error getting grades from ecole directe")

                    if FAKE_ON or "EDT" in eleve.modules:
                        try:
                            break_time = self.config_entry.options.get(
                                "lunch_break_time", DEFAULT_LUNCH_BREAK_TIME
                            )
                            lunch_break_time = datetime.strptime(
                                break_time,
                                "%H:%M",
                            ).time()

                            lessons = await client.get_lessons(
                                eleve,
                                today.strftime("%Y-%m-%d"),
                                current_week_plus_21.strftime("%Y-%m-%d"),
                                lunch_break_time,
                            )
                            self.data[
                                f"{eleve.get_fullname_lower()}_timetable_today"
                            ] = list(
                                filter(
                                    lambda lesson: (
                                        lesson["start"].astimezone(self.timezone).date()
                                        == today
                                    ),
                                    lessons,
                                )
                            )
                            lessons_tomorrow = list(
                                filter(
                                    lambda lesson: (
                                        lesson["start"].astimezone(self.timezone).date()
                                        == tomorrow
                                    ),
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
                            self.data[f"{eleve.get_fullname_lower()}_timetable_1"] = (
                                list(
                                    filter(
                                        lambda lesson: (
                                            lesson["start"]
                                            .astimezone(self.timezone)
                                            .date()
                                            >= today
                                            and lesson["start"]
                                            .astimezone(self.timezone)
                                            .date()
                                            <= current_week_end
                                        ),
                                        lessons,
                                    )
                                )
                            )
                            self.data[f"{eleve.get_fullname_lower()}_timetable_2"] = (
                                list(
                                    filter(
                                        lambda lesson: (
                                            lesson["start"]
                                            .astimezone(self.timezone)
                                            .date()
                                            >= next_week_begin
                                            and lesson["start"]
                                            .astimezone(self.timezone)
                                            .date()
                                            <= next_week_end
                                        ),
                                        lessons,
                                    )
                                )
                            )
                            self.data[f"{eleve.get_fullname_lower()}_timetable_3"] = (
                                list(
                                    filter(
                                        lambda lesson: (
                                            lesson["start"]
                                            .astimezone(self.timezone)
                                            .date()
                                            >= after_next_week_begin
                                        ),
                                        lessons,
                                    )
                                )
                            )

                        except Exception:
                            LOGGER.exception("Error getting Lessons from ecole directe")

                    if FAKE_ON or "VIE_SCOLAIRE" in eleve.modules:
                        try:
                            vie_scolaire = await client.get_vie_scolaire(eleve)
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
                        except Exception:
                            LOGGER.exception(
                                "Error getting vie scolaire from ecole directe"
                            )
                    if FAKE_ON or "MESSAGERIE" in eleve.modules:
                        try:
                            self.data[
                                f"{eleve.get_fullname_lower()}_messagerie"
                            ] = await client.get_messages(
                                client.id,
                                eleve,
                                year_data,
                            )
                        except Exception:
                            LOGGER.exception(
                                "Error getting messages from ecole directe"
                            )
        except EDApiClientAuthenticationError as exception:
            LOGGER.warning("Authentication error - %s", exception)
            raise ConfigEntryAuthFailed(
                translation_domain="ecole_directe",
                translation_key="authentication_failed",
            ) from exception
        except EDApiClientError as exception:
            LOGGER.exception("Error communicating with API")
            raise UpdateFailed(
                translation_domain="ecole_directe",
                translation_key="update_failed",
            ) from exception

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
        except Exception:
            LOGGER.exception(
                "Error comparing data: self[%s] previous_data[%s] data_key[%s]",
                self,
                previous_data,
                data_key,
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
