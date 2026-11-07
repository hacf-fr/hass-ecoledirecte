# Copyright (c) 2024-2026
# SPDX-License-Identifier: MIT

"""HTTP view serving homework documents to the frontend."""

from __future__ import annotations

import mimetypes
from http import HTTPStatus
from typing import TYPE_CHECKING, Any
from urllib.parse import quote

from aiohttp import web
from ecoledirecte_api.client import QCMException
from homeassistant.helpers.http import HomeAssistantView

from ..const import DOMAIN, LOGGER

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from ..coordinator import EDDataUpdateCoordinator


class EDDocumentView(HomeAssistantView):
    """
    Serve a document downloaded from Ecole Directe.

    The first request for a document downloads it from Ecole Directe and
    caches it locally. Subsequent requests, including the several byte-range
    requests Safari/AVFoundation make just to start playing audio or video,
    are served from the cached file via aiohttp's FileResponse, which handles
    Range/Accept-Ranges/conditional-GET on its own.
    """

    url = f"/api/{DOMAIN}/document/{{document_id}}"
    extra_urls = [f"/api/{DOMAIN}/document/{{workspace_id}}/{{document_id}}"]
    name = f"api:{DOMAIN}:document"
    requires_auth = True

    async def get(
        self,
        request: web.Request,
        document_id: str,
        workspace_id: str | None = None,
    ) -> web.StreamResponse:
        """Serve the document, as attachment when ?download=1."""
        hass: HomeAssistant = request.app["hass"]

        coordinator: EDDataUpdateCoordinator | None = None
        document: dict[str, Any] | None = None
        eleve_key: str | None = None
        for entry in hass.config_entries.async_entries(DOMAIN):
            runtime_data = getattr(entry, "runtime_data", None)
            if not runtime_data:
                continue
            candidate_coordinator = runtime_data.coordinator
            if workspace_id is None:
                found = candidate_coordinator.find_homework_document(document_id)
                if found is not None:
                    eleve_key, document = found
            else:
                document = candidate_coordinator.find_workspace_document(
                    workspace_id, document_id
                )
            if document is not None:
                coordinator = candidate_coordinator
                break
        if document is None or coordinator is None:
            return web.Response(status=HTTPStatus.NOT_FOUND)

        if workspace_id is not None:
            filename = str(document.get("unc") or f"document_{document_id}").rsplit(
                "/", maxsplit=1
            )[-1]
        else:
            filename = str(document.get("libelle") or f"document_{document_id}")
        content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
        disposition = (
            "attachment"
            if workspace_id is not None or request.query.get("download") == "1"
            else "inline"
        )

        try:
            if workspace_id is not None:
                cache_path = await coordinator.async_get_workspace_document_path(
                    workspace_id, document
                )
            else:
                if eleve_key is None:
                    return web.Response(status=HTTPStatus.NOT_FOUND)
                cache_path = await coordinator.async_get_document_path(
                    eleve_key, document
                )
        except QCMException:
            LOGGER.warning("QCM verification pending, cannot download %s", document_id)
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
