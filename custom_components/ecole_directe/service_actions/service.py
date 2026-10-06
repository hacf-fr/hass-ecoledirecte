"""Example service action handlers for ecole_directe."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.exceptions import HomeAssistantError

from custom_components.ecole_directe.const import LOGGER

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
        # entry.runtime_data.client is only constructed, never logged in: the
        # coordinator logs in a fresh client on every refresh and keeps the
        # authenticated one in its data instead (see coordinator/base.py).
        session_data = entry.runtime_data.coordinator.data or {}
        client = session_data.get("session")
        if client is None:
            msg = "Ecole Directe client not yet authenticated"
            raise HomeAssistantError(msg)
        await client.post_homework(
            eleve_id=eleve_id, devoir_id=devoir_id, effectue=effectue
        )
        # Update entities now instead of waiting for the next scheduled poll.
        await entry.runtime_data.coordinator.async_request_refresh()
    except Exception as err:
        LOGGER.exception("Error on service devoir_effectue call")
        msg = f"Failed to mark homework as done: {err}"
        raise HomeAssistantError(msg) from err
