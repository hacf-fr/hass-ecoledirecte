"""Data update coordinator for the Ecole Directe integration."""
from __future__ import annotations

from datetime import timedelta
from typing import Any

import logging
from .ecoleDirecte_helper import *

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import TimestampDataUpdateCoordinator

from .const import (
    DEFAULT_REFRESH_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

class EDDataUpdateCoordinator(TimestampDataUpdateCoordinator):
    """Data update coordinator for the Ecole Directe integration."""

    config_entry: ConfigEntry

    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass=hass,
            logger=_LOGGER,
            name=entry.title,
            update_interval=timedelta(minutes=entry.options.get("refresh_interval", DEFAULT_REFRESH_INTERVAL)),
        )
        self.config_entry = entry

    async def _async_update_data(self) -> dict[Platform, dict[str, Any]]:
        """Get the latest data from Ecole Directe and updates the state."""

        data = self.config_entry.data

        session = await self.hass.async_add_executor_job(get_ecoledirecte_session, data)

        if session is None:
            _LOGGER.error('Unable to init ecole directe client')
            return None

        self.data['session'] = session

        try:
            self.data['messages'] = await self.hass.async_add_executor_job(getMessages, session, None)
        except Exception as ex:
            self.data['messages'] = None
            _LOGGER.warning("Error getting messages from ecole directe: %s", ex)

        for eleve in session.eleves:
            if "CAHIER_DE_TEXTES" in eleve.modules:
                try:
                    self.data['homework'+ eleve.eleve_id] = await self.hass.async_add_executor_job(getHomework, session, eleve)
                except Exception as ex:
                    _LOGGER.warning("Error getting homework from ecole directe: %s", ex)
            if "NOTES" in eleve.modules:
                try:
                    self.data['notes'+ eleve.eleve_id] = await self.hass.async_add_executor_job(getNotes, session, eleve)
                except Exception as ex:
                    _LOGGER.warning("Error getting notes from ecole directe: %s", ex)

        return self.data
