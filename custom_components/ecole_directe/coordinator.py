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

from .ecoleDirecte_helper import get_ecoledirecte_session, getDevoirs, getNotes

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

        currentYear = datetime.datetime.now().year
        if (currentYear % 2) == 0:
            yearData = f"{str(currentYear-1)}-{str(currentYear)}"
        else:
            yearData = f"{str(currentYear)}-{str(currentYear + 1)}"

        # if (session.typeCompte == '1'): # famille
        #     if "MESSAGERIE" in session.modules:
        #         try:
        #             self.data['messages'] = await self.hass.async_add_executor_job(getMessages, session, None, yearData)
        #         except Exception as ex:
        #             self.data['messages'] = None
        #             _LOGGER.warning("Error getting messages for family from ecole directe: %s", ex)

        for eleve in session.eleves:
            if "CAHIER_DE_TEXTES" in eleve.modules:
                try:
                    self.data[
                        "devoirs" + eleve.get_fullnameLower()
                    ] = await self.hass.async_add_executor_job(
                        getDevoirs, session, eleve
                    )
                except Exception as ex:
                    _LOGGER.warning("Error getting devoirs from ecole directe: %s", ex)
                    self.data["devoirs" + eleve.get_fullnameLower()] = {}
            if "NOTES" in eleve.modules:
                try:
                    self.data[
                        "notes" + eleve.get_fullnameLower()
                    ] = await self.hass.async_add_executor_job(
                        getNotes, session, eleve, yearData
                    )
                except Exception as ex:
                    _LOGGER.warning("Error getting notes from ecole directe: %s", ex)
                    self.data["notes" + eleve.get_fullnameLower()] = {}
            # if "MESSAGERIE" in eleve.modules:
            #     try:
            #         self.data['messages'+ eleve.eleve_id] = await self.hass.async_add_executor_job(getMessages, session, eleve, yearData)
            #     except Exception as ex:
            #         _LOGGER.warning("Error getting notes from ecole directe: %s", ex)

        return self.data
