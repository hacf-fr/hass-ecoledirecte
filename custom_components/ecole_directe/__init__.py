"""
Ecole Directe integration.

For more details about this integration, please refer to
https://github.com/hacf-fr/hass-ecoledirecte

For integration development guidelines:
https://developers.home-assistant.io/docs/creating_integration_manifest
"""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import (
    EVENT_HOMEASSISTANT_STARTED,
    CoreState,
    HomeAssistant,
)
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.loader import async_get_loaded_integration

from .api import EDApiClient
from .const import (
    DEFAULT_REFRESH_INTERVAL,
    DOMAIN,
    INTEGRATION_VERSION,
    LOGGER,
    PLATFORMS,
)
from .coordinator import EDDataUpdateCoordinator
from .data import EDConfigEntry, EDData
from .frontend import JSModuleRegistration
from .service_actions import async_setup_services

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.util.event_type import EventType

# This integration is configured via config entries only
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_register_frontend(hass: HomeAssistant) -> None:
    """Enregistrer les modules frontend après le démarrage de HA."""
    module_register = JSModuleRegistration(hass)
    await module_register.async_register()


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/version",
    }
)
@websocket_api.async_response
async def websocket_get_version(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict,
) -> None:
    """Gérer la demande de version du frontend."""
    connection.send_result(
        msg["id"],
        {"version": INTEGRATION_VERSION},
    )


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """
    Set up the integration.

    This is called once at Home Assistant startup to register service actions.
    Service actions must be registered here (not in async_setup_entry) to ensure:
    - Service action validation works correctly
    - Service actions are available even without config entries
    - Helpful error messages are provided

    This is a Silver Quality Scale requirement.

    Args:
        hass: The Home Assistant instance.
        config: The Home Assistant configuration.

    Returns:
        True if setup was successful.

    For more information:
    https://developers.home-assistant.io/docs/dev_101_services

    """
    LOGGER.debug("async_setup")

    # Enregistrer la commande websocket pour la vérification de version
    websocket_api.async_register_command(hass, websocket_get_version)

    async def _setup_frontend(_event: EventType = None) -> None:
        await async_register_frontend(hass)

    # Si HA est déjà en cours d'exécution, enregistrer immédiatement
    if hass.state == CoreState.running:
        await _setup_frontend()
    else:
        # Sinon, attendre l'événement STARTED
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STARTED, _setup_frontend)

    await async_setup_services(hass)
    return True


async def async_setup_entry(
    hass: HomeAssistant,
    entry: EDConfigEntry,
) -> bool:
    """
    Set up this integration using UI.

    This is called when a config entry is loaded. It:
    1. Creates the API client with credentials from the config entry
    2. Initializes the DataUpdateCoordinator for data fetching
    3. Performs the first data refresh
    4. Sets up all platforms (sensors, switches, etc.)
    5. Registers services
    6. Sets up reload listener for config changes

    Data flow in this integration:
    1. User enters username/password in config flow (config_flow.py)
    2. Credentials stored in entry.data[CONF_USERNAME/CONF_PASSWORD]
    3. API Client initialized with credentials (api/client.py)
    4. Coordinator fetches data using authenticated client (coordinator/base.py)
    5. Entities access data via self.coordinator.data (sensor/, binary_sensor/, etc.)

    This pattern ensures credentials from setup flow are used throughout
    the integration's lifecycle for API communication.

    Args:
        hass: The Home Assistant instance.
        entry: The config entry being set up.

    Returns:
        True if setup was successful.

    For more information:
    https://developers.home-assistant.io/docs/config_entries_index/#setting-up-an-entry

    """
    LOGGER.debug("async_setup_entry")
    hass.data.setdefault(DOMAIN, {})
    # Initialize client first
    client = EDApiClient(
        user=entry.data[CONF_USERNAME],  # From config flow setup
        pwd=entry.data[CONF_PASSWORD],  # From config flow setup
        qcm_path=hass.config.config_dir
        + "/"
        + entry.data["qcm_filename"],  # From config flow setup
        hass=hass,
    )

    # Initialize coordinator with config_entry
    coordinator = EDDataUpdateCoordinator(
        hass=hass,
        logger=LOGGER,
        name=DOMAIN,
        entry=entry,
        update_interval=timedelta(
            minutes=entry.options.get("refresh_interval", DEFAULT_REFRESH_INTERVAL)
        ),
    )

    # Store runtime data
    entry.runtime_data = EDData(
        client=client,
        integration=async_get_loaded_integration(hass, entry.domain),
        coordinator=coordinator,
    )

    # https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
    await coordinator.async_config_entry_first_refresh()

    if not coordinator.last_update_success:
        raise ConfigEntryNotReady

    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: EDConfigEntry,
) -> bool:
    """
    Unload a config entry.

    This is called when the integration is being removed or reloaded.
    It ensures proper cleanup of:
    - All platform entities
    - Registered services
    - Update listeners

    Args:
        hass: The Home Assistant instance.
        entry: The config entry being unloaded.

    Returns:
        True if unload was successful.

    For more information:
    https://developers.home-assistant.io/docs/config_entries_index/#unloading-entries

    """
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_reload_entry(
    hass: HomeAssistant,
    entry: EDConfigEntry,
) -> None:
    """
    Reload config entry.

    This is called when the integration configuration or options have changed.
    It unloads and then reloads the integration with the new configuration.

    Args:
        hass: The Home Assistant instance.
        entry: The config entry being reloaded.

    For more information:
    https://developers.home-assistant.io/docs/config_entries_index/#reloading-entries

    """
    hass.data[DOMAIN][entry.entry_id]["coordinator"].update_interval = timedelta(
        minutes=entry.options.get("refresh_interval", DEFAULT_REFRESH_INTERVAL)
    )
    await hass.config_entries.async_reload(entry.entry_id)
