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
        # The client kept in coordinator.data["session"] is closed at the end of
        # each refresh: log in a fresh one (see async_logged_in_client).
        coordinator = entry.runtime_data.coordinator
        async with coordinator.async_logged_in_client() as client:
            eleve = next(
                (e for e in client.eleves if e.eleve_id == str(eleve_id)), None
            )
            if eleve is not None and eleve.account_id_login is not None:
                await client.switch_account(eleve.account_id_login)
            done = await client.post_homework(
                eleve_id=eleve_id, devoir_id=devoir_id, effectue=effectue
            )
        if not done:
            msg = "Ecole Directe refused the update"
            raise HomeAssistantError(msg)
        # Update entities now instead of waiting for the next scheduled poll.
        await coordinator.async_request_refresh()
    except Exception as err:
        LOGGER.exception("Error on service devoir_effectue call")
        msg = f"Failed to mark homework as done: {err}"
        raise HomeAssistantError(msg) from err
