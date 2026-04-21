"""Example service action handlers for ecole_directe."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.exceptions import HomeAssistantError

from custom_components.ecole_directe.const import DOMAIN, LOGGER

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant, ServiceCall

    from custom_components.ecole_directe.data import EDConfigEntry


async def async_handle_devoir_effectue(
    hass: HomeAssistant, entry: EDConfigEntry, call: ServiceCall
) -> None:
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
        client = entry.runtime_data.client
        await client.post_homework(
            eleve_id=eleve_id, devoir_id=devoir_id, effectue=effectue
        )
    except Exception as err:
        LOGGER.exception("Error on service devoir_effectue call")
        raise HomeAssistantError(
            f"Failed to mark homework as done: {err}"
        ) from err
