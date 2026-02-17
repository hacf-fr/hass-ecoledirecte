"""Service actions package for ecole_directe."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.core import ServiceCall, SupportsResponse, callback

from custom_components.ecole_directe.const import (
    DOMAIN,
    LOGGER,
)
from custom_components.ecole_directe.service_actions.service import (
    async_handle_devoir_effectue,
)

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

# Service action names - only used within service_actions module
SERVICE_DEVOIR_EFFECTUE = "devoir_effectue"


async def async_setup_services(hass: HomeAssistant) -> None:
    """
    Register services for the integration.

    Services are registered at component level (in async_setup) rather than
    per config entry. This is a Silver Quality Scale requirement and ensures:
    - Service validation works correctly
    - Services are available even without config entries
    - Helpful error messages are provided

    Service handlers iterate over all config entries to find the relevant one.
    """

    @callback
    async def handle_devoir_effectue(call: ServiceCall) -> None:
        """Handle the service action call."""
        # Find all config entries for this domain
        entries = hass.config_entries.async_entries(DOMAIN)
        if not entries:
            LOGGER.warning("No config entries found for %s", DOMAIN)
        # Use first entry (or implement logic to select specific entry)
        entry = entries[0]
        await async_handle_devoir_effectue(hass, entry, call)

    # Register services (only once at component level)
    if not hass.services.has_service(DOMAIN, SERVICE_DEVOIR_EFFECTUE):
        hass.services.async_register(
            domain=DOMAIN,
            service=SERVICE_DEVOIR_EFFECTUE,
            service_func=handle_devoir_effectue,
            schema=None,
            supports_response=SupportsResponse.NONE,
        )

    LOGGER.debug("Services registered for %s", DOMAIN)
