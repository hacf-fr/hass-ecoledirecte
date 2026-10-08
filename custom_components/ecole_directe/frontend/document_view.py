"""HTTP view serving homework documents to the frontend."""

from __future__ import annotations

import mimetypes
from http import HTTPStatus
from typing import TYPE_CHECKING
from urllib.parse import quote

from aiohttp import web
from ecoledirecte_api.client import QCMException
from homeassistant.components.http import HomeAssistantView

from ..const import DOMAIN, LOGGER

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from ..coordinator import EDDataUpdateCoordinator


class EDDocumentView(HomeAssistantView):
    """
    Serve a homework document downloaded from Ecole Directe.

    The first request for a given document downloads it from Ecole Directe
    and caches it locally (see EDDataUpdateCoordinator.async_get_document_path);
    every request after that, including the several byte-range requests
    Safari/AVFoundation make just to start playing audio or video, is served
    straight from that local file via aiohttp's FileResponse, which handles
    Range/Accept-Ranges/conditional-GET on its own.
    """

    url = f"/api/{DOMAIN}/document/{{document_id}}"
    name = f"api:{DOMAIN}:document"
    requires_auth = True

    async def get(self, request: web.Request, document_id: str) -> web.StreamResponse:
        """Serve the document, as attachment when ?download=1."""
        hass: HomeAssistant = request.app["hass"]

        found = None
        coordinator: EDDataUpdateCoordinator | None = None
        for entry in hass.config_entries.async_entries(DOMAIN):
            runtime_data = getattr(entry, "runtime_data", None)
            if not runtime_data:
                continue
            coordinator = runtime_data.coordinator
            found = coordinator.find_homework_document(document_id)
            if found is not None:
                break
        if found is None or coordinator is None:
            return web.Response(status=HTTPStatus.NOT_FOUND)

        eleve_key, document = found
        filename = str(document.get("libelle") or f"document_{document_id}")
        content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
        disposition = "attachment" if request.query.get("download") == "1" else "inline"

        try:
            cache_path = await coordinator.async_get_document_path(eleve_key, document)
        except QCMException:
            LOGGER.warning("QCM verification pending, cannot download document")
            return web.Response(status=HTTPStatus.SERVICE_UNAVAILABLE)
        except Exception:
            LOGGER.exception("Error downloading document %s", document_id)
            return web.Response(status=HTTPStatus.BAD_GATEWAY)

        return web.FileResponse(
            cache_path,
            headers={
                "Content-Type": content_type,
                "Content-Disposition": (
                    f"{disposition}; filename*=UTF-8''{quote(filename)}"
                ),
                "Cache-Control": "private, no-store",
            },
        )
