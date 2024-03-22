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

from .ecole_directe_helper import (
    get_ecoledirecte_session,
    get_homeworks,
    get_grades,
    get_homeworks_by_date,
)

from .const import (
    DEFAULT_REFRESH_INTERVAL,
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

        data = self.config_entry.data

        session = await self.hass.async_add_executor_job(get_ecoledirecte_session, data)

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

        # if session._account_type == "1":  # famille
        #     if "MESSAGERIE" in session.modules:
        #         try:
        #             self.data["messages"] = await self.hass.async_add_executor_job(
        #                 get_messages, session, None, year_data
        #             )
        #         except Exception as ex:
        #             self.data["messages"] = None
        #             _LOGGER.warning(
        #                 "Error getting messages for family from ecole directe: %s", ex
        #             )

        for eleve in session.eleves:
            if "CAHIER_DE_TEXTES" in eleve.modules:
                try:
                    homeworks_json = await self.hass.async_add_executor_job(
                        get_homeworks, session, eleve
                    )
                    for key in homeworks_json.keys():
                        homeworks_by_date_json = await self.hass.async_add_executor_job(
                            get_homeworks_by_date, session, eleve, key
                        )
                        _LOGGER.debug(
                            "homeworks_by_date_json:%s", homeworks_by_date_json
                        )
                        for matiere in homeworks_by_date_json["matieres"]:
                            for homework in homeworks_json[key]:
                                if matiere["id"] == homework["idDevoir"]:
                                    homework["nbJourMaxRenduDevoir"] = matiere[
                                        "nbJourMaxRenduDevoir"
                                    ]
                                    homework["contenu"] = matiere["aFaire"]["contenu"]

                        _LOGGER.debug("homeworks_json:%s", homeworks_json)
                    self.data[f"homeworks{eleve.get_fullname_lower()}"] = homeworks_json
                except Exception as ex:
                    _LOGGER.warning(
                        "Error getting homeworks from ecole directe: %s", ex
                    )
                    self.data[f"homeworks{eleve.get_fullname_lower()}"] = {}
            if "NOTES" in eleve.modules:
                try:
                    self.data[
                        f"grades{eleve.get_fullname_lower()}"
                    ] = await self.hass.async_add_executor_job(
                        get_grades, session, eleve, year_data
                    )
                except Exception as ex:
                    _LOGGER.warning("Error getting grades from ecole directe: %s", ex)
                    self.data[f"grades{eleve.get_fullname_lower()}"] = {}
            # if "MESSAGERIE" in eleve.modules:
            #     try:
            #         self.data[
            #             "messages" + eleve.eleve_id
            #         ] = await self.hass.async_add_executor_job(
            #             get_messages, session, eleve, year_data
            #         )
            #     except Exception as ex:
            #         _LOGGER.warning("Error getting messages from ecole directe: %s", ex)

        return self.data
