"""
Ecole Directe integration.

For more details about this integration, please refer to
https://github.com/hacf-fr/hass-ecoledirecte
"""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import TYPE_CHECKING

from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    SupportsResponse,
    callback,
)
from homeassistant.exceptions import ConfigEntryNotReady

from custom_components.ecole_directe.ecole_directe_helper import EDSession

from .const import DEFAULT_REFRESH_INTERVAL, DOMAIN, PLATFORMS
from .coordinator import EDDataUpdateCoordinator

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant) -> bool:
    """Set up is called when Home Assistant is loading our component."""
    LOGGER.debug("async_setup")

    @callback
    async def handle_devoir_effectue(call: ServiceCall) -> None:
        """Handle the service action call."""
        try:
            eleve_id = call.data["eleve_id"]
            devoir_id = call.data["devoir_id"]
            effectue = call.data.get("effectue", True)
            LOGGER.debug(
                "Service devoir_effectue called with eleve_id=%s, devoir_id=%s, effectue=%s",
                eleve_id,
                devoir_id,
                effectue,
            )
            qcm = hass.config_entries.async_entries(DOMAIN)[0].data["qcm_filename"]
            username = hass.config_entries.async_entries(DOMAIN)[0].data["username"]
            password = hass.config_entries.async_entries(DOMAIN)[0].data["password"]
            async with EDSession(
                username,
                password,
                hass.config.config_dir + "/" + qcm,
                hass,
            ) as session:
                await session.post_homework(
                    eleve_id=eleve_id, devoir_id=devoir_id, effectue=effectue
                )
        except Exception:
            LOGGER.exception("Error on service devoir_effectue call")
            return

    hass.services.async_register(
        DOMAIN,
        "devoir_effectue",
        handle_devoir_effectue,
        None,
        SupportsResponse.NONE,
    )

    # Return boolean to indicate that initialization was successful.
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Ecole Directe from a config entry."""
    LOGGER.debug("async_setup_entry")
    hass.data.setdefault(DOMAIN, {})

    coordinator = EDDataUpdateCoordinator(hass, entry)

    await coordinator.async_config_entry_first_refresh()

    if not coordinator.last_update_success:
        raise ConfigEntryNotReady

    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
    }

    entry.async_on_unload(entry.add_update_listener(update_listener))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    hass.data[DOMAIN][entry.entry_id]["coordinator"].update_interval = timedelta(
        minutes=entry.options.get("refresh_interval", DEFAULT_REFRESH_INTERVAL)
    )
